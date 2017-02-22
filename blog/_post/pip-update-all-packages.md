---
title: pip更新所有的包
date: 2017-02-13 16:48:21
tags: 
- python
- pip
---

当有python第三方包需要批量更新的时候，我们可以使用以下脚本进行更新
```python
import pip
from subprocess import call

for dist in pip.get_installed_distributions():
    call("pip install --upgrade " + dist.project_name, shell=True)
```

**注意，在windows平台下，使用安装程序安装的python包是无法更新的**
