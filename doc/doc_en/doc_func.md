  * [Directory Structure](#Directory Structure)
  * [iframe display](#iframe display)
  * [mdict parsing](#mdict parsing)
  * [zim parsing](#zim parsing)
  * [Prototype guessing and spell checking](#Prototype guessing and spell checking)
  * [Split characters and search](#Split characters and search)
  * [Part retrieval and full Song font](#Part retrieval and full Song font)
  * [character conversion](#character conversion)
  * [Loading with the same name](#Loading with the same name)
  * [Query history](#Query history)
  * [Other](#Other)

### Directory Structure


```
django-mdict
├─.git
├─.cache
│  ├─.Linux.cache（cache file on linux）
│  ├─.Linux.dat（cache file on linux）
│  ├─.Windows.cache（cache file on windows）
│  └─.Windows.dat（cache file on windows）
├─base（common functions）
├─doc（markdown documentation）
├─export（database export path）
├─mdict（dictionary module）
│  ├─mdict_utils
│  ├─readlib（mdict and zim parsing）
│  │  ├─lib（cython compiled so and pyd will be copied here）
│  │  ├─pyx（pyx files and cython compiled intermediate files）
│  │  └─src（py files）
│  ├─static
│  │  └─mdict（mdict static files）
│  └─templates
│     └─mdict（mdict template files）
├─media
│  ├─char（special characters from unicode-table-data）
│  ├─font（全宋体）
│  ├─icon（navigation icons）
│  ├─nltk_data（nltk corpus）
│  └─uploads（images from built-in entrys）
├─mynav（local navigation）
│  ├─static（mynav static files）
│  └─templates（mynav template files）
├─mysite（django base settings）
├─script（service\import&export\icons download）
├─static（common static files）
├─templates（common template files）
├─.gitattributes
├─.gitignore
├─config.ini（config file）
├─db.sqlite3（database file）
├─django-mdict.conf（apache config file）
├─init_mdict_path.py（set path of dictionaries）
├─init_server.bat（initalization on windows）
├─init_server.sh（initalization on linux）
├─init_wsl.sh（initalization on linux with apache）
├─manage.py（django-mdict entry point）
├─mdict_path.json（path of dictionaries）
├─readme.md
├─requirements1.txt（dependency requirements）
├─requirements2.txt（dependency requirements）
├─run_server.bat（run django-mdict on windows）
├─run_server.sh（run run_server_apt.sh）
├─run_server_apt.sh（run django-mdict on ubuntu）
├─run_server_brew.sh（run django-mdict on macos）
├─run_server_yum.sh（run django-mdict on centos）
├─run_server.vbs（run django-mdict on windows without cmd window）
├─run_server_no_check.bat（run django-mdict on windows without initalization）
└─run_server_no_check.sh（run django-mdict on linux without initalization）
```
  
### iframe display

iframe-resizer:[https://github.com/davidjbradshaw/iframe-resizer](https://github.com/davidjbradshaw/iframe-resizer)

The entries are displayed using iframe, and the height is set by iframe-resizer.

Advantages: Entries are completely isolated, js and css will not affect each other.

Disadvantages: 1. Low efficiency; 2. The height is sometimes incorrect; 3. Some online URLs do not support display in iframes.

### mdict parsing

bitbucket mdict-analysis：[https://bitbucket.org/xwang/mdict-analysis](https://bitbucket.org/xwang/mdict-analysis)

github mdict-analysis：[https://github.com/csarron/mdict-analysis/blob/master/readmdict.py](https://github.com/csarron/mdict-analysis/blob/master/readmdict.py)

django-mdict/mdict/media/readmdict_py3.zip/readmdict_py3.py modified readmdict.py

1. Line 136 of the source code, add compress == b'\x00\x00\x00\x00'.

2. In lines 485 and 593 of the source code, change len(record_block) to decompressed_size to avoid certain dictionary decompression errors.

3. Source code line 634, modify the import of tkinter so that the script can run under python3.

The function of django-mdict/mdict/readlib/src/readmdict.py is to search mdict.

django-mdict/mdict/readlib/pyx/readmdict.pyx is the cython version of readmdict_seach.py. Run build.bat or build.sh to compile. The compiled library file will be copied to /django-mdict/mdict/readlib/lib/.

### zim parsing

ZIM file format: [https://openzim.org/wiki/ZIM_file_format](https://openzim.org/wiki/ZIM_file_format)

github ZIMply: [https://github.com/kimbauters/ZIMply](https://github.com/kimbauters/ZIMply)

django-mdict/mdict/mdict-utils/readzim.py is modified from zimply.py.

Some terms cannot be found during the current search, and full-text search is required. Full-text search requires xapian to be installed, and manual compilation is required under windows. After running django-mdict, ZIM's built-in index will be extracted and saved as an idx file. Extracting the index is similar to file copying, and the speed depends on the maximum read and write speed of the hard disk.

kiwix (official reader) download address: [https://www.kiwix.org/download/](https://www.kiwix.org/download/)

The height of some vertical ancient texts in phet.zim and wikisource.zim cannot be determined, and the fixed height needs to be turned on for normal display.

zim is an offline wiki format:

wikipedia - wikibooks - wikibooks - wikinews - wikiquote - wikisource - wikivoyage - wikiversity - wikispecies - wikispecies gutenberg - Project Gutenberg phet - offline web pages for interactive simulation programs vikida - an encyclopedia for children stackexchange - the offline page of the question and answer website stackexchange

zim download address: [https://wiki.kiwix.org/wiki/Content_in_all_languages](https://wiki.kiwix.org/wiki/Content_in_all_languages)

### Prototype guessing and spell checking

The prototype estimation uses the WordNetLemmatizer of the nltk module.

Spell checking uses the spellchecker module

### Split characters and search

github hanzi_chaizi：[https://github.com/howl-anderson/hanzi_chaizi](https://github.com/howl-anderson/hanzi_chaizi)

github chaizi：[https://github.com/kfcd/chaizi](https://github.com/kfcd/chaizi)

online dictionary: [http://kaifangcidian.com/han/chaizi](http://kaifangcidian.com/han/chaizi)

django-mdict/mdict/mdict_utils/chaizi_reverse.py modifies chaizi.py so that it can be reverse-search. 

When you search 山鸟, you will get 山鸟, 嶋 and 嶌.

### Part retrieval and full Song font

WFG Blog: [https://fgwang.blogspot.com/](https://fgwang.blogspot.com/)

pdawiki component retrieval and full Song font: [https://www.pdawiki.com/forum/forum.php?mod=viewthread&tid=23133&highlight=%E9%83%A8%E4%BB%B6%E6%A3%80%E7%B4%A2](https://www.pdawiki.com/forum/forum.php?mod=viewthread&tid=23133&highlight=%E9%83%A8%E4%BB%B6%E6%A3%80%E7%B4%A2)

Integrated component retrieval and full Song font. Since chrome does not support fonts larger than 30MB, FSung-2.ttf and FSung-F.ttf were split. The full Song font size is 138MB.

Parts retrieval is more accurate than characters splitting. For example, if you enter 山鸟, you will get 山鸟, 嶋, 嶌 and 㠀.

The parts search currently contains 173334 Chinese characters.

### character conversion

Opencc-python-reimplemented is used for traditional and simplified chinese conversion.

Some of the characters copied from the PDF are full-width characters. When querying, the characters will be queried once as full-width characters, and then queried as half-width characters.

Japanese hiragana and katakana are automatically converted, and half-width katakana will be converted to full-width katakana.

Japanese kana and romanization conversion is implemented using python-romkan.

python-romkan：[https://github.com/soimort/python-romkan](https://github.com/soimort/python-romkan)

### Loading with the same name

js, css and font files with the same name as mdx will be loaded automatically.

### Query history

Query history will not be saved by default. You need to modify history_enable in config.ini to True to save query history.

The query history is stored in the history.dat file in the root directory. The first column is the time, and the second column is the query entry.

Click the Download Query History button in the settings to generate a file in csv format (utf-8). 

The word cloud generated by query history can be viewed on mdict/wordcloud/.

Delete all history*.dat files in the root directory to delete query history.

### Other

The front-end interface uses bootstrap5 and jquery-ui

bootstrap5:[https://getbootstrap.com/](https://getbootstrap.com/)

jquery-ui：[https://github.com/jquery/jquery-ui](https://github.com/jquery/jquery-ui)

The built-in entries use django-ckeditor and MathJax to implement rich text and latex formula input.

django-ckeditor：[https://github.com/django-ckeditor/django-ckeditor](https://github.com/django-ckeditor/django-ckeditor)

MathJax:[https://github.com/mathjax/MathJax](https://github.com/mathjax/MathJax)

Keyword highlighting for full-text search is implemented using mark.js.

mark.js：[https://github.com/julmot/mark.js](https://github.com/julmot/mark.js)

Word cloud is implemented using wordcloud2.js.

wordcloud2.js：[https://github.com/timdream/wordcloud2.js](https://github.com/timdream/wordcloud2.js)

Displaying dictionaries by path and grouping is implemented using jstree.js.

jstree.js：[https://www.jstree.com/](https://www.jstree.com/)

Markdown document display is implemented using marked.js.

marked.js：[https://github.com/markedjs/marked](https://github.com/markedjs/marked)

Anki card creation is implemented by calling anki-connect.

anki-connect:[https://github.com/FooSoft/anki-connect](https://github.com/FooSoft/anki-connect)

Data for special symbols comes from unicode-table-data.

unicode-table-data：[https://github.com/unicode-table/unicode-table-data](https://github.com/unicode-table/unicode-table-data)

The picture magnifier is implemented using blowup.js.

blowup.js：[https://github.com/paulkr/blowup.js](https://github.com/paulkr/blowup.js)

The network diagram display of built-in entries is implemented using vis-network.

vis-network：[https://github.com/visjs/vis-network](https://github.com/visjs/vis-network)

Bookshelf (Style 3): [https://www.elated.com/rotatable-3d-product-boxshot-threejs/](https://www.elated.com/rotatable-3d-product-boxshot-threejs/)