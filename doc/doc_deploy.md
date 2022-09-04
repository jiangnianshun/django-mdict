  * [在wsl上运行](#在wsl上)
  * [部署到wsl apache](#部署到wsl-apache)
  * [删除数据库中重复词典](#删除数据库中重复词典)
  * [威联通部署docker](威联通部署docker)
  * [生成docker镜像（windows）](生成docker镜像（windows）)

### 在wsl上运行

windows下建议部署到wsl1，wsl2读取windows文件要慢于wsl1，导致查询速度会慢大约1/20-1/10，此外还要解决ip访问的问题。

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
dos2unix init_wsl.sh init_server.sh init_server_brew.sh init_server_yum.sh init_server_apt.sh django-mdict.conf run_server.sh run_server_brew.sh run_server_yum.sh run_server_apt.sh mdict/readlib/pyx/build.sh
```

4. 运行run_server.sh，默认端口8000，该脚本适用于ubuntu（centos需要运行run_server_yum.sh）。

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
dos2unix init_wsl.sh init_server.sh init_server_brew.sh init_server_yum.sh init_server_apt.sh django-mdict.conf run_server.sh run_server_brew.sh run_server_yum.sh run_server_apt.sh mdict/readlib/pyx/build.sh
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

### 删除数据库中重复词典

1. 运行django shell

```
python manage.py shell
```

2. 运行下列代码，删除db.sqlite3数据库中词典文件名重复的词典

```
from mdict.models import MdictDic
all_dics = MdictDic.objects.all()
temp_dics = {}
for dic in all_dics:
    if dic.mdict_file in temp_dics.keys():
        dic.delete()
    else:
        temp_dics.update({dic.mdict_file: None})
```

### 威联通部署docker

1. 打开container station/创建，搜索django-mdict，点击安装。

2. 容器设置：

命令设置填写以下命令，8000可以替换为别的端口，进入点设置留空。

```
python3 manage.py runserver 0.0.0.0:8000 --noreload
```

高级设置/网络：网络模式选择host

高级设置/共享文件夹：

点击第一个新增：新增存储空间填写dmdict，挂载路径填写/code

点击第二个新增：挂载本机共享文件夹选择词典所在的路径，挂载路径填写/code/media/mdict/doc

点击创建

3. 其他设备访问nas ip:端口

### 生成docker镜像（windows）

1. 安装docker并运行

2. 删除根目录下的.git和huaci文件夹

3. 在wsl中运行以下命令进行格式转换（或者notepad++手动转换格式）

```
sudo apt-get update
sudo apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh init_server_brew.sh init_server_yum.sh init_server_apt.sh django-mdict.conf run_server.sh run_server_brew.sh run_server_yum.sh run_server_apt.sh mdict/readlib/pyx/build.sh
```

5. 在wsl中运行以下命令生成数据库文件db.sqlite3并设置用户名和密码

```
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py makemigrations mdict
python3 manage.py migrate mdict
python3 manage.py makemigrations mynav
python3 manage.py migrate mynav
python3 manage.py createsuperuser
```

6. 运行以下命令进行编译

```
docker compose build --progress=plain
```