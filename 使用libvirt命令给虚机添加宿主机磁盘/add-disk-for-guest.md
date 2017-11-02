---
title: 使用libvirt命令给虚机添加宿主机磁盘
date: 2017-11-02 17:50:32
tags: 
- Libvirt
- KVM
---

记录一下使用libvirt的attach-device命令给客户机添加宿主机磁盘
<!--more-->

libvirt可以给客户机添加宿主机磁盘，具体操作如下。

####准备
首先使用fdisk等工具给宿主机磁盘分区，例如创建了新分区`/dev/sdf1`
编辑新设备的xml文件

```
<disk type='block' device='disk'>
        <driver name='qemu' type='raw' cache='none'/>
        <source dev='/dev/sdf1'/>
        <target dev='vdb' bus='virtio'/>
</disk>
```

`target`标签中的属性`dev`表示这块磁盘在客户机中的标签。

####操作
给客户机添加磁盘

```
virsh attach-device {domainName} disk-device.xml
```
*disk-device.xml*文件就是之前编辑的那个磁盘设备xml文件

这时就可以在客户机中通过了`lsblk -f`命令查看到磁盘了
*注意*，如果磁盘已经在宿主机中格式化了磁盘，会发现客户机中的磁盘也被格式化了，ID也一样

####持久化
以上命令添加完成后，如果虚机重启，那么磁盘就不再会自动挂载到客户机了

需要使用`virsh edit {domainName}`来修改客户机的xml文件。
之后重启了也同样能够挂载磁盘
