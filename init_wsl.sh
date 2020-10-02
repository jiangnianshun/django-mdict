#!/bin/bash
#!/usr/bin/env python3
cd `dirname  $0`
apt-get install -y python3 python3-pip apache2 libapache2-mod-wsgi-py3 zlib1g-dev liblzo2-dev
source init_server.sh
cd ..
chmod -R 777 django-mdict
cd django-mdict
sed -i '19a\define PRJTROOT '$(cd `dirname $0`; pwd) django-mdict.conf
cp django-mdict.conf /etc/apache2/sites-available/django-mdict.conf
sed -i '$a\\nexport LANG="en_US.UTF-8"' /etc/apache2/envvars
sed -i '$a\\nexport LC_ALL="en_US.UTF-8"' /etc/apache2/envvars
sed -i '$a\\nAcceptFilter http none' /etc/apache2/apache2.conf
a2dissite 000-default.conf
a2ensite django-mdict.conf
mv /bin/sleep /bin/sleep~
touch /bin/sleep
chmod +x /bin/sleep
python3 init_mdict_path.py
