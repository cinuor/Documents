---
title: Nngix解决跨域问题(有认证权限)
date: 2016-06-16 16:36:32
tags: 
- HTTP
- nginx
---

很多时候需要使用Javascript调用别的域名下面的接口，但是不能更改现有接口，所以就需要使用Nginx来处理跨域问题。
<!-- more -->

当时用Javascript往另一个域名或IP上发送请求(`POST`, `GET`, `PUT`...)的时候，浏览器首先会发送一个`OPTIONS`的请求。这个请求的作用就是到服务器上去确定目标请求(POST, GET, PUT...)是否被服务器就允许。

如果这个请求不带任何认证信息的话，那么`OPTIONS`请求是不会有任何问题的。但是如果有token或别的认证信息的话，`OPTIONS`请求则会返回`401`

所以我们必须配置那些header是被允许的，一下是Nginx的配置：
```
server {
    listen 8080;

    location ^~/test/ {
        add_header 'Access-Control-Allow-Methods' 'GET,OPTIONS,PUT,DELETE' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
        add_header 'Access-Control-Allow-Origin' '$http_origin' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization,DNT,User-Agent,Keep-Alive,Content-Type,accept,origin,X-Requested-With,X-Auth-Token' always;

        if ($request_method = OPTIONS ) {
            #如果遇到OPTIONS请求，则返回200
            return 200;
        }

        proxy_pass http://test/;
    }
}
```