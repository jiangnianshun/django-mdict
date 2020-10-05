## django-mdict

### 简介

django-mdict是django实现的mdict词典查询工具。

### 在windows上运行测试服务器

1. 安装python3。

2. 安装Microsoft C++ Build Tools，在安装nltk、python-Levenshtein等库以及进行cython编译时需要该工具，安装时勾选C++开发组件。

[https://visualstudio.microsoft.com/zh-hant/visual-cpp-build-tools/
](https://visualstudio.microsoft.com/zh-hant/visual-cpp-build-tools/
)

3. 下载解压，如果文件夹名不是django-mdict就改成django-mdict，然后命令行cd到django-mdict文件夹。

4. 运行run_server.bat，第一次运行会进行初始化（安装依赖，cython编译）。

Windows下运行（双击运行或使用cmd运行，不要用powershell）

```
run_server.bat
```

首先会弹出文件夹选择框，第一次选择字典库路径，第二次选择发音库路径，路径记录在mdict_path.json文件中。

最后要求设置django的用户名和密码。

5. django服务器默认端口8000
<br />本地电脑访问http://127.0.0.1:8000/mdict/
<br />其他设备访问http://本机ip:8000/mdict/
<br />可能需要设置防火墙入站链接，开放8000端口。

### 说明文档

[说明文档](documentation.md)