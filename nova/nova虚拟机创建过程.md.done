---
title: Nova创建虚拟机的过程
date: 2016-03-15 16:15:33
tags:
- openstack
- nova
---

本文介绍了nova创建虚拟机的过程，网上相关的资料也很多，就算是一篇归类总结吧。
<!-- more -->

![](https://blog.apporc.org/wp-content/uploads/2016/04/nova.png)
**建议新标签页打开**

##Nova服务介绍
- Nova-api：Nova-api服务为是整个计算服务的web入口，为用户或者别的组件提供了RESTFUL API。
- Nova-conductor：Nova-conductor主要有两个作用，一个是为Nova-compute服务提供数据库操作代理，确保计算节点不直接操作数据库。第二个作用是当我们需要进行一些复杂的、长流程的操作时，比如“创建虚拟机”、“迁移虚拟机”等操作时，需要Nova-conductor来协调操作。
- Nova-scheduler：Nova-scheduler的主要功能是根据制定的策略来进行调度分配任务。、
- Nova-compute：Nova-compute的作用就是直接管理虚拟机，利用libvirt等工具执行具体的操作。

##Nova创建虚拟机的过程

###nova-api
nova-api接收到创建虚拟机的请求之后，最终会调用`nova/api/openstack/compute/servers.py`模块的`create()`方法。
该方法。该方法会根据传入的参数以及默认的参数，补全创建虚拟机所需的参数。

之后再调用`nova/compute/api.py`中的`API.create()`方法、`API._create_instance()`方法。在`API._create_instance()`方法中，首先会检查所有输入参数，然后再调用`_provision_instances()`方法将虚拟机的信息写入到数据库当中。(**所以并不是只由conductor来操作数据库，conductor只是为nova-compute代理数据库操作**)。此时我们可以在`_populate_instance_for_create()`方法中看到，虚拟机的状态现在为`vm_states.BUILDING`，创建任务的状态为`task_states.SCHEDULING`。

在数据库表中插入相关的虚拟机条目之后，再调用`nova/conductor/api.py`模块中的`ComputeTaskAPI.build_instances()`方法来进行RPC调用。调用的代码就是`nova/conductor/rpcapi.py`模块中的`ComputeTaskAPI.build_instances()`方法，该方法中，将虚拟机的调度信息和其他网络、磁盘等信息封装好后，再由`oslo.messaging`提供的`rpc_client`发送出去，进入消息队列当中, 消息类型是`topic`类型，具体的值是`conductor`类型的。

###nova-conductor
nova-conductor利用`oslo.service`提供的服务以及`nova/conductor/manager.py`模块中的`ComputeTaskManager`类对象来进行服务的接收。(题外话：其实我们可以很清晰的看得出来nova每个组件的代码结构，除了`nova-api`模块之外`nova/xxx/api.py`就是该模块提供出来，给其他组件调用的API；`nova/xxx/rpcapi.py`则是被`nova/xxx/api.py`模块调用，相当于有了一层代理，避免了直接调用rpc接口。消息发出后，`nova/xxx/manager.py`模块则接受当前组件rpc发送出来的消息，然后完成具体操作。)

`ComputeTaskManager.build_instances()`方法首先解析rpc的消息，然后首先获取目标主机，调用`_schedule_instances()`方法来选择目标主机，实际调用的依次是`SchedulerClient.select_destinations()`、`SchedulerQueryClient.select_destinations()`、`SchedulerAPI.select_destinations()`，然后将topic为`scheduler`的消息发送到消息队列当中，发送方式为`call`。

###nova-scheduler
同样的，`nova/scheduler/manager.py`模块中的`SchedulerManager`类对象开始执行`select_destinations()`方法。当查找到合适的物理主机之后，因为是`call`类型的调用，所以会`replay`回去，只不过这次的消息类型是`direct`，这样就发送回了之前的`nova-conductor`节点。

###nova-compute
`nova-conductor`知道要在哪台物理节点上创建机器之后，调用`nova/compute/rpcapi.py`的`build_and_run_instance()`方法，发送消息到消息队列。
`nova/compute/manager.py`模块的`ComputeManager`接受到消息之后，调用`build_and_run_instance()`方法来创建虚拟机。


`_do_build_and_run_instance()`方法开始实际进行创建的流程，主要的有两步操作：

* 创建虚拟机
* 如果创建失败，且设置了`retry`，那么再调用`ComputeTaskAPI.build_instances()`的方法，将创建请求再发送到`conductor`节点，重新再进行调度。

下面详细分析一下创建虚拟机的过程：

* `_build_and_run_instance()`方法里调用`_build_resources()`方法创建**网络**和**磁盘**资源。
* 资源创建分为两部分，`_build_networks_for_instance()`方法为虚拟主机创建网络资源；`_prep_block_device`为虚拟机创建磁盘资源
* 网络资源调用的是`nova/network/neutronv2/api.py`模块里的`allocate_for_instance()`方法，实际调用的就是`neutronclient`的代码。
* 磁盘资源调用的是`nova/volume/cinder.py`模块来创建的块设备。
* 之后便是创建虚拟机的操作。当资源准备完成后，vm_state设置为BUILDING，task_state这是为SPAWNING。之后将网络资源、块设备资源等整合起来，调用`nova/virt/libvirt/driver.py`模块的`spawn`方法。

`spawn()`方法里包含了三个最主要的方法：

* `create_image`被调用来创建系统盘，从代码里可以看出，如果代码支持**克隆**的话，那么直接就可以从后端存储中克隆一份镜像。否则就会将镜像从后端存储拉下来。目前`ceph`支持磁盘克隆，效果就是能够秒级创建虚拟机，性能比直接复制拷贝镜像快很多。
* `_get_guest_xml()`方法则会根据网络信息、块设备信息等创建虚拟机的xml文件。
* `_create_domain_and_network`这里将前面准备的周边资源整合起来。具体代码可以看到，首先对块设备进行操作，之后调用`plug_vifs()`方法创建网络配置，详细一点来说就是首先在`openvswtich`上创建端口，并将veth pair设备一端连接到openvswtich上，一端连接到linux bridge上。之后再设置linux bridge的防火墙规则。这些的网络组件的操作都是`nova-compute`完成的。最后，使用`_create_domain()`方法完成对虚拟机的创建。

创建完成之后，并不会立即返回，而是还需要调用`_wait_for_boot()`方法，当检测到power_state的状态为`RUNNING`时，那么虚拟机创建成功。

