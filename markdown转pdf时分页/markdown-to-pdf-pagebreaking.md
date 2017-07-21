---
title: Markdown转PDF时实现分页效果
date: 2017-07-21 15:51:32
tags: 
- Markdown
---

当我们需要将Markdown文件转换为PDF文件时，会发现Markdown语法并没有换页的功能，这给排版带来了很大的不方便，鉴于这种情况，我们可以使用HTML标签的方式来实现分页的效果
<!-- more -->

当需要进行分页的时候，只需要在分页处添加
```HTML
<div style="page-break-after: always;"></div>
```
即可。实现的效果就是我们在预览Markdown生成的HTML页面时，是看不到有分页效果的，之后在右键点击页面打印之后，就可以在预览页面看到分页效果。

以上方法在Google Chrome 59.0.3071.115以及IE11上测试通过。