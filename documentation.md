## 说明文档

- [说明文档](#说明文档)
  * [适用情景](#适用情景)
  * [格式支持](#格式支持)
  * [admin操作](#admin操作)
  * [依赖](#依赖)
  * [mdict解析](#mdict解析)
  * [内置词典](#内置词典)
  * [原形推测和拼写检查](#原形推测和拼写检查)
  * [拆字反查](#拆字反查)
  * [部件检索和全宋体](#部件检索和全宋体)
  * [繁简转化和全角转化](#繁简转化和全角转化)
  * [同名加载](#同名加载)
  * [划词](#划词)
  * [修改词典库地址](#修改词典库地址)
  * [设置](#设置)
  * [配置文件](#配置文件)
  * [在windows上运行测试服务器](#在windows上运行测试服务器)
  * [在wsl上运行测试服务器](#在wsl上运行测试服务器)
  * [部署到wsl apache](#部署到wsl-apache)
  * [可能的问题](#可能的问题)

### 适用情景

局域网内，将django-mdict部署在服务器上，其他电脑、平板、手机可只保留少量词典，当离开局域网时，查询本地词典，当进入局域网时，可通过浏览器对全部词典进行查词。

1. 不建议使用移动硬盘，移动硬盘会休眠，休眠唤醒耗时长。
2. 不建议使用树莓派，cpu性能低，只能部署少量词典。
3. 不建议使用云服务器，学生机cpu性能和网络传输速度不满足要求。

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

### admin操作

进入后台admin界面

[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

* MDICT/Mdict词典：
<br />修改词典名，词典排序，是否启用词典。

* MDICT/内置词条：
<br />添加内置词典的词条，支持图片和富文本，支持LaTex公式（公式用$符号包裹）。
<br />支持两个自定义命令
<br />[link]要跳转的词条名[/link]
<br />[wrap]要折叠的内容[/wrap]

* MDICT/在线词典：
<br />添加在线词典，将要查询的字符用%WORD%替换，有些网站不支持在iframe中显示，此时需要去掉在iframe中打开的勾选。

* MDICT/标签
<br />创建标签，标签用于内置词条。

* MDICT/词典分组
<br />创建词典分组，创建分组后去MDICT/Mdict词典中将词典加入某个分组。

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
pip install python_lzo-1.12-cp37-cp37m-win_amd64.whl
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

### 同名加载

mdx同名的js、css和字体文件会自动加载。

### 划词

划词工具使用tesseract和cefpython3，通过鼠标点击对屏幕截图并进行OCR查询，仅用于windows。

1. 下载安装tesseract-OCR.exe，并将tesseract.exe的路径添加到系统的环境变量Path中。

tesseract训练数据：[https://tesseract-ocr.github.io/tessdoc/Data-Files.html](https://tesseract-ocr.github.io/tessdoc/Data-Files.html)

2. 安装依赖。

```
pip install -r requirements3.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. 双击运行huaci.bat，右下角系统托盘会出现django-mdict的图标。

4. 默认是复制查词模式，选择文字后按ctrl+c+c进行查词。

要切换ocr查词，单击系统托盘图标，选择ocr切换到ocr查词模式，然后按ctrl+c+c开始划词，对鼠标两次点击之间的图像截图进行查词。

默认url是http://127.0.0.1:8000/mdict/?query=%WORD%，在huaci/huaci.ini中修改url。

也可以添加其他在线词典，将url中要查询的词的部分用%WORD%代替。

5. 关闭划词工具，系统托盘图标上右键退出。

### 修改词典库地址

修改mdict_path.json的路径，样式如下，mdict_path是词典库路径，audio_path是发音库路径。

第一个含有mdx的路径会被设置为词典库路径，第一个含有mdd的路径会被设置为发音库路径。

如果mdict_path.json为空，词典库地址设置为/django-mdict/media/mdict/doc/，发音库地址设置为/django-mdict/media/mdict/audio/。

注意输入规范的路径，用双引号并且用反斜杠或者双斜杠作为路径分隔符。

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

merge_entry_max_length 查询结果长度，同一词典查询结果长度都小于该长度时才会合并。

st_enable 启用繁简转化

chaizi_enable 启用拆字反查

fh_char_enable 启用全角字符转换

force_refresh 启用强制刷新，启用后会重新查询，而不是从缓存中读取。

select_btn_enable 启用文字选择菜单

suggestion_num 查询提示数目

link_new_label entry链接打开新标签页

force_font 强制使用全宋体

card_show 同时展开多个词典

### 在windows上运行测试服务器

1. 安装python3。

2. 安装Microsoft C++ Build Tools

在安装nltk、python-Levenshtein等库以及进行cython编译时需要该工具，安装时勾选C++开发组件。

[https://visualstudio.microsoft.com/zh-hant/visual-cpp-build-tools/
](https://visualstudio.microsoft.com/zh-hant/visual-cpp-build-tools/
)

3. 下载django-mdict

```
git clone https://github.com/jiangnianshun/django-mdict.git
```

Windows下双击运行run_server.bat，第一次运行会进行初始化（安装依赖，cython编译）。

初始化过程中首先会弹出文件夹选择框，第一次选择字典库路径，第二次选择发音库路径。（路径保存在mdict_path.json文件中）

最后要求设置django的用户名和密码。

4. django服务器默认端口8000
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

### 可能的问题

1. 加入新的词典没有显示

重启django-mdict，只有启动时才会检查文件夹变动。

2. 部署在wsl上，前端的js、css等无法更新。

因为django-mdict.conf里设置了expires_module，使得浏览器长期缓存文件，手动删除浏览器的缓存文件（不需要清cookie）。

3. 显示\[INIT_UTILS WARNING\] loading readmdict_search lib failed! run /mdict/readmdict/pyx/build.sh or build.bat, this will speed up search.

出现该提示说明没有进行cython编译。

windows下运行/django-mdict/mdict/readmdict/pyx/build.bat，linux下运行/django-mdict/mdict/readmdict/pyx/build.sh。

这将对readmdict_search.py进行编译，编译后的pyd或so运行库在/django-mdict/mdict/readmdict/lib/下，编译后相比于没有编译，速度提升约1/3。

4. 如何更新django-mdict

先clone项目

4.1 如果在内置词典中添加了词条或者想保留mdict词典的排序，那么将旧项目的db.sqlite3和mdict_path.json复制到新项目下，然后手动运行build.bat或build.sh进行cython编译

4.2 如果没有使用内置词典且不想保留mdict词典的排序，直接运行run_server.bat或run_server.sh。

5. 403错误

权限问题，设置django-mdict文件夹及子文件的权限。

6. Failed to enable APR_TCP_DEFER_ACCEPT

```
sudo vim /etc/apache2/apache2.conf
```

在文件末尾加入

```
AcceptFilter http none
```

7. sleep: cannot read realtime clock: Invalid argument

```
sudo mv /bin/sleep /bin/sleep~
touch /bin/sleep
chmod +x /bin/sleep
```

8. apache在ubuntu20.04下restart和stop失败

多进程的问题，多重复几次。

