---
title: Ceph与Openstack整合
date: 2016-02-15 14:19:15
tags:
- ceph
- openstack
---
本文介绍如何使用Ceph作为Openstack的后端存储。Ceph作为后端存储能够提供诸如“秒级创建虚拟机、自动恢复等功能”。下面就介绍如何将Ceph与Openstack整合。使用的Ceph版本是`Jewel`版本，Openstack版本是`Newton`
<!-- more -->

### 准备工作

#### 创建pool
Ceph集群安装完成后，创建如下四个pool，pg_num根据自己集群大小来定，官网或谷歌有相关教程
```
ceph osd pool create volumes 64 64
ceph osd pool create images 64 64
ceph osd pool create backups 64 64
ceph osd pool create vms 64 64  
```


#### 拷贝文件
运行有`glance-api`、`cinder-volume`、`nova-compute`、`cinder-backup`的节点我们都将其看做为Ceph集群的客户端。将`ceph.conf`拷贝到客户端的`/etc/ceph/`目录下
```
scp /etc/ceph/ceph.conf root@{client-node}:/etc/ceph/ceph.conf
```


#### 安装软件
安装客户端软件包`python-rbd`、`ceph-common`
```
yum install python-rbd ceph-common
```


#### 客户端认证
使用了cephx认证时候，需要创建`cinder`和`glance`用户(这里使用`cinder`用户来操作nova)
```
ceph auth get-or-create client.glance mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=images'
ceph auth get-or-create client.cinder-backup mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=backups'
ceph auth get-or-create client.cinder mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=volumes, allow rwx pool=vms, allow rwx pool=images'
```

如果Openstack的版本是mitaka之前的版本，那么使用如下命令创建用户
```
ceph auth get-or-create client.glance mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=images'
ceph auth get-or-create client.cinder-backup mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=backups'
ceph auth get-or-create client.cinder mon 'allow r' osd 'allow class-read object_prefix rbd_children, allow rwx pool=volumes, allow rwx pool=vms, allow rx pool=images'
```

创建完成用户之后，将`client.glance`、`client.cinder`、`client.cinder-backup`的密钥环拷贝到ceph客户端节点，对应关系如下

```
ceph auth get-or-create client.glance | sudo tee /etc/ceph/ceph.client.glance.keyring
ceph auth get-or-create client.cinder | sudo tee /etc/ceph/ceph.client.cinder.keyring
ceph auth get-or-create client.cinder-backup | sudo tee /etc/ceph/ceph.client.cinder-backup.keyring


scp /etc/ceph/ceph.client.glance.keyring root@{client}:/etc/ceph/ceph.client.glance.keyring
scp /etc/ceph/ceph.client.cinder.keyring root@{client}:/etc/ceph/ceph.client.cinder.keyring
scp /etc/ceph/ceph.client.cinder-backup.keyring root@{client}:/etc/ceph/ceph.client.cinder-backup.keyring

```

**注意，在nova-compute节点上，ceph.client.cinder.keyring的用户组为root:root**

|服务         |密钥环        |所属用户     |
|-------------|--------------|-------------|
|cinder-volume|client.cinder |cinder:cinder|
|cinder-backup|client.cinder-backup |cinder:cinder|
|glance-api|client.glance |glance:glance|
|nova-compute|client.cinder|root:root|

同时，我们需要把`client.cinder`的密钥存储在`libvirt`中，因为libvirt在挂载磁盘的时候需要这个密钥。具体操作按照如下步骤
```
ceph auth get-key client.cinder | ssh {nova-compute-node} tee /etc/ceph/client.cinder.key
```

在**计算节点**上，把密钥添加进libvirt
```
cd /etc/ceph

uuidgen
457eb676-33da-42ec-9a8c-9293d545c337

cat > secret.xml <<EOF
<secret ephemeral='no' private='no'>
  <uuid>457eb676-33da-42ec-9a8c-9293d545c337</uuid>
  <usage type='ceph'>
    <name>client.cinder secret</name>
  </usage>
</secret>
EOF

sudo virsh secret-define --file secret.xml
Secret 457eb676-33da-42ec-9a8c-9293d545c337 created

sudo virsh secret-set-value --secret 457eb676-33da-42ec-9a8c-9293d545c337 --base64 $(cat client.cinder.key) && rm client.cinder.key secret.xml
```


### 配置Openstack

#### 配置glance服务
编辑`/etc/ceph/ceph.conf`
```
[client.glance]
keyring= /etc/ceph/client.glance.keyring
```


编辑`/etc/glance/glance-api.conf`的[glance_store]

