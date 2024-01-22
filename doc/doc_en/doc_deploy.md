  * [Running on wsl](#Running on wsl)
  * [Running on wsl with apache](#Running on wsl with apache)
  * [Delete duplicate dictionaries records in database](#Delete duplicate dictionaries records in database)
  * [Greate docker image on windows](#Greate docker image on windows)
  * [Running on QNAP with docker](#Running on QNAP with docker)

### Running on wsl

It is recommended to deploy to wsl1 on windows. Wsl2 reads Windows files slower than wsl1, causing the query speed to be about 1/20-1/10 slower. In addition, the problem of IP access must be solved.

1. Install wsl, system ubuntu.

[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

2. Switch to the root user. Django needs to be installed with the root user.


```
su root
```
3. cd to the django-mdict directory and run the following commands to convert the script format.


```
sudo apt-get update
sudo apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh init_server_brew.sh init_server_yum.sh init_server_apt.sh django-mdict.conf run_server.sh run_server_brew.sh run_server_yum.sh run_server_apt.sh mdict/readlib/pyx/build.sh
```

4. Run run_server.sh, the default port is 18000, this script is suitable for ubuntu (centos needs to run run_server_yum.sh).


```
sudo bash run_server.sh
```

It will be initialized on the first run.

First, it is required to enter the dictionary path and pronunciation library path from the command line. If not, skip it.

Finally, you are asked to enter your django username and password.

5. Access http://127.0.0.1:18000/mdict locally

Known issues: Under Ubuntu20.04, due to multiple processes, commands such as migrate cannot end automatically during the running of run_server.sh, and need to be ended manually with ctrl+c. It is normal under Ubuntu18.04.

### Running on wsl with apache

After deploying to apache, the startup speed is much slower than starting the test server (manage.py), and the memory usage increases because MPM causes multiple process pools to be created.

1. Install wsl, system ubuntu.

[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

2. Switch to the root user. Django needs to be installed under the root user.


```
su root
```
3. cd to the django-mdict directory and run the following commands to convert the script format.


```
sudo apt-get update
sudo apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh init_server_brew.sh init_server_yum.sh init_server_apt.sh django-mdict.conf run_server.sh run_server_brew.sh run_server_yum.sh run_server_apt.sh mdict/readlib/pyx/build.sh
```

4. Run init_wsl.sh, default port 80, this script only applies to ubuntu, not centos.


```
sudo bash init_wsl.sh
```

First, it is required to enter the dictionary path and pronunciation library path from the command line. If not, skip it.

Finally, you are asked to enter your django username and password.

5. Access http://127.0.0.1/mdict locally

6. Set up wsl auto-start script

Run shell:startup on Windows to create ubuntu.vbs with the following content:


```
Set ws = CreateObject("Wscript.Shell")
ws.run "wsl -d ubuntu -u root /etc/init.d/apache2 start", vbhid
```

Among them, ubuntu is the name of the distribution version. Use the command wsl -list to view the specific name.

7. apache common commands


```
Start apache:
sudo service apache2 start
Restart apache:
sudo service apache2 restart
Stop apache:
sudo service apache2 stop
```

The location of the apache error log on ubuntu is /var/log/apache2/error.log

### Delete duplicate dictionaries records in database

1. Run django shell


```
python manage.py shell
```

2. Run the following code to delete dictionaries with duplicate dictionary file names in the db.sqlite3 database


```
from mdict.models import MdictDic
all_dics = MdictDic.objects.all()
temp_dics = {}
for dic in all_dics:
    if dic.mdict_file in temp_dics.keys():
        dic.delete()
    else:
        temp_dics.update({dic.mdict_file: None})
```

### Greate docker image on windows

1. Install docker and run

2. Delete the .git and deprecated folders in the root directory

3. Run the following command in wsl to convert the format (or manually convert the format with notepad++)


```
sudo apt-get update
sudo apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh init_server_brew.sh init_server_yum.sh init_server_apt.sh django-mdict.conf run_server.sh run_server_brew.sh run_server_yum.sh run_server_apt.sh mdict/readlib/pyx/build.sh
```

5. Run the following command in wsl to generate the database file db.sqlite3 and set the username and password


```
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py makemigrations mdict
python3 manage.py migrate mdict
python3 manage.py makemigrations mynav
python3 manage.py migrate mynav
python3 manage.py createsuperuser
```

6. Run the following command to compile


```
docker compose build --progress=plain
```

### Running on QNAP with docker

1. Open container station/create, search your upload image and install.

2. Container settings:

Fill in the following commands for the command settings. 18000 can be replaced with another port, and the entry point setting is left blank.


```
python3 manage.py runserver 0.0.0.0:18000 --noreload
```

Advanced Settings/Network: Select host for network mode

Advanced Settings/Shared Folders:

Click the first Add: fill in dmdict for the new storage space and /code for the mount path.

Click the second Add: Mount local shared folder, select the path where the dictionary is located, and fill in /code/media/mdict/doc for the mounting path.

Click Create

3. Other devices access nas ip:port

