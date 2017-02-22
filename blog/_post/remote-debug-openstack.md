---
title: 远程调试Openstack代码
date: 2016-01-10 15:02:56
tags:
- Pycharm
- Openstack
- Debug
---
Openstack是开源的云计算平台，下面就分享一下如何远程调试Openstack代码。
<!-- more -->
### 1.准备工具
* Pycharm
* pycharm-debug.egg

### 2.修改代码
将./nova/cmd/\__init__.py文件中代码改为如下所示
```python
if debugger.enabled():
    # turn off thread patching to enable the remote debugger
    eventlet.monkey_patch(os=False, thread=False)
else:
    eventlet.monkey_patch(os=False, thread=False)
```
目的是关闭eventlet对线程的补丁，方便我们调试。

这里我们没有直接使用debugger.enable()的方法，因为如果使用这种方法的话，每次每次重启服务都要加上`--remote_debug-host`和`--remote_debug-port`这两个参数。这部分的具体代码可以再./nova/debugger.py中看到。

### 3.安装debug软件包
这里以CentOS为例，在Pycharm的安装目录下的`debug-eggs`目录下有两个.egg文件。导入到Openstack环境后使用rpm安装即可，不需要其他依赖包。
```
$ rpm -ivh pycharm-debug.egg
```

### 4.Pycharm设置
在已有项目中添加远程调试配置。

![Markdown](http://i1.piimg.com/575242/a3279379b15e85f1s.png)
![Markdown](http://i1.piimg.com/575242/ec43d6e3ce636450s.png)
![Markdown](http://i1.piimg.com/575242/d69440bf48f2bf57s.png)
完善相关信息之后，可以设置相关的路径映射。调试的时候就不需要再从远程服务器中下载代码文件了。
![Markdown](http://i1.piimg.com/575242/3fc601e822d68ad9s.png)

设置完成后就点击右上角的虫子图标开启debug服务器了。

### 5.断点设置
开启debug服务之后，Pycharm就开始等待连接。
![Markdown](http://i1.piimg.com/575242/121ff4d16283256bs.png)

我们只需要在远程主机上的需要打断点的地方添加以下两行代码：
```python
import pydevd
pydevd.settrace('10.133.146.179', port=51234, stdoutToServer=True, stderrToServer=True)
```
*注意：host和port根据自己填写的进行修改*

### 6.开始调试
当代码执行到断点处时，pydevd就会连接上本机的pycharm调试服务，然后就可以进行单步跟踪等等调试操作了。

