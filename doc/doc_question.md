1. 加入新的词典没有显示

重启django-mdict，只有启动时才会检查文件夹变动。
如果重启无效，尝试手动删除根目录下的.cache缓存文件夹后再重启。

2. 前端页面的js、css无效。

手动删除浏览器的缓存文件（不需要清cookie）。

3. 显示\[BASE_FUNC.CHECK_READLIB WARNING\]

提示没有进行cython编译。

windows下运行django-mdict/mdict/readlib/pyx/build.bat，linux下运行django-mdict/mdict/readlib/pyx/build.sh。

这将对readmdict.py进行编译，编译后的pyd或so运行库在django-mdict/mdict/readlib/lib/下，编译后相比于没有编译，速度提升约1/3。

4. 403错误，500错误和Operation not permitted

权限问题

4.1 尝试删除.cache缓存文件夹。

4.2 尝试提升django-mdict文件夹及所有子文件的权限。

```
chmod -R 777 django-mdict
```
4.3 尝试提升词典库中从zim文件抽取出的idx文件的权限。

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

在任务管理器手动结束python进程，或者注销或重启系统。

11. run_server.sh: line 16: syntax error: unexpected end of file

需要转换脚本格式

12. Error: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。

默认端口8000被占用，尝试使用其他端口，或者重启电脑。

```
python manage.py runserver 0.0.0.0:7000
```

13. 载入词典报错mdx loading failed 'Encoding'或mdd loading failed 'GeneratedByEngineVersion'。

该词典为mdxbuilder4.0生成的新格式的mdx词典，不支持。

14. 部件检索不显示结果。

查看是否忘记勾选即时查询。

15. ipad safari添加到主屏幕后，当词条很多时，底部按钮栏会随着页面一起滚动。

在设置中隐藏底部栏。

16. ipad safari在悬浮窗口状态下经常输入框无法唤出键盘。

将ipad键盘类型改为浮动键盘，并且收回悬浮窗后重新拉出。

17. urlopen error \[WinError 10061\] 由于目标计算机积极拒绝，无法连接。

windows下ws_server的端口8766被占用，启动失败。修改config.ini中的ws_server_port。