#!/bin/bash
#!/usr/bin/env python3
cd `dirname  $0`
echo "installing dependencies..."
apt-get install -y python3 python3-pip zlib1g-dev liblzo2-dev
pip3 install -r requirements1.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
pip3 install -r requirements2.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
cd mdict/readmdict/pyx
echo "cython compiling..."
source build.sh
cd ../../../
file="db.sqlite3"
if [ ! -f $file ]; then
echo "initializing django..."
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py makemigrations mdict
python3 manage.py migrate mdict
python3 manage.py createsuperuser
fi
chmod 777 db.sqlite3
