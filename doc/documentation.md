## 说明文档

- [说明文档](#说明文档)
  * [适用情景](#适用情景)
  * [PWA支持](#PWA支持)
  * [格式支持](#格式支持)
  * [不支持](#不支持)
  * [admin操作](#admin操作)
  * [依赖](#依赖)
  * [mdict解析](#mdict解析)
  * [内置词典](#内置词典)
  * [原形推测和拼写检查](#原形推测和拼写检查)
  * [拆字反查](#拆字反查)
  * [部件检索和全宋体](#部件检索和全宋体)
  * [繁简转化和全角转化](#繁简转化和全角转化)
  * [同名加载](#同名加载)
  * [查询历史](#查询历史)
  * [全文搜索](#全文搜索)
  * [划词](#划词)
  * [修改词典库地址](#修改词典库地址)
  * [缩放](#缩放)
  * [设置](#设置)
  * [配置文件](#配置文件)
  * [在windows上运行测试服务器](#在windows上运行测试服务器)
  * [在wsl上运行测试服务器](#在wsl上运行测试服务器)
  * [部署到wsl apache](#部署到wsl-apache)
  * [更新](#更新)
  * [可能的问题](#可能的问题)

### 适用情景

局域网内，将django-mdict部署在服务器上，其他电脑、平板、手机可只保留少量词典，当离开局域网时，查询本地词典，当进入局域网时，可通过浏览器对全部词典进行查词。

1. 不建议使用移动硬盘，移动硬盘会休眠，休眠唤醒耗时长。
2. 不建议使用树莓派，cpu性能低，只能部署少量词典。
3. 不建议使用云服务器，学生机cpu性能和网络传输速度不满足要求。

### PWA支持

在本地浏览器上打开时，点击主页面、查询页面或者全文搜索页面地址栏上的安装按钮，可以安装为PWA应用，默认打开页面是查询页面。
1：如果django-mdict页面没有设置为主页或收藏，需要手动输入url打开页面，安装为PWA后只需要点击图标打开。
2：安装为PWA后窗口没有地址栏。

在安卓chrome浏览器上，PWA安装需要https支持，否则只能选择添加到主屏幕，和普通网页添加到主屏幕相比，没有地址栏。

### 格式支持

仅测试最新版chrome、firefox、edge浏览器。

音频：
* mp3,spx,ogg 支持
* wav chrome支持，firefox不支持

图像：
* png,jpg,svg,webp,tiff 支持

字体：
* chrome不支持大于30MB的字体

图片词典建议使用双栏版，因为手机浏览器可以双指缩放，双栏版不影响阅读，使用单栏版，在手机浏览器上正常显示，在电脑浏览器上会特别细长。

### 不支持

1. 不支持词头未排序的词典。

2. 不支持mdxbuilder4.0制作的词典。

3. 不支持IE浏览器。

### admin操作

进入后台admin界面

[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

* MDICT/Mdict词典：
<br />不需要手动添加词典。仅用于修改词典名，词典排序，是否启用词典。

* MDICT/内置词条：
<br />添加内置词典的词条，支持图片和富文本，支持LaTex公式。

* LaTex公式插入：
<br />方法1.单击latex公式按钮(求和符号的按钮)插入公式；
<br />方法2.手动输入，将公式用$包裹。

* 自定义命令：
<br />[link]要跳转的词条名[/link]
<br />[wrap]要折叠的内容[/wrap]
<br />自定义命令插入：
<br />1.选中文字，单击L按钮，自动将文字用[link]包裹，选中的文字显示为entry词条跳转。
<br />2.选中文字，单击W按钮，自动将文字用[wrap]包裹，选中的文字被折叠。

* MDICT/在线词典：
<br />添加在线词典，将url中要查询的字符用%WORD%替换，有些网站不支持在iframe中显示，此时需要去掉在iframe中打开的勾选。

* MDICT/标签
<br />创建标签，标签用于内置词条。

* MDICT/词典分组
<br />创建词典分组，然后将词典加入分组。

* 启用/停用所有词典
<br />Mdict词典页面，勾选ID前的复选框，选择第一页所有的词典，点击执行按钮右边的选中所有的XXX个Mdict词典，选择动作下拉框中的EnableAllDics/DisableAllDics，最后点击执行按钮。
### 依赖

1. requirements1.txt：必需依赖

django版本需要不小于3.0

2. requirements2.txt：python-lzo在windows下需要手动安装

[https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo)

python 版本3.7就选cp37，python是32位选择win32，是64位选择win_amd64。

注意32位、64位指的是python的位数，不是系统的位数，比如你是64位系统，但安装
了32位python，那么应该安装32位的库。

比如下载了python_lzo-1.12-cp37-cp37m-win_amd64.whl，在当前目录运行以下命令安装

```
python -m pip install python_lzo-1.12-cp37-cp37m-win_amd64.whl
```

3. requirements3.txt：划词工具的依赖

划词工具仅用于windows，由于cefpython3暂不支持python3.8，建议安装python3.7。

### mdict解析

bitbucket mdict-analysis：[https://bitbucket.org/xwang/mdict-analysis](https://bitbucket.org/xwang/mdict-analysis)

github mdict-analysis：[https://github.com/csarron/mdict-analysis/blob/master/readmdict.py](https://github.com/csarron/mdict-analysis/blob/master/readmdict.py)

/django-mdict/mdict/readmdict/source/readmdict_py3.zip/readmdict_py3.py对readmdict.py进行了修改

1. 源代码136行，增加compress == b'\x00\x00\x00\x00'的情况。

2. 源代码485行和593行，将len(record_block)改为decompressed_size，避免某些词典解压错误。

3. 源代码634行，修改tkinter的导入，使脚本能在python3下运行。

/django-mdict/mdict/readmdict/source/readmdict_search.py功能是对mdict进行查找。

/django-mdict/mdict/readmdict/pyx/readmdict_search.pyx是readmdict_seach.py的cython版本，运行build.bat或build.sh进行编译，编译后的库文件会复制到/django-mdict/mdict/readmdict/lib/。

### 内置词典

内置词典通过后台admin添加词条，支持LaTex公式（MathJax），支持富文本和插入图片（django-ckeditor），支持导出为mdict格式的txt，由于目前词典软件不支持MathJax，因此导出txt时不会导出MathJax。

命令：

[link]abc[/link]

创建一个跳转到abc词条的连接

[wrap]内容[/wrap]

包裹的内容会被折叠，需要点击展开。

导出内置词典：

```
python export_builtin_dic.py
```

内置词典导出到/django-mdict/export/，export.txt是导出的文本，data是导出的资源，导出后不支持mathjax，wrap脚本goldendict支持，mdict不支持。

### 原形推测和拼写检查

原形推测用的是nltk模块的WordNetLemmatizer

拼写检查用的是spellchecker模块

### 拆字反查

github hanzi_chaizi：[https://github.com/howl-anderson/hanzi_chaizi](https://github.com/howl-anderson/hanzi_chaizi)

github chaizi：[https://github.com/kfcd/chaizi](https://github.com/kfcd/chaizi)

开放词典网拆字字典：[http://kaifangcidian.com/han/chaizi](http://kaifangcidian.com/han/chaizi)

/django-mdict/mdict/mdict_utils/chaizi_reverse.py对chaizi.py进行修改，使其可以进行反查。比如输入山鳥，得到嶋和嶌。

拆字反查仅支持常用字，查询功能集成了拆字反查，查询山鸟，会返回山鸟、嶋、嶌，查询王八，会返回王八、兲、玐。

### 部件检索和全宋体

WFG博客：[https://fgwang.blogspot.com/](https://fgwang.blogspot.com/)

pdawiki部件检索和全宋体：[https://www.pdawiki.com/forum/forum.php?mod=viewthread&tid=23133&highlight=%E9%83%A8%E4%BB%B6%E6%A3%80%E7%B4%A2](https://www.pdawiki.com/forum/forum.php?mod=viewthread&tid=23133&highlight=%E9%83%A8%E4%BB%B6%E6%A3%80%E7%B4%A2)

集成了部件检索和全宋体，由于chrome不支持大于30MB的字体，因此将FSung-2.ttf拆成FSung-2-1.ttf和FSung-2-2.ttf。

建议部署到apache，并设置浏览器文件缓存时长（expires_module模块），这样只有第一次需要下载字体，全宋体大小95.5MB。

部件检索相比于拆字反查更准确，比如输入山鸟，得到嶋、嶌和㠀。

部件检索生僻字基本包含，极少部分废弃字不包含，比如左山右鸟（简体鸟），该字在中华字海山部5画441页可查，是嶋的类推简化字。

### 繁简转化和全角转化

繁简转化用的是opencc-python-reimplemented

部分pdf复制的字符是全角字符，查询时会全角查询一遍，转化为半角再查询一遍。

日文平假名和片假名自动转换，半角平假名会转换为全角片假名。

### 同名加载

mdx同名的js、css和字体文件会自动加载。

### 查询历史

查询历史存储在根目录下的history.dat文件中，第一列是时间，第二列是查询的词条。

点击设置中下载查询历史按钮，会生成csv格式的文件。注意excel直接打开可能会乱码，需要先用notepad++或其他工具将编码格式改为utf-8 with BOM。

在mdict/wordcloud/下查看查询历史生成的词云，可以在右上角设置中选择时间范围。

删除保存的查询历史，直接删除根目录下所有history.data开头的文件。

### 全文搜索

[全文搜索](essearch.md)

### 划词

划词工具仅适用于windows，使用cefpython3，python版本最高支持为3.7。

1. 安装依赖。

```
pip install -r requirements3.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

2. 将/django-mdict/huaci/huaci.pyw发送到桌面快捷方式。

3. 双击运行，右下角出现托盘图标。

4. 默认url是http://127.0.0.1:8000/mdict/?query=%WORD%，在huaci/utils/huaci.ini中修改url。

如果查词结果是空白，查看huaci/utils/huaci.ini中的ip和端口是否正确。

5. 选择文字，按ctrl+c+c快捷键开始查询。

6. 在托盘图标上右键退出，关闭划词工具。

如果需要用OCR查词，需要安装tesseract。

1. 下载安装tesseract-OCR.exe，并将tesseract.exe的路径添加到系统的环境变量Path中。

2. 添加tesseract训练数据

[https://tesseract-ocr.github.io/tessdoc/Data-Files.html](https://tesseract-ocr.github.io/tessdoc/Data-Files.html)

3. 打开划词工具的设置界面，选择OCR查词。按ctrl+c+c，鼠标点击两次，框选OCR的范围。

如果划词工具显示混乱，尝试删除huaci/huaci.cache缓存文件夹。

页面缩放比例，设置huaci/utils/huaci.ini中auto_zooming，-1.0是75%;0.0是100%;1.0是125%;2.0是150%。

### 修改词典库地址

1. 重新运行init_mdict_path.py，选择路径。

2. 或者手动修改mdict_path.json的路径，样式如下，mdict_path是词典库路径，audio_path是发音库路径。

第一个含有mdx的路径会被设置为词典库路径，第一个含有mdd的路径会被设置为发音库路径。

如果mdict_path.json为空，词典库地址设置为/django-mdict/media/mdict/doc/，发音库地址设置为/django-mdict/media/mdict/audio/。

windows下的d盘在wsl下为/mnt/d/。 注意输入规范的路径，用双引号并且用反斜杠或者双斜杠作为路径分隔符。

```
{
    "mdict_path": [
        "D:/media/mdict/doc",
        "/mnt/d/media/mdict/doc"
    ],
    "audio_path": [
        "D:/media/mdict/audio",
        "/mnt/d/media/mdict/audio"
    ]
}
```

### 缩放

整个页面的缩放，使用浏览器的缩放进行设置。

文字的缩放，使用下面按钮栏放大字号和缩小字号按钮。

图片的缩放，在手机上直接双指缩放，在电脑上在图片右键，在新标签页中打开图像，然后再进行缩放。

### 设置

* 键盘的enter键绑定查询按钮，上下方向键绑定展开上一词条和展开下一词条按钮。

* 强制刷新：后台会缓存最近查询过的内容，调试时为了显示查询结果的变化，需要开启强制刷新。

* entry链接打开新标签页：默认点击entry://连接会在当前页面查询，勾选本项后，会打开新标签页进行查询，下一次查询生效。

* 强制使用全宋体：强制将所有iframe的字体改为全宋体，下一次查询生效。

* 同时展开多个词典：默认只会展开一个词典，开启后允许同时展开多个词典，但此时跳转上一个和下一个词条的按钮失效。

* 启用文字选择菜单：启用该功能后，在词典中选择文字后，会弹出菜单，有三个功能，复制，在当前页面查询选择的词，打开新标签页查询选择的词。

* 在线词典：在线词典在后台admin添加，将url中查询的词改为%WORD%，有两种模式，在iframe中打开或在新标签页中打开（某些网站不支持在iframe中显示）。

* 保存为默认值：如果没有保存为默认值，则页面刷新后，设置恢复默认。

* 文字转简体和文字转繁体按钮，将当前展开的词条内容进行繁简转化。已知问题：由于使用直接替换转化，结果不准确且有未转化的字。

* 夜间模式和日间模式按钮，切换夜间样式和原本样式。已知问题：M-W Visual Dictionary词典折叠展开操作在夜间模式下无效，因为其对class进行全匹配判断。

### 配置文件

/django-mdict/config.ini

cache_num 查询提示缓存数目

search_cache_num 查询缓存数目

builtin_dic_enable 启用内置词典

merge_entry_max_length 默认值1000，同名词条合并，同一词典有多个查询结果时，长度小于1000的词条会被合并。如果完全不合并，设置为0。

st_enable 启用繁简转化

chaizi_enable 启用拆字反查

fh_char_enable 启用全角字符转换

kana_enable 启用假名转换

force_refresh 启用强制刷新，启用后会重新查询，而不是从缓存中读取。

select_btn_enable 启用文字选择菜单

disable_iframe_click 屏蔽iframe中的默认点击事件，关闭词典的自动发音和解决点击发重音的问题。但可能带来其他的问题，比如在低版本浏览器内核中可能导致页面空白。
重新查询后生效。

suggestion_num 查询提示数目

link_new_label entry链接打开新标签页

force_font 强制使用全宋体

card_show 同时展开多个词典

### 在windows上运行测试服务器

1. 安装python3。

2. 安装Visual Studio（同时安装C++开发组件），或者安装Microsoft C++ Build Tools（安装时勾选C++开发组件）。

在安装nltk、python-Levenshtein等库以及进行cython编译时需要C++开发组件。

Visual Studio地址：

[https://visualstudio.microsoft.com/downloads/](https://visualstudio.microsoft.com/downloads/)

Microsoft C++ Build Tools地址：

[https://visualstudio.microsoft.com/visual-cpp-build-tools/
](https://visualstudio.microsoft.com/visual-cpp-build-tools/
)

3. 安装python-lzo

[https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo)

python版本3.7就选cp37，python是32位选择win32，是64位选择win_amd64。

比如下载了python_lzo-1.12-cp37-cp37m-win_amd64.whl，在当前目录运行以下命令安装

```
pip install python_lzo-1.12-cp37-cp37m-win_amd64.whl
```

4. 下载django-mdict

```
git clone https://github.com/jiangnianshun/django-mdict.git
```

Windows下双击运行run_server.bat，第一次运行会进行初始化（安装依赖，cython编译）。

初始化过程中首先会弹出文件夹选择框，第一次选择字典库路径，第二次选择发音库路径（没有就跳过）。

路径信息保存在mdict_path.json文件中。

最后要求设置django的用户名和密码。

5. django服务器默认端口8000
<br />本地电脑访问http://127.0.0.1:8000/mdict/
<br />其他设备访问http://本机ip:8000/mdict/
<br />可能需要设置防火墙入站链接，开放8000端口。

### 在wsl上运行测试服务器

windows下django无法调用多进程，建议部署到wsl，建议使用wsl1。

1. 安装wsl，系统ubuntu，建议使用18.04。

[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

2. 切换到root用户，django需要安装到root用户下。

```
su root
```
3. cd到django-mdict目录，运行下列命令，转换脚本格式。

```
apt-get update
apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh django-mdict.conf run_server.sh mdict/readmdict/pyx/build.sh
```

4. 运行run_server.sh，默认端口8000，该脚本仅适用于ubuntu，不适用于centos。

```
bash run_server.sh
```

第一次运行会进行初始化。

首先要求从命令行输入词典库路径和发音库路径，没有就跳过。

最后要求输入django用户名和密码。

5. 本机访问http://127.0.0.1:8000/mdict

已知问题：在ubuntu20.04下，由于多进程的原因，run_server.sh运行过程中，migrate等命令无法自动结束，需要手动ctrl+c结束，在ubuntu18.04下正常。

### 部署到wsl apache

windows下django无法调用多进程，建议部署到wsl，建议使用wsl1。

1. 安装wsl，系统ubuntu，建议使用18.04。

[https://docs.microsoft.com/en-us/windows/wsl/install-win10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

2. 切换到root用户，django需要安装到root用户下。

```
su root
```
3. cd到django-mdict目录，运行下列命令，转换脚本格式。

```
apt-get update
apt-get install dos2unix
dos2unix init_wsl.sh init_server.sh django-mdict.conf run_server.sh mdict/readmdict/pyx/build.sh
```

4. 运行init_wsl.sh，默认端口80，该脚本仅适用于ubuntu，不适用于centos。

```
bash init_wsl.sh
```

首先要求从命令行输入词典库路径和发音库路径，没有就跳过。

最后要求输入django用户名和密码。

5. 本机访问http://127.0.0.1/mdict

6. 设置wsl自启动脚本

windows下运行shell:startup，建立脚本文件ubuntu.vbs，内容为

```
Set ws = CreateObject("Wscript.Shell")
ws.run "wsl -d ubuntu -u root /etc/init.d/apache2 start", vbhid
```

其中ubuntu是发行版名称，具体名称用命令wsl -list来查看。

### 更新

* 如果不需要保存旧数据，重新git clone，注意可能要清除浏览器缓存（不需要清cookie）。

* 如果需要保存旧数据，运行git pull更新项目

```
git pull
```

如果有js和css的修改，可能需要清理浏览器的缓存（不需要清cookie）。

如果有pyx文件的修改，需要手动运行build.bat或build.sh编译pyx文件。

如果requirements1.text中有新增的依赖，需要安装依赖。

```
pip install -r requirements1.txt
```

如果有模型改动(models.py)，旧数据库可能无法正常使用，尝试运行

```
python manage.py makemigrations mdict
python manage.py migrate mdict
```

linux下是

```
python3 manage.py makemigrations mdict
python3 manage.py migrate mdict
```

如果仍然无法恢复正常，可尝试手动导入。

1. 将旧的db.sqlite3改名。
   
2. 删除mdict_path.json，重新运行run_server.bat或run_server.sh，词典库路径留空，生成新的数据库。

3. 删除mdict文件夹下的migrations和__pycache__。
   
4. 用软件导出所有mdict开头的数据表，再导入到新的数据库中。

以DB browser for SQLite软件为例，打开旧数据库，选择菜单文件/导出/导出数据库到SQL文件，选择所有mdict开头的表，勾选在insert into语句中保留列名，然后导出。

如果第2步没有删除mdict_path.json，导致新的数据库又导入了词典信息，那么这里应当手动将新数据库中mdict_mdictdic数据表中的记录都清空。

打开新数据库，导入刚才的sql文件，是否创建新数据库选择no，导入完成后保存数据库。

### 可能的问题

1. 加入新的词典没有显示

重启django-mdict，只有启动时才会检查文件夹变动。

2. 部署在wsl上，前端的js、css等无法更新。

因为django-mdict.conf里设置了expires_module，使得浏览器长期缓存文件，手动删除浏览器的缓存文件（不需要清cookie）。

3. 显示\[INIT_UTILS WARNING\] loading readmdict_search lib failed! run /mdict/readmdict/pyx/build.sh or build.bat, this will speed up search.

出现该提示说明没有进行cython编译。

windows下运行/django-mdict/mdict/readmdict/pyx/build.bat，linux下运行/django-mdict/mdict/readmdict/pyx/build.sh。

这将对readmdict_search.py进行编译，编译后的pyd或so运行库在/django-mdict/mdict/readmdict/lib/下，编译后相比于没有编译，速度提升约1/3。

4. 403错误

权限问题，设置django-mdict文件夹及子文件的权限。

5. Failed to enable APR_TCP_DEFER_ACCEPT

```
sudo vim /etc/apache2/apache2.conf
```

在文件末尾加入

```
AcceptFilter http none
```

6. sleep: cannot read realtime clock: Invalid argument

```
sudo mv /bin/sleep /bin/sleep~
touch /bin/sleep
chmod +x /bin/sleep
```

7. apache在ubuntu20.04下restart和stop失败

多进程的问题，多重复几次。

8. 保存数据时报错attempt to write a readonly database

修改db.sqlite3的权限。

9. 内置词条存在，但是无法查询到。

尝试将该词条重新保存。
