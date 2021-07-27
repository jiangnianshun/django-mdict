1. 加入新的词典没有显示

重启django-mdict，只有启动时才会检查文件夹变动。
如果重启无效，尝试手动删除根目录下的.Windows.cache，.Windows.dat，.Linux.cache，.Linex.dat文件后再重启。

2. 部署在wsl上，前端的js、css等无法更新。

因为django-mdict.conf里设置了expires_module，使得浏览器长期缓存文件，手动删除浏览器的缓存文件（不需要清cookie）。

3. 显示\[INIT_UTILS WARNING\] loading readmdict lib failed!

出现该提示说明没有进行cython编译。

windows下运行django-mdict/mdict/readlib/pyx/build.bat，linux下运行django-mdict/mdict/readlib/pyx/build.sh。

这将对readmdict.py进行编译，编译后的pyd或so运行库在django-mdict/mdict/readlib/lib/下，编译后相比于没有编译，速度提升约1/3。

4. 403错误和Operation not permitted

权限问题，提升django-mdict文件夹及子文件的权限。

```
chmod -R 777 django-mdict
```

可能需要手动删除.Linux.cache和.Linux.dat等缓存文件。

可能需要提升词典库中zim文件抽取出的idx文件的权限。

5. Failed to enable APR_TCP_DEFER_ACCEPT

```
sudo vim /etc/apache2/apache2.conf
```

在文件末尾加入

```
AcceptFilter http none
```

6. sleep: cannot read realtime clock: Invalid argument

```
sudo mv /bin/sleep /bin/sleep~
touch /bin/sleep
chmod +x /bin/sleep
```

7. apache在ubuntu20.04下restart和stop失败

多进程的问题，多重复几次。

8. 保存数据时报错attempt to write a readonly database

修改db.sqlite3的权限。

9. 内置词条存在，但是无法查询到。

尝试将该词条重新保存。

10. windows下关闭djnago-mdict后，后台残留僵尸进程。

注销或重启系统。

11. run_server.sh: line 16: syntax error: unexpected end of file

需要转换脚本格式

12. Error: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。

默认端口8000被占用，尝试使用其他端口。

```
python manage.py runserver 0.0.0.0:7000
```