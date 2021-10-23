  * [在windows上运行测试服务器](#在windows上运行测试服务器)
  * [在wsl上运行测试服务器](#在wsl上运行测试服务器)
  * [部署到wsl apache](#部署到wsl-apache)

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

跳过后采用lzo编码的mdx词典无法读取。

[https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo)

python版本3.7就选cp37，python是32位选择win32，是64位选择win_amd64。

比如下载了python_lzo-1.12-cp37-cp37m-win_amd64.whl，在当前目录运行以下命令安装

```
pip install python_lzo-1.12-cp37-cp37m-win_amd64.whl
```

4. 下载django-mdict

```
git clone https://github.com/jiangnianshun/django-mdict.git --depth=1
```

Windows下双击运行run_server.bat，第一次运行会进行初始化（安装依赖，cython编译）。

初始化过程中首先会弹出文件夹选择框，第一次选择字典库路径，第二次选择发音库路径（没有就跳过）。

路径信息保存在mdict_path.json文件中。

最后要求设置django的用户名和密码，邮箱不需要填写。

5. django服务器默认端口8000
<br />本地电脑访问http://127.0.0.1:8000/mdict/
<br />其他设备访问http://本机ip:8000/mdict/
<br />可能需要设置防火墙入站链接，开放8000端口。

### 在wsl上运行测试服务器

windows下建议部署到wsl1(ubuntu)，wsl2读取windows文件要慢于wsl1，导致查询速度会慢大约1/20-1/10，此外还要解决ip的问题。

1. 安装wsl，系统ubuntu，建议使用18.04。

[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

2. 切换到root用户，django需要安装到root用户下。

```
su root
```
3. cd到django-mdict目录，运行下列命令，转换脚本格式。

```
apt-get update
apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh django-mdict.conf run_server.sh mdict/readlib/pyx/build.sh
```

4. 运行run_server.sh，默认端口8000，该脚本仅适用于ubuntu，不适用于centos。

```
bash run_server.sh
```

第一次运行会进行初始化。

首先要求从命令行输入词典库路径和发音库路径，没有就跳过。

最后要求输入django用户名和密码。

5. 本机访问http://127.0.0.1:8000/mdict

已知问题：在ubuntu20.04下，由于多进程的原因，run_server.sh运行过程中，migrate等命令无法自动结束，需要手动ctrl+c结束，在ubuntu18.04下正常。

### 部署到wsl apache

windows下建议部署到wsl1(ubuntu)。部署到apache后的启动速度远慢于启动自带的测试服务器。

1. 安装wsl，系统ubuntu，建议使用18.04。

[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

2. 切换到root用户，django需要安装到root用户下。

```
su root
```
3. cd到django-mdict目录，运行下列命令，转换脚本格式。

```
apt-get update
apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh django-mdict.conf run_server.sh mdict/readlib/pyx/build.sh
```

4. 运行init_wsl.sh，默认端口80，该脚本仅适用于ubuntu，不适用于centos。

```
bash init_wsl.sh
```

首先要求从命令行输入词典库路径和发音库路径，没有就跳过。

最后要求输入django用户名和密码。

5. 本机访问http://127.0.0.1/mdict

6. 设置wsl自启动脚本

windows下运行shell:startup，建立脚本文件ubuntu.vbs，内容为

```
Set ws = CreateObject("Wscript.Shell")
ws.run "wsl -d ubuntu -u root /etc/init.d/apache2 start", vbhid
```

其中ubuntu是发行版名称，具体名称用命令wsl -list来查看。

7. apache常用命令

```
启动apache
sudo service apache2 start
重启apache
sudo service apache2 restart
停止apache
sudo service apache2 stop
```

ubuntu上apache错误日志的位置/var/log/apache2/error.log