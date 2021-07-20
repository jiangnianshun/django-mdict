  * [iframe显示](#iframe显示)
  * [mdict解析](#mdict解析)
  * [zim解析](#zim解析)
  * [原形推测和拼写检查](#原形推测和拼写检查)
  * [拆字反查](#拆字反查)
  * [部件检索和全宋体](#部件检索和全宋体)
  * [字符转化](#字符转化)
  * [同名加载](#同名加载)
  * [查询历史](#查询历史)
  * [其他](#其他)
  
### iframe显示

iframe-resizer：[https://github.com/davidjbradshaw/iframe-resizer](https://github.com/davidjbradshaw/iframe-resizer)

词条使用iframe显示，高度使用iframe-resizer设置。

优点：词条间完全隔离，js和css不会相互影响。

缺点：1.效率低；2.高度有时候不正确；3.部分在线网址不支持在iframe中显示。

### mdict解析

bitbucket mdict-analysis：[https://bitbucket.org/xwang/mdict-analysis](https://bitbucket.org/xwang/mdict-analysis)

github mdict-analysis：[https://github.com/csarron/mdict-analysis/blob/master/readmdict.py](https://github.com/csarron/mdict-analysis/blob/master/readmdict.py)

django-mdict/mdict/media/readmdict_py3.zip/readmdict_py3.py对readmdict.py进行了修改

1. 源代码136行，增加compress == b'\x00\x00\x00\x00'的情况。

2. 源代码485行和593行，将len(record_block)改为decompressed_size，避免某些词典解压错误。

3. 源代码634行，修改tkinter的导入，使脚本能在python3下运行。

django-mdict/mdict/readlib/src/readmdict.py功能是对mdict进行查找。

django-mdict/mdict/readlib/pyx/readmdict.pyx是readmdict_seach.py的cython版本，运行build.bat或build.sh进行编译，编译后的库文件会复制到/django-mdict/mdict/readlib/lib/。

### zim解析

ZIM file format: [https://openzim.org/wiki/ZIM_file_format](https://openzim.org/wiki/ZIM_file_format)

github ZIMply： [https://github.com/kimbauters/ZIMply](https://github.com/kimbauters/ZIMply)

django-mdict/mdict/mdict-utils/readzim.py修改自zimply.py。

正查会有部分词条无法查询到，需要用全文搜索。全文搜索需要安装xapian，windows下需要手动编译。
django-mdict运行后会抽取zim的内置索引保存为idx文件，抽取索引类似文件复制，速度取决于硬盘的最大读写速度。

kiwix（官方阅读器）下载地址：
[https://www.kiwix.org/download/](https://www.kiwix.org/download/)

phet.zim以及wikisource.zim中部分竖排古文的高度无法确定，需要开启固定高度才能正常显示。

zim是离线维基格式：

wikipedia-维基百科
wikibooks-维基教科书
wiktionary-维基词典
wikinews-维基新闻
wikiquote-维基语录
wikisource-维基文库
wikivoyage-维基导游
wikiversity-维基学院
wikispecies-维基物种
gutenberg-古登堡计划
phet-互动仿真程序的离线网页
vikida-面向儿童的百科
stackexchange-问答网站stackexchange的离线网页

zim下载地址：
[https://wiki.kiwix.org/wiki/Content_in_all_languages](https://wiki.kiwix.org/wiki/Content_in_all_languages)

### 原形推测和拼写检查

原形推测用的是nltk模块的WordNetLemmatizer

拼写检查用的是spellchecker模块

### 拆字反查

github hanzi_chaizi：[https://github.com/howl-anderson/hanzi_chaizi](https://github.com/howl-anderson/hanzi_chaizi)

github chaizi：[https://github.com/kfcd/chaizi](https://github.com/kfcd/chaizi)

开放词典网拆字字典：[http://kaifangcidian.com/han/chaizi](http://kaifangcidian.com/han/chaizi)

django-mdict/mdict/mdict_utils/chaizi_reverse.py对chaizi.py进行修改，使其可以进行反查。比如输入山鳥，得到嶋和嶌。

拆字反查仅支持常用字，查询功能集成了拆字反查，查询山鸟，会返回山鸟、嶋、嶌，查询王八，会返回王八、兲、玐。

### 部件检索和全宋体

WFG博客：[https://fgwang.blogspot.com/](https://fgwang.blogspot.com/)

pdawiki部件检索和全宋体：[https://www.pdawiki.com/forum/forum.php?mod=viewthread&tid=23133&highlight=%E9%83%A8%E4%BB%B6%E6%A3%80%E7%B4%A2](https://www.pdawiki.com/forum/forum.php?mod=viewthread&tid=23133&highlight=%E9%83%A8%E4%BB%B6%E6%A3%80%E7%B4%A2)

集成了部件检索和全宋体，由于chrome不支持大于30MB的字体，因此将FSung-2.ttf和FSung-F.ttf进行了拆分。

建议部署到apache，并设置浏览器文件缓存时长（expires_module模块），这样只有第一次需要下载字体，全宋体大小126MB。

部件检索相比于拆字反查更准确，比如输入山鸟，得到嶋、嶌和㠀。

部件检索目前包含155070个汉字。

### 字符转化

繁简转化用的是opencc-python-reimplemented

部分pdf复制的字符是全角字符，查询时会全角查询一遍，转化为半角再查询一遍。

日文平假名和片假名自动转换，半角片假名会转换为全角片假名。

日文假名和罗马音转化使用python-romkan实现。

python-romkan：[https://github.com/soimort/python-romkan](https://github.com/soimort/python-romkan)

### 同名加载

mdx同名的js、css和字体文件会自动加载。

### 查询历史

默认不会保存查询历史，需要修改config.ini中的history_enable为True才会保存查询历史。

查询历史存储在根目录下的history.dat文件中，第一列是时间，第二列是查询的词条。

点击设置中下载查询历史按钮，会生成csv格式的文件。注意excel直接打开可能会乱码，需要先用notepad++或其他工具将编码格式改为utf-8 with BOM。

在mdict/wordcloud/下查看查询历史生成的词云，可以在右上角设置中选择时间范围。

关闭保存查询历史，修改config.ini中的history_enable为False，然后重启django-mdict。

删除保存的查询历史，直接删除根目录下所有history开头的dat文件。

### 其他

内置词条使用django-ckeditor和MathJax实现富文本和latex公式输入。

django-ckeditor：[https://github.com/django-ckeditor/django-ckeditor](https://github.com/django-ckeditor/django-ckeditor)

MathJax：[https://github.com/mathjax/MathJax](https://github.com/mathjax/MathJax)

查询历史词云使用wordcloud2.js实现。

wordcloud2.js：[https://github.com/timdream/wordcloud2.js](https://github.com/timdream/wordcloud2.js)

按照路径和分组显示词典使用jstree.js实现。

jstree.js：[https://www.jstree.com/](https://www.jstree.com/)

markdown文档显示使用marked.js实现。

marked.js：[https://github.com/markedjs/marked](https://github.com/markedjs/marked)