```
[glance_store]
stores = glance.store.rbd.Store,glance.store.http.Store
default_store = rbd
rbd_store_pool = images
rbd_store_user = glance
rbd_store_ceph_conf = /etc/ceph/ceph.conf
rbd_store_chunk_size = 8
```

编辑`/etc/glance/glance-api.conf`的[DEFAULT]来使用`copy-on-write`这个特性

```
[DEFAULT]
...
show_multiple_locations = True #mitaka之前的版本没有这个设置
show_image_direct_url = True
```

编辑`/etc/glance/glance-api.conf`的[paste_deploy]来取消镜像本地缓存

```
[paste_deploy]
flavor = keystone
```

上传镜像时，设置镜像参数

`hw_scsi_model=virtio-scsi`：添加virtio-scsi控制器和获得更好的性能
`hw_disk_bus=scsi`：连接每个cinder块设备到控制器
`hw_qemu_guest_agent=yes`：启用qemu-guest-agent，以便宿主机与客户机之间通信
`os_require_quiesce=yes`：能够通过qemu-gutst-agent冻结或解冻客户机文件系统

设置完成后，重启glance-api服务

#### 配置cinder-volume服务
编辑`/etc/ceph/ceph.conf`
```
...
[client.cinder]
keyring = /etc/ceph/client.cinder.keyring
```


编辑`/etc/cinder/cinder.conf`文件
rbd_secret_uuid即是`secret.xml`的uuid

```
[DEFAULT]
...
# volume_group = cinder-volumes
enabled_backends = rbd

#以下是添加的配置
[rbd]
volume_backend_name = rbd-backend
volume_driver = cinder.volume.drivers.rbd.RBDDriver
rbd_pool = volumes
rbd_ceph_conf = /etc/ceph/ceph.conf
rbd_flatten_volume_from_snapshot = false
rbd_max_clone_depth = 5
rbd_store_chunk_size = 4
rados_connect_timeout = -1
glance_api_version = 2

rbd_user = cinder
rbd_secret_uuid = 457eb676-33da-42ec-9a8c-9293d545c337
```

重启cinder-volume服务

*请注意,如果您正在配置多个cinder后端,glance_api_version = 2必须在[DEFAULT]部分*

#### 配置cinder-backup服务
编辑`/etc/ceph/ceph.conf`
```
...
[client.cinder]
keyring = /etc/ceph/client.cinder-backup.keyring
```

OpenStack cinder-backup需要特定的守护进程，需要自行安装。

编辑`/etc/cinder/cinder.conf`

```
[DEFAULT]
...
backup_driver = cinder.backup.drivers.ceph
backup_ceph_conf = /etc/ceph/ceph.conf
backup_ceph_user = cinder-backup
backup_ceph_chunk_size = 134217728
backup_ceph_pool = backups
backup_ceph_stripe_unit = 0
backup_ceph_stripe_count = 0
restore_discard_excess_bytes = true
```

重启cinder-backup服务

#### 配置nova-compute服务
编辑`/etc/ceph/ceph.conf`文件
```
[client]
rbd cache = true
rbd cache size = 268435456
rbd cache max dirty = 134217728
rbd cache max dirty age = 5
rbd cache writethrough until flush = true
log file = /var/log/qemu/qemu-guest-$pid.log
rbd concurrent management ops = 20

[client.cinder]
keyring = /etc/ceph/client.cinder.keyring

[client.cinder-backup]
keyring = /etc/ceph/client.cinder-backup.keyring

[client.glance]
keyring = /etc/ceph/client.glance.keyring
```

配置这些路径的权限
```
mkdir -p /var/run/ceph/guests/ /var/log/qemu/
chown qemu:libvirtd /var/run/ceph/guests /var/log/qemu/
```

修改`/etc/nova/nova.conf`
```
[libvirt]
virt_type = kvm
inject_password = False
inject_key = False
inject_partition = -2
block_migration_flag = VIR_MIGRATE_UNDEFINE_SOURCE,VIR_MIGRATE_PEER2PEER,VIR_MIGRATE_LIVE,VIR_MIGRATE_NON_SHARED_INC
live_migration_flag = VIR_MIGRATE_UNDEFINE_SOURCE,VIR_MIGRATE_PEER2PEER,VIR_MIGRATE_LIVE,VIR_MIGRATE_PERSIST_DEST
disk_cachemodes = "network=writeback"
hw_disk_discard = unmap
cpu_mode = host-model
images_type = rbd
images_rbd_pool = vms
rbd_user = cinder
rbd_secret_uuid = 457eb676-33da-42ec-9a8c-9293d545c337
```

配置完成后重启nova-compute服务

