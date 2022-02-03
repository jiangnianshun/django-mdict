### 更新

1. 重新git clone或者原项目git pull。
2. 删除根目录下的.cache缓存文件夹，并清除浏览器缓存（不需要清cookie）。
3. 如果需要保存旧数据（词典排序，词典分组，内置词条，导航网站等），将旧的db.sqlite3文件复制过来（可能会有不兼容，需要手动处理），并将/media/uploads/和/media/icon/文件夹复制过来。
4. 如果需保存查询历史，将旧的根目录下所有history开头的dat文件移动到新的django-mdict根目录。
5. 然后运行一次run_server.bat（run_server.sh），这将安装新添加的依赖并重新cython编译。

### 读取数据库报错

* 如果修改了models.py文件，旧数据库可能无法正常使用，尝试运行

```
python manage.py makemigrations mdict
python manage.py migrate mdict
```

如果仍然无法恢复正常，可尝试手动导入。

1. 将旧的db.sqlite3改名。
   
2. 删除mdict_path.json，重新运行run_server.bat或run_server.sh，词典库路径留空，生成新的数据库。

3. 删除mdict文件夹下的migrations和__pycache__。
   
4. 用软件导出所有mdict开头的数据表，再导入到新的数据库中。

以DB browser for SQLite软件为例，打开旧数据库，选择菜单文件/导出/导出数据库到SQL文件，选择所有mdict开头的表，勾选在insert into语句中保留列名，然后导出。

如果第2步没有删除mdict_path.json，导致新的数据库又导入了词典信息，那么这里应当手动将新数据库中mdict_mdictdic数据表中的记录都清空。

打开新数据库，导入刚才的sql文件，是否创建新数据库选择no，导入完成后保存数据库。