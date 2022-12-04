if not exist mdict_path.json (
echo "set mdict path and audio path..."
python init_mdict_path.py
)
call init_server.bat
start python manage.py runserver 0.0.0.0:18000 --noreload
choice /t 3 /d y /n >nul
start http://127.0.0.1:18000/
exit