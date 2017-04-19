---
title: Centos安装Ceph
date: 2016-02-20 14:32:52
tags: 
- ceph
---
Ceph是可扩展、性能优异、分布式的存储系统，能够支持文件存储、对象存储、块存存储三种主流存储类型。Ceph还广泛应用于云计算领域，能够很好的支持OpenStack等平台。本文介绍如何安装Ceph
<!-- more -->

###环境介绍

* mon节点 publick network: 10.16.0.2
* osd1节点<br>publick network: 10.16.0.3<br>cluster network: 192.168.1.3
* osd2节点<br>publick network: 10.16.0.4<br>cluster network: 192.168.1.4
* osd3节点<br>publick network: 10.16.0.5<br>cluster network: 192.168.1.5


