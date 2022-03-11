  * [在wsl上运行测试服务器](#在wsl上运行测试服务器)
  * [部署到wsl apache](#部署到wsl-apache)

### 在wsl上运行测试服务器

windows下建议部署到wsl1(ubuntu)，wsl2读取windows文件要慢于wsl1，导致查询速度会慢大约1/20-1/10，此外还要解决ip访问的问题。

1. 安装wsl，系统ubuntu。

[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

2. 切换到root用户，django需要安装到root用户下。

```
su root
```
3. cd到django-mdict目录，运行下列命令，转换脚本格式。

```
sudo apt-get update
sudo apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh django-mdict.conf run_server.sh mdict/readlib/pyx/build.sh
```

4. 运行run_server.sh，默认端口8000，该脚本仅适用于ubuntu，不适用于centos。

```
sudo bash run_server.sh
```

第一次运行会进行初始化。

首先要求从命令行输入词典库路径和发音库路径，没有就跳过。

最后要求输入django用户名和密码。

5. 本机访问http://127.0.0.1:8000/mdict

已知问题：在ubuntu20.04下，由于多进程的原因，run_server.sh运行过程中，migrate等命令无法自动结束，需要手动ctrl+c结束，在ubuntu18.04下正常。

### 部署到wsl apache

部署到apache后启动速度远慢于启动测试服务器（manage.py），且占用内存增大，因为MPM导致创建了多个进程池。

1. 安装wsl，系统ubuntu。

[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

2. 切换到root用户，django需要安装到root用户下。

```
su root
```
3. cd到django-mdict目录，运行下列命令，转换脚本格式。

```
sudo apt-get update
sudo apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh django-mdict.conf run_server.sh mdict/readlib/pyx/build.sh
```

4. 运行init_wsl.sh，默认端口80，该脚本仅适用于ubuntu，不适用于centos。

```
sudo bash init_wsl.sh
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