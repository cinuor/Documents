---
title: ceilometer使用独立的消息队列
date: 2016-10-20 20:14:33
tags:
- openstack
- ceilometer
---
Ceilometer是Openstack中的计量与监控组件。具体的Ceilometer架构可以参考这里[这里][1]。

当我们把Ceilometer部署到Openstack的rpc消息集群当中后，当采集频率较高的时候，就会对其他组件造成很大的影响。所以我们使用单独的消息队列来启动部署Ceilometer组件。
<!-- more -->

### 一. 节点信息
测试环境使用CentOS7，网络信息如下，Openstack的rpc消息队列我们直接安装在控制节点中。

 - 控制节点：10.133.157.228
 - 计算节点：10.133.157.229
 - 消息队列B：10.133.157.71

其中消息队列B里面我们创建新的用户`ceilometer`，密码也是`ceilometer`
 

### 二. 控制节点部署

安装mongodb
```
 yum install mongodb-server mongodb
```
 之后配置`/etc/mongod.conf`
```
 bind_ip = 10.133.157.228
 smallfiles = true
```
 
 启动mongodb
 ```
 systemctl enable mongod.service
 systemctl start mongod.service
 ```
 
 创建Ceilometer数据库
 ```
 mongo --host 10.133.146.228 --eval '
 db = db.getSiblingDB("ceilometer");
 db.createUser({user: "ceilometer",
 pwd: "CEILOMETER_DBPASS",
 roles: [ "readWrite", "dbAdmin" ]})'
 ```



安装控制节点组件
 创建Ceilometer用户
```
 openstack user create --domain default --password-prompt ceilometer
```
 
 为Ceilometer用户赋予`admin`角色
```
 openstack role add --project service --user ceilometer admin
```
 
 创建Ceilometer服务
```
 openstack service create --name ceilometer --description "Telemetry" metering
```
 
 创建endpoint
```
 openstack endpoint create --region RegionOne metering public http://10.133.157.228:8777
 
 openstack endpoint create --region RegionOne metering internal http://10.133.157.228:8777
 
 openstack endpoint create --region RegionOne metering admin http://10.133.157.228:8777
```
 
 安装组件
```
 yum install openstack-ceilometer-api openstack-ceilometer-collector openstack-ceilometer-notification openstack-ceilometer-central python-ceilometerclient
```
 
 修改配置文件`/etc/ceilometer/ceilometer.conf`
```
 [DEFAULT]
 ...
 rpc_backend = rabbit
 auth_strategy = keystone
 
 [database]
 ...
 connection = mongodb://ceilometer:CEILOMETER_DBPASS@10.133.157.228:27017/ceilometer
 
 [oslo_messaging_rabbit]
 ...
 rabbit_host = 10.133.157.71
 rabbit_userid = ceilometer
 rabbit_password = ceilometer

 [keystone_authtoken]
 ...
 auth_uri = http://10.133.157.228:5000
 auth_url = http://10.133.157.228:35357
 memcached_servers = 10.133.157.228:11211
 auth_type = password
 project_domain_name = default
 user_domain_name = default
 project_name = service
 username = ceilometer
 password = CEILOMETER_PASS//创建ceilometer用户时的密码

 [service_credentials]
 ...
 auth_type = password
 auth_url = http://10.133.157.228:5000/v3
 project_domain_name = default
 user_domain_name = default
 project_name = service
 username = ceilometer
 password = CEILOMETER_PASS
 interface = internalURL
 region_name = RegionOne
```
 
 创建HTTP服务文件`/etc/httpd/conf.d/wsgi-ceilometer.conf`
```xml
    Listen 8777
    
    <VirtualHost *:8777>
        WSGIDaemonProcess ceilometer-api processes=2 threads=10 user=ceilometer group=ceilometer display-name=%{GROUP}
        WSGIProcessGroup ceilometer-api
        WSGIScriptAlias / "/var/www/cgi-bin/ceilometer/app"
        WSGIApplicationGroup %{GLOBAL}
        ErrorLog /var/log/httpd/ceilometer_error.log
        CustomLog /var/log/httpd/ceilometer_access.log combined
    </VirtualHost>
    
    WSGISocketPrefix /var/run/httpd
```
 
 启动服务
