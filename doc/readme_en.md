## django-mdict

### Introduction

django-mdict is a mdict search tool based on Django.

online demo：[http://81.68.207.87/mdict/](http://81.68.207.87/mdict/)

### run on Windows

1. install python3。

2. (can skip) install Visual Studio (including C++ development components), or install Microsoft C++ Build Tools (including C++ development components).

Visual Studio：

[https://visualstudio.microsoft.com/downloads/](https://visualstudio.microsoft.com/downloads/)

Microsoft C++ Build Tools：

[https://visualstudio.microsoft.com/visual-cpp-build-tools/
](https://visualstudio.microsoft.com/visual-cpp-build-tools/
)

3. install python-lzo

[https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo)

download the module according to your system and python version, then install it.

```
python -m pip install python_lzo-1.12-cp37-cp37m-win_amd64.whl
```

4. clone django-mdict

```
git clone https://github.com/jiangnianshun/django-mdict.git --depth=1
```

4.1 then run run_server.bat

4.2 firstly, select the path to mdict, secondly, select the path to audio.

4.3 finally enter username and password

5. Django dafault port 8000
<br />local url: http://127.0.0.1:8000/mdict/
   
### Recommendation

recommend deploying to Ubuntu or wsl1 on Windows.

### Documentation

[documentation](doc_index.md)

### Style

![图片1](doc/img/structure.png?raw=true)

![图片2](doc/img/img1.jpg?raw=true)

![图片3](doc/img/img2.jpg?raw=true)

![图片4](doc/img/img3.jpg?raw=true)

