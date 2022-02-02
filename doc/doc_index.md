## 说明文档

- [说明文档](#说明文档)
  * [PWA支持](#PWA支持)
  * [格式支持](#格式支持)
  * [不支持](#不支持)
  * [常用操作](#常用操作)
  * [依赖](#依赖)
  * [admin操作和内置词典](#admin操作和内置词典)
  * [功能实现](#功能实现)
  * [全文搜索](#全文搜索)
  * [anki制卡](#anki制卡)
  * [划词](#划词)
  * [设置](#设置)
  * [运行](#运行)
  * [更新](#更新)
  * [可能的问题](#可能的问题)

### PWA支持

在本机浏览器上打开时，点击主页面、查询页面或者全文搜索页面地址栏上的安装按钮，可以安装为PWA应用，默认打开页面是查询页面。
1：如果django-mdict页面没有设置为主页，需要手动输入url打开页面，安装为PWA后只需要点击图标打开。
2：安装为PWA后窗口没有地址栏。

在非本机浏览器上，PWA安装需要https支持。比如安卓chrome浏览器上，在http下只能选择添加到主屏幕，和普通网页添加到主屏幕相比，没有地址栏。

### 格式支持

仅测试最新版chrome、firefox、edge浏览器。

词典：支持mdx,mdd和zim

音频：
* mp3,spx,ogg 支持
* wav chrome支持，firefox不支持

图像：
* png,jpg,svg,webp,tiff 支持
* swf 不支持

字体：
* chrome不支持大于30MB的字体

图片词典建议使用整页版或切图版，因为手机浏览器可以双指缩放，整页版影响较小，而使用单栏版，在手机浏览器上正常显示，在电脑浏览器上页面特别长。

### 不支持

1. 不支持词头未排序的词典，会查询不到正确结果。

2. 不支持mdxbuilder4.0制作的词典。

3. 不支持IE浏览器。

4. 不支持mdx文件名重复，只会载入重名mdx的其中一个。

5. 正查不支持模糊查找。

6. 目前不支持通配符查找和正则查找。

### 常用操作

[常用操作图文说明](doc/doc_op.md)

#### 修改词典库路径

1. 重新运行init_mdict_path.py，选择路径，新选择的路径将插入到最前面。

2. 或者手动修改mdict_path.json的路径，格式如下，mdict_path是词典库路径，audio_path是发音库路径。

第一个含有mdx的路径会被设置为词典库路径，第一个含有mdd的路径会被设置为发音库路径。

如果mdict_path.json为空，词典库地址设置为django-mdict/media/mdict/doc/，发音库地址设置为/django-mdict/media/mdict/audio/。

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

#### 内容缩放

缩放页面：使用浏览器的缩放设置，手机浏览器双指缩放。

缩放文字：使用底部按钮栏放大字号和缩小字号按钮。

缩放图片：

1. 手机浏览器直接双指缩放。
2. 电脑浏览器打开启用放大镜按钮（下一次查询生效）。
3. 电脑浏览器图片右键，在新标签页中打开图像。

#### 页内查询

无页内查询功能，只能使用浏览器自带的ctrl+F搜索展开的词条。

#### 同名词条合并

修改配置文件django-mdict/config.ini中的merge_entry_max_length项。

默认值为1000，当同一词典对同一个查询有多个查询结果时，长度（字符串的长度，包含html标签）小于1000的词条会被合并显示。如果需要完全不合并，设置为0。

#### 修改服务器端口

测试服务器修改启动脚本（run_server.bat,run_server_no_check.bat,run_server.sh,run_server_no_check.sh）中的0.0.0.0:8000。

apache修改配置文件django-mdict.conf中的VirtualHost *:80。

#### 初始化

运行run_server脚本时，仅当根目录下数据库db.sqlite3不存在时，才会进行初始化，db.sqlite3存在的情况下，直接启动django服务器。

#### 减小体积

为了减小体积，以下内容可删除。

.git/ 删除后无法操作git

huaci/ 删除后无法使用划词脚本

media/font/ 删除后无法显示全宋体

mdict/readlib/pyx/build/ cython编译生成的中间文件

mdict/readlib/pyx/mdict/ cython编译生成的中间文件

#### 查词API

1. 使用GET方法获取查词的json结果

url是[http://IP地址/api/mdict2/mdict/]()，参数是query:apple,page:1

2. 使用url获取查词的json结果

访问[http://IP地址/api/mdict2/mdict/?query=apple&page=2&format=json]()

#### 切换主页

在config.ini中修改index_id的值（1或2），主页2背景图位于/static/img/background.jpg。

### 依赖

默认用的是清华源，如果需要修改，修改init_server.bat和init_server.sh中pip命令的-i参数。

1. requirements1.txt：必需依赖

django版本需要3.0以上或者4.0

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

### admin操作和内置词典

[admin操作](doc_admin.md)

### 功能实现

[功能实现](doc_func.md)

### 全文搜索

[全文搜索](doc_es.md)

### anki制卡

[anki](doc_anki.md)

### 划词脚本

[划词](doc_huaci.md)

### 设置

[设置](doc_config.md)

### 运行

[运行](doc_deploy.md)

### 更新

[更新](doc_update.md)

### 可能的问题

[可能的问题](doc_question.md)
