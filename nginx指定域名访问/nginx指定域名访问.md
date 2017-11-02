---
title: Nngix指定域名访问
date: 2017-11-02 11:21:32
tags: 
- HTTP
- nginx
---

nginx可以绑定域名访问。
<!-- more -->

假设在配置文件nginx.conf中，初始配置如下：
```
server {
    listen 80 default_server;
    server_name www.lnmp.org;

    #....
}
```

然后更改配置如下：
```
server {
    listen 80;
    server_name my.domain.name;

    #....
}
```

再在上个server段添加如下配置：
```
server {
    listen 80 default_server;
    server_name _;
    return 403;
}
```
表示当匹配到ip或者除开my.domain.name域名的访问请求的时候，就返回403。