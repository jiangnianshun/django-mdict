cd /d %~dp0
echo "installing dependencies..."
echo "python-lzo needs to be installed manually... "
pip install -r requirements1.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if not exist db.sqlite3 (
echo "initializing django..."
python manage.py makemigrations
python manage.py migrate
python manage.py makemigrations mdict
python manage.py migrate mdict
python manage.py createsuperuser
)
cd mdict/readlib/pyx
echo "cython compiling..."
call build.bat
cd ../../../