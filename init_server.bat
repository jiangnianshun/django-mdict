cd /d %~dp0
echo "installing dependencies..."
echo "python-lzo needs to be installed manually... "
pip install -r requirements1.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
cd mdict/readmdict/pyx
echo "cython compiling..."
call build.bat
cd ../../../
if not exist mdict_path.json (
echo "set mdict path and audio path..."
python init_mdict_path.py
)
if not exist db.sqlite3 (
echo "initializing django..."
python manage.py makemigrations
python manage.py migrate
python manage.py makemigrations mdict
python manage.py migrate mdict
python manage.py createsuperuser
)

pause