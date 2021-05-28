## django-mdict

[English](doc/readme_en.md)

### 简介

django-mdict是django实现的mdict词典查询工具（支持zim格式）。

在线demo：[http://81.68.207.87/mdict/](http://81.68.207.87/mdict/)

### 适用情景

局域网内，将django-mdict部署在服务器上，其他电脑、平板、手机可只保留少量词典，当离开局域网时，查询本地词典，当进入局域网时，可通过浏览器对全部词典进行查词。

### 在windows上运行测试服务器

1. 安装python3。

2. 安装Visual Studio（同时安装C++开发组件），或者安装Microsoft C++ Build Tools（安装时勾选C++开发组件）。

在安装nltk、python-Levenshtein等库以及进行cython编译时需要C++开发组件。

Visual Studio地址：

[https://visualstudio.microsoft.com/downloads/](https://visualstudio.microsoft.com/downloads/)

Microsoft C++ Build Tools地址：

[https://visualstudio.microsoft.com/visual-cpp-build-tools/
](https://visualstudio.microsoft.com/visual-cpp-build-tools/
)

3. 安装python-lzo

[https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo)

python版本3.7就选cp37，python是32位选择win32，是64位选择win_amd64。

比如下载了python_lzo-1.12-cp37-cp37m-win_amd64.whl，在当前目录运行以下命令安装

```
python -m pip install python_lzo-1.12-cp37-cp37m-win_amd64.whl
```

4. 下载django-mdict

```
git clone https://github.com/jiangnianshun/django-mdict.git --depth=1
```

Windows下双击运行run_server.bat，第一次运行会进行初始化（安装依赖，cython编译）。

初始化过程中首先会弹出文件夹选择框，第一次选择字典库路径，第二次选择发音库路径（没有就跳过）。

路径信息保存在mdict_path.json文件中。

最后要求设置django的用户名和密码。

5. django服务器默认端口8000
<br />本地电脑访问http://127.0.0.1:8000/mdict/
<br />其他设备访问http://本机ip:8000/mdict/
<br />可能需要设置防火墙入站链接，开放8000端口。
   
### 注意

不要更新测试分支（test branch），测试分支可能无法正常运行，当测试分支稳定后会合并到主分支。

建议使用ubuntu进行部署(18.04或20.04，20.04有多进程无法结束的问题)。 

目前windows下查询速度与linux下相近，但存在僵尸进程的问题，需要改进。windows下可以部署到wsl1(ubuntu)。

不建议使用pypy，有时候查询快，有时候反而更慢。

linux下可能需要转换脚本格式

```
apt-get update
apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh django-mdict.conf run_server.sh mdict/readlib/pyx/build.sh
```

更新后为了避免出问题，需要手动清除浏览器缓存（不需要清cookies）。

建议每个物理核心分配30-50本词典，查询词典数=物理核心数*(30~50)，如果查询词典数大于这个数量，建议分组。

### 说明文档

[说明文档](doc/documentation.md)

[常用操作图文说明](doc/operation.md)

### 样式

![图片1](doc/img/structure.png?raw=true)

![图片2](doc/img/img1.jpg?raw=true)

![图片3](doc/img/img2.jpg?raw=true)

![图片4](doc/img/img3.jpg?raw=true)

### bug反馈
jiangnianshun@outlook.com