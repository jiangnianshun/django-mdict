## django-mdict

### Introduction

django-mdict is a mdict dictionary query tool implemented by django (supports mdx and zim formats).

It is a supplement to the LAN online query function. Priority is using official software, such as goldendict, mdict, eudic, dicttango, etc.

### Running on windows

1. Install python3.

2. (Can be skipped) Install Visual Studio (also install C++ development component), or install Microsoft C++ Build Tools (check the C++ development component during installation).

A C++ compiler is required for cython compilation. Cython can slightly improve query speed.

[Visual Studio](https://visualstudio.microsoft.com/downloads/)

[Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/
)

3. (Can be skipped) Install python-lzo. python-lzo needs to be installed manually under Windows.

It is not recommended to skip. After skipping, the mdx dictionary encoded with lzo cannot be read.

[python-lzo](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo)

For Python version 3.7, choose cp37. If Python is 32-bit, choose win32. If Python is 64-bit, choose win_amd64.

For example, download python_lzo-1.12-cp37-cp37m-win_amd64.whl and run the following command in the current directory to install it.


```
python -m pip install python_lzo-1.12-cp37-cp37m-win_amd64.whl
```

4. Download django-mdict


```
git clone https://github.com/jiangnianshun/django-mdict.git --depth=1
```

Double-click run_server.bat. The first run will perform initialization (install dependencies, compile cython, and create database db.sqlite3).

During the running process, the folder selection dialog will pop up twice. The first time you select the root path of dictionaries (can be skipped), the second time you select the path of pronunciation mdd files (can be skipped).

Path information is saved in the mdict_path.json file.

Finally, you are required to enter your Django username, email, and password. Email address can be ignored.

5. Django server default port 18000
<br>Default local URL is [http://127.0.0.1:18000/mdict/](http://127.0.0.1:18000/mdict/)
<br>May need to Set up the firewall inbound link and open port 18000.

6. After completing the initialization, just run run_server_no_check.bat to start each time.
   
### Notice

1. Make sure the folder name is django-mdict and not django-mdict-master or another name to ensure the script runs correctly.

2. Make sure that the current user has permissions for folder django-mdict and all sub-files. On Ubuntu, use chmod -R 777 django-mdict. On Windows, right-click on the django-mdict folder, add the local account in Properties/Security and set permissions. for complete control.

3. It is not recommended to use pypy, sometimes the query is fast, sometimes it is slower.

4. Under Linux, the script format may need to be converted to run properly.


```
sudo apt-get update
sudo apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh init_server_brew.sh init_server_yum.sh init_server_apt.sh django-mdict.conf run_server.sh run_server_brew.sh run_server_yum.sh run_server_apt.sh mdict/readlib/pyx/build.sh
```

6. Program update may need to manually clear the browser cache (no cookies required), delete the .cache folder in the root directory, and re-run the run_server.bat or run_server.sh script. For PWA, it needs to be deleted and re-installed.

7. The local browser can open the url, but other devices under same LAN cannot. Check whether port 18000 is open for the inbound connection of the firewall, and check whether the current network is a private network rather than a public network, and check whether the device is connected to the same LAN.

### Documentation

[Sources](doc/doc_en/doc_func.md)

[Documentation](doc/doc_en/doc_index.md)

[Running](doc/doc_en/doc_deploy.md)

[Update](doc/doc_en/doc_update.md)

[Style](doc/doc_style.md)

[Known issues](doc/doc_en/doc_question.md)

### Related Projects

[flask-mdict](https://github.com/liuyug/flask-mdict)

[SilverDict](https://github.com/Crissium/SilverDict)