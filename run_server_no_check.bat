start python manage.py runserver 0.0.0.0:18000 --noreload
choice /t 3 /d y /n >nul
start http://127.0.0.1:18000/
exit