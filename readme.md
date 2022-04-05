## django-mdict

[English](doc/readme_en.md)

### 简介

django-mdict是django实现的mdict词典查询工具（支持mdx、zim格式）。

### 适用情景

局域网内，将django-mdict部署在服务器上，其他电脑、平板、手机可只保留少量词典，当离开局域网时，查询本地词典，当进入局域网时，可通过浏览器对全部词典进行查词。

django-mdict不是词典软件，是词典查询的脚本工具，主要目的是解决词典数量多，手机容量不足的问题，是对其他词典软件局域网在线查询功能的补充。优先使用正式软件，如goldendict、mdict、欧陆、dicttango等。

### 在windows上运行测试服务器

1. 安装python3。

2. （可跳过）安装Visual Studio（同时安装C++开发组件），或者安装Microsoft C++ Build Tools（安装时勾选C++开发组件）。

在进行cython编译时需要C++编译器，跳过后无法进行cython编译，查询速度变慢。

Visual Studio地址：

[https://visualstudio.microsoft.com/downloads/](https://visualstudio.microsoft.com/downloads/)

Microsoft C++ Build Tools地址：

[https://visualstudio.microsoft.com/visual-cpp-build-tools/
](https://visualstudio.microsoft.com/visual-cpp-build-tools/
)

3. （可跳过）安装python-lzo，python-lzo在windows下需要手动安装。

不建议跳过，跳过后采用lzo编码的mdx词典无法读取。

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

Windows下双击运行run_server.bat，第一次运行会进行初始化（安装依赖，cython编译，创建数据库db.sqlite3）。

运行过程中会弹出两次文件夹选择框，第一次选择词典库路径（可跳过），第二次选择发音库路径（可跳过）。

路径信息保存在mdict_path.json文件中。

最后要求输入django的用户名、邮箱和密码，邮箱不需要填写。

5. django服务器默认端口8000
<br />本地电脑访问http://127.0.0.1:8000/mdict/
<br />其他设备访问http://本机ip:8000/mdict/
<br />可能需要设置防火墙入站链接，开放8000端口。

6. 完成初始化后每次运行run_server_no_check.bat启动即可。
   
### 注意

1. 保证文件夹名是django-mdict而不是django-mdict-master或其他名字以确保脚本运行正确。

2. 确保当前用户对django-mdict及所有子文件拥有权限，ubuntu上使用chmod -R 777 django-mdict，windows上在django-mdict文件夹上右键，在属性/安全中将本机账户添加进去并设置权限为完全控制。

3. 不建议使用pypy，有时候查询快，有时候反而更慢。

4. linux下可能需要转换脚本格式才能正常运行。

```
sudo apt-get update
sudo apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh init_server_brew.sh init_server_yum.sh django-mdict.conf run_server.sh run_server_brew.sh run_server_yum.sh mdict/readlib/pyx/build.sh
```

6. 每次更新为了避免出问题，需要手动清除浏览器缓存（不需要清cookies），删除根目录下的.cache缓存文件夹，并重新运行一遍run_server.bat或run_server.sh脚本。对于PWA或添加到桌面图标，需要删除后重新添加。

7. 本机浏览器可以打开，但局域网下其他设备无法打开。检查防火墙入站连接是否开放了8000端口，检查当前网络为专用网络而非公用网络，检查设备接入的是否是同一局域网。

### 说明文档

[功能实现](doc/doc_func.md)

[常用操作](doc/doc_op.md)

[说明文档](doc/doc_index.md)

[运行](doc/doc_deploy.md)

[更新](doc/doc_update.md)

[样式](doc/doc_style.md)

[可能的问题](doc/doc_question.md)

### 分流

百度网盘：https://pan.baidu.com/s/1bwv5TXZ7SpyVVjpSVi3h4g 

提取码：76xe

GoogleDrive：https://drive.google.com/drive/folders/1Zbf-tix4Nkz8MDgSA9yK2b0EdihCo_Lv?usp=sharing