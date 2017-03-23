---
title: Paste-Deploy简略使用教程
date: 2016-05-13 10:51:52
tags: 
- openstack
- python
- wsgi
---
在Python web应用程序中，WSGI (Web Server Gateway Interface)协议是连接Python应用框架和web服务器之间的桥梁。Paste-Deploy的作用，就是方便我们快速的构建wsgi application的组件。
<!-- more -->
Paste.deploy通过配置文件或者Python Egg为应用程序提供了构建WSGI应用程序的入口。通过`loadapp`方法，将配置文件或Egg包构建成WSGI应用程序。

##配置文件

一份配置文件包含不同的章节。其中章节的声明格式如下：
> [type:name]

以下是一些常用的类型

1. 应用，app，application；
2. 过滤器，filter；
3. 管道，pipeline；
4. 工厂函数，factory；
5. 组合， composite；
6. 类型， type；
7. 段， section

其中，方括号括起的section声明一个新section的开始，section的声明由两部分组成，section的类型（type）和section的名称（name），如：[app:main]等。section的type可以有：app、composite、filter、pipeline、filter-app等。

每个section中具体配置项的格式就是基本的ini格式： key = value ，所有从PasteDeploy配置文件中提取的参数键、值都以字符串的形式传入底层实现。

此外，PasteDeploy的配置文件中使用“#”标注注释

一份配置文件包含这不同的章节，我们来看一下一份[官网](http://pastedeploy.readthedocs.io/en/latest/index.html)提供的示例文档。

>[composite:main]<br>
use = egg:Paste#urlmap<br>
/ = home<br>
/blog = blog<br>
/wiki = wiki<br>
/cms = config:cms.ini<br>
 
>[app:home]<br>
use = egg:Paste#static<br>
document_root = %(here)s/htdocs<br>
 
>[filter-app:blog]<br>
use = egg:Authentication#auth<br>
next = blogapp<br>
roles = admin<br>
htpasswd = /home/me/users.htpasswd<br>
 
>[app:blogapp]<br>
use = egg:BlogApp<br>
database = sqlite:/home/me/blog.db<br>
 
>[app:wiki]<br>
use = call:mywiki.main:application<br>
database = sqlite:/home/me/wiki.db<br>

接下来我来看一下每个章节什么意思

###composite

>[composite:main]<br>
use = egg:Paste#urlmap<br>
/ = home<br>
/blog = blog<br>
/wiki = wiki<br>
/cms = config:cms.ini<br>

composite类型的主要作用是**通过`egg:Paste#urlmap`这个方法，根据`URL`的不同，将请求转到不同的app中进行处理**。我们可以看到，这个章节当中会有一个`use`字段，这个字段就是表明该使用什么Python代码完成这个分发的操作。

###app
>[app:blogapp]<br>
use = egg:BlogApp<br>
database = sqlite:/home/me/blog.db<br>

app类型则表明这里使用一个wsgi application。这里可以通过`use`指定很多中调用方式。例如：

>\#通过别的配置文件中的app章节运行
>[app:myapp]<br>
use = config:another_config_file.ini#app_name<br>
 
>\#通过带三方库MyApp
>[app:myotherapp]<br>
use = egg:MyApp<br>
 
>\#直接调用自己的模块、类对象或者方法来运行
>[app:mythirdapp]<br>
use = call:my.project:myapplication<br>

>\#调用本文件下的的其他app章节
>[app:mylastapp]<br>
use = myotherapp<br>

###filter-app

>[filter-app:blog]<br>
use = egg:Authentication#auth<br>
next = blogapp<br>
roles = admin<br>
htpasswd = /home/me/users.htpasswd<br>
 
>[app:blogapp]<br>
use = egg:BlogApp<br>
database = sqlite:/home/me/blog.db<br>

filter-app实际上是一个过滤器。可以设定一些过滤条件等，对请求进行过滤。除了过滤之外，只要调用`blog`这个过滤器，那么这个方法就会被执行，也就是我们可以在过滤器中添加一些打日志等等通用操作。
filter-app必须要有next属性，以表明过滤器执行完成之后，需要将请求传递给下一个app或者过滤器。

###filter

>[app:main]
use = egg:MyEgg
filter-with = printdebug

>[filter:printdebug]
use = egg:Paste#printdebug
\# and you could have another filter-with here, and so on...

filter和filter-app功能差不多，只不过一个(filter)是需要在app中表明该使用什么filter；一个(filter-app)是在自身内部表明该使用哪个app进行之后的操作。

###pipeline

>[pipeline:main]<br>
pipeline = filter1 egg:FilterEgg#filter2 filter3 app<br>
 
>[filter:filter1]<br>
...<br>

pipeline实际上就是一个filter的集合，作用很简单，就是在`pipeline`的value当中，按照过滤顺序排列过滤器。只不过要注意的是，最后的项必须是**app**或者是**filter-app**。


###基本用法

在代码中引入`loadapp`方法之后，指定配置文件，然后组成wsgi application

```python
from paste.deploy import loadapp
wsgi_app = loadapp('config:/path/to/config.ini')
```


###全局变量

在Paste.deploy中，还可以设置全局的变量，方法就是在`[DEFAULT]`下面定义。

>[DEFAULT]<br>
admin_email = webmaster@example.com<br>
 
>[app:main]<br>
use = ...<br>
set admin_email = bob@example.com<br>

如果要自己修改一下这个参数，可以使用`set`

##Factory

除了一般的`use`方法，我们还可以在遵循特定的协议的情况下，是有自己编写的过滤器、应用、中间件等等。这个协议就是Paste-Deploy规定的一些工厂方法。

常用的工厂方法包括：`paste.app_factory`、`paste.composite_factory`、`paste.filter_factory`等，这些所谓的协议，其实也就是规定传入参数和返回值。不同的工厂函数，参数可能会有不同，返回值类型也会有所不同。

####paste.app_factory
这个工厂函数最后返回的wsgi应用程序，具体形式如下：
```python
def app_factory(global_config, **local_config):
    """
    global: 全局配置参数，以“字典”形式传入
    local_config：局部配置参数，以“关键字参数”形式传入
    """
    def wsgi_app(environ, start_response):
        start_response('200 OK', [('Content-type', 'text/html')])
        return ['Hello, World\n']

    return wsgi_app
```


####paste.composite_factory
组合类工厂方法除了接收

