---
title: 生成requirement.txt
date: 2016-06-14 17:23:52
tags: 
- python
---
python使用requirement.txt文件来指定项目的依赖关系。自动从项目中生成requirement.txt就很有必要了
<!-- more -->

##使用pip

我们可以直接使用pip来生成requirement.txt
```shell
pip freeze > requirement.txt
```

使用以上命令可以生成requirement.txt。但是缺点也很明显，这会把项目没有用到的包也包含进去，所以不建议

##使用pipreqs

pipreqs能够在项目文件中通过`import`语句来生成requirement.txt

```shell
pipreqs /path/to/project
```

*项目路径即setup.py文件所在文件夹*