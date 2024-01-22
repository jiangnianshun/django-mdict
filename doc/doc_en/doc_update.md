### Update

1. Re clone or git pull the original project.
2. Delete the .cache folder in the root directory and clear the browser cache (no cookies required).
3. If you need to save old data (dictionary sorting, dictionary grouping, built-in entries, navigation website, etc.), copy the old db.sqlite3 file (there may be incompatibilities and need to be processed manually), and copy folders /media/uploads/ and /media/icon/.
4. If you need to save the query history, move all history*.dat files in the old root directory to the new django-mdict root directory.
5. Then run run_server.bat (run_server.sh) once, which will install the newly added dependencies and recompile cython.

### Reading database error

* If the models.py file is modified, the old database may not work properly. Try running


```
python manage.py makemigrations mdict
python manage.py migrate mdict
```

If it still doesn't work, try importing it manually.

1. Rename the old db.sqlite3.
   
2. Delete mdict_path.json, re-run run_server.bat or run_server.sh, leave the dictionary path blank, and generate a new database.

3. Delete migrations and \_\_pycache\_\_ under the mdict folder.
   
4. Use software to export all database tables starting with mdict, and then import them into a new database.

Taking the DB browser for SQLite software as an example, open the old database, select the menu File/Export/Export database to SQL file, select all tables starting with mdict, check to retain column names in the insert into statement, and then export.

If mdict_path.json was not deleted in step 2 and dictionary information was imported into the new database, then all records in the mdict_mdictdic data table in the new database should be manually cleared.

Open the new database, import the sql file just now, select no whether to create a new database, and save the database after the import is completed.