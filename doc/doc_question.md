1. 加入新的词典没有显示

尝试手动删除根目录下的.cache缓存文件夹后再重启。

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

10. windows下关闭django-mdict后，后台残留僵尸进程。

在任务管理器手动结束python进程，或者注销或重启系统。

11. run_server.sh: line 16: syntax error: unexpected end of file

需要转换脚本格式

12. Error: [WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。

默认端口8000端口被占用，或者ws_server.py运行的18766端口被占用，尝试使用其他端口，或者重启电脑。

8000端口被占用

```
python manage.py runserver 0.0.0.0:另一个端口号
```

18766端口被占用，修改config.ini中的ws_server_port。

13. 载入词典报错mdx loading failed 'Encoding'或mdd loading failed 'GeneratedByEngineVersion'。

该词典为mdxbuilder4.0生成的新格式的mdx词典，不支持。

14. 部件检索不显示结果。

查看是否忘记勾选即时查询。

15. ipad safari添加到主屏幕后，当词条很多时，底部按钮栏会随着页面一起滚动。

在设置中隐藏底部栏。

16. ipad safari在悬浮窗口状态下经常输入框无法唤出键盘。

将ipad键盘类型改为浮动键盘，并且收回悬浮窗后重新拉出。

17. urlopen error \[WinError 10061\] 由于目标计算机积极拒绝，无法连接。

windows下ws_server的端口8766被占用，启动失败。重启电脑解除占用，或者修改config.ini中的ws_server_port。

18. 新的nltk版本报错Resource omw-1.4 not found.

下载omw1.4.zip放置到django-mdict/media/nltk_data/corpora/文件夹下。

19. sqlite3.9.0 or later is required

升级sqlite版本

20. django升级到4.1版本后，ckeditor无效且js的引用显示为字符串。

升级django-js-asset

```
pip install -U django-js-asset
```

[https://github.com/django-ckeditor/django-ckeditor/issues/727](https://github.com/django-ckeditor/django-ckeditor/issues/727)

21. django-mdict文件夹以及词典所在文件夹内的文件被占用，可能出现以下报错

报错：OSError: Permission denied（需等待文件解除占用）

报错：django.db.utils.OperationalError: disk I/O error（需等待文件解除占用）

报错：django.db.utils.DatabaseError: database disk image is malformed（需要对db.sqlite3文件进行修复）

不要将django-mdict文件夹以及词典所在文件夹设置为同步软件的同步文件夹。

22. django.db.utils.DatabaseError: database disk image is malformed

以windows为例：

a. [下载sqlite工具](https://www.sqlite.org/download.html)

a.1 下载sqlite-dll-win-x64-3460000.zip，解压到某个路径

a.2 将该路径加入到系统环境变量Path中

b. 修复db.sqlite3文件

b.1. 在cmd中cd到django-mdict根目录

b.2. 将损坏的db.sqlite3的内容导出到db.sql

```
sqlite3 db.sqlite3
.mode insert
.output db.sql
.dump
.exit
```

b.3. 将db.sql最后一行的ROLLBACK;改成COMMIT;。

b.4. 将db.sql导出为export.sqlite3

```
sqlite3
.open export.sqlite3
.read db.sql
.exit
```

b.5. 检查完整性，修复成功应当显示ok。

```
sqlite3 export.sqlite3
PRAGMA integrity_check;
.exit
```

b.6. 将export.sqlite3重命名并替换损坏的db.sqlite3

b.7. 如果django-mdict部署在wsl中，还需在wsl中更改db.sqlite3的读写权限

```
chmod 777 db.sqlite3
```

b.8. 删除django-mdict根目录下的.cache文件夹

23. django.db.utils.OperationalError: attempt to write a readonly database

更改db.sqlite3文件的读写权限.