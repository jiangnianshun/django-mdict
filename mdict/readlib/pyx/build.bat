cd /d %~dp0
python setup.py build_ext --inplace
if %errorlevel%==0 (
echo "cython compiling success"
cd mdict/readlib/pyx
if not exist ../../../../lib (
mkdir "../../../../lib"
)
echo "copying pyd files to lib"
for /f "delims=" %%b in ('dir /b') do ( 
copy "%%b" "../../../../lib/%%b"
)
)
cd ../../../