if not exist mdict_path.json (
echo "set mdict path and audio path..."
python init_mdict_path.py
)
if not exist db.sqlite3 (
call init_server.bat
)
python manage.py runserver 0.0.0.0:8000