```
 systemctl reload httpd.service
 
 systemctl enable openstack-ceilometer-notification.service openstack-ceilometer-central.service openstack-ceilometer-collector.service
 
 systemctl start openstack-ceilometer-notification.service openstack-ceilometer-central.service openstack-ceilometer-collector.service
```
 
### 三. 开启镜像服务计量
编辑`/etc/glance/glance-api.conf`和`/etc/glance/glance-registry.conf`文件
```
[DEFAULT]
...
rpc_backend = rabbit

[oslo_messaging_notifications]
...
driver = messagingv2
transport_url = rabbit://ceilometer:ceilometer@10.133.157.71:5672//
topics = notifications
```

重启glance服务
```
systemctl restart openstack-glance-api.service openstack-glance-registry.service
```

### 四. 开启计算服务计量
安装相关组件
```
yum install openstack-ceilometer-compute python-ceilometerclient python-pecan
```

编辑`/etc/ceilometer/ceilometer.conf`文件
```
[DEFAULT]
...
rpc_backend = rabbit
auth_strategy = keystone

[oslo_messaging_rabbit]
...
rabbit_host = 10.133.157.71
rabbit_userid = ceilometer
rabbit_password = ceilometer

[keystone_authtoken]
...
auth_uri = http://10.133.157.228:5000
auth_url = http://10.133.157.228:35357
memcached_servers = 10.133.157.228:11211
auth_type = password
project_domain_name = default
user_domain_name = default
project_name = service
username = ceilometer
password = CEILOMETER_PASS

[service_credentials]
...
auth_url = http://10.133.157.228:5000
project_domain_id = default
user_domain_id = default
auth_type = password
username = ceilometer
project_name = service
password = CEILOMETER_PASS
interface = internalURL
region_name = RegionOne
```

修改`/etc/nova/nova.conf`
```
[DEFAULT]
...
instance_usage_audit = True
instance_usage_audit_period = hour
notify_on_state_change = vm_and_task_state

[oslo_messaging_notifications]
...
driver = messagingv2
transport_url = rabbit://ceilometer:ceilometer@10.133.157.71:5672//
topics=notifications
```

启动ceilometer服务
```
systemctl enable openstack-ceilometer-compute.service
systemctl start openstack-ceilometer-compute.service
```

重启nova-compute服务
```
systemctl restart openstack-nova-compute.service
```

### 五. 开启云硬盘服务计量
在cinder-volume节点上，修改配置文件`/etc/cinder/cinder.conf`
```
[DEFAULT]
...
volume_usage_audit_period = hour

[oslo_messaging_notifications]
...
driver = messagingv2
transport_url = rabbit://ceilometer:ceilometer@10.133.157.71:5672//
topics=notifications
```

重启cinder服务
控制节点
```
systemctl restart openstack-cinder-api.service openstack-cinder-scheduler.service
```
存储节点
```
systemctl restart openstack-cinder-volume.service
```

**注意，需要使用`cinder-volume-usage-audit`命令来获取计量值**

### 六.查看
控制节点上，执行命令
```
# ceilometer meter-list
```
可以看到以`image.*`,`volume.*`,`memory`,`vcpus`等等的计量名字，那么就说明配置成功了。


### 七. 总结
实际上我们在更改配置的时候，只是指定了`transport_url`这个参数，避免了使用默认的消息队列集群。那么这样一来，ceilometer收集数据的操作就不会影响其他组件了。我们甚至还可以修改相关代码，做到秒级获取数据等等操作，从而实现秒级计费功能。
 
  [1]: http://docs.openstack.org/developer/ceilometer/
