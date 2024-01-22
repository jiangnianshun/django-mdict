cd /d %~dp0
echo "installing dependencies..."
echo "python-lzo needs to be installed manually... "
::pip install -r requirements1.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements1.txt
if not exist db.sqlite3 (
echo "initializing db.sqlite3..."
python manage.py makemigrations
python manage.py migrate
python manage.py makemigrations mdict
python manage.py migrate mdict
python manage.py makemigrations mynav
python manage.py migrate mynav
python manage.py createsuperuser
)
else (
echo "db.sqlite3 already exists..."
)
cd mdict/readlib/pyx
echo "cython compiling..."
call build.bat
set "lj=%~p0"
set "lj=%lj:\= %"
for %%a in (%lj%) do set wjj=%%a
if "%wjj%"=="pyx" (
cd ../../../
)