* 如果不需要保存旧数据，重新git clone，并清除浏览器缓存（不需要清cookie）。

如果requirements1.txt中有新增的依赖，需要安装依赖。

```
pip install -r requirements1.txt
```

如果需要转移保存的查询历史，将旧的django-mdict根目录下所有history开头的dat文件移动到新的django-mdict根目录。

* 如果需要保存旧数据，运行git pull更新项目，然后清除浏览器缓存（不需要清cookie）。

```
git pull
```

如果有pyx文件的修改，需要手动运行build.bat或build.sh编译pyx文件。

如果requirements1.text中有新增的依赖，需要安装依赖。

```
pip install -r requirements1.txt
```

如果有模型改动(models.py)，旧数据库可能无法正常使用，尝试运行

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