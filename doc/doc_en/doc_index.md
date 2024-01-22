## Documentation

- [Documentation](#Documentation)
  * [Equipment testing](Equipment testing)
  * [PWA support](#PWA support)
  * [Format support](#Format support)
  * [not support](#not support)
  * [Common operations](#Common operations)
  * [Dependencies](#Dependencies)
  * [Admin operations and built-in dictionaries](#admin操作和内置词典)
  * [Full-text search](#Full-text search)
  * [ANKI](#ANKI)
  * [Settings](#Settings)

### Equipment testing

#### Equipment testing

Test dictionary library, a total of 1248 dictionaries, size (mdx+mdd+zim) 761GB.

Test equipment 1: Tencent Cloud 4-core cloud server, 50G hard drive.

The hard disk capacity and CPU performance are both insufficient and can only run about 50 dictionaries. The connection speed is sometimes fast and sometimes very slow.

Test device 2: QNAP 464C (enable solid-state cache acceleration).

When running the test dictionary database, the first query will take several hours, and subsequent queries will take between 30 seconds and 60 seconds, and the CPU will occupy 100% for each word search.

Test equipment 3: Desktop computer (CPU3900X 12 core, frequency locked at 3.8GHz), solid state drive.

When running the test dictionary, it takes about 3-4 seconds to search words.

#### Network test

Modem does not have a public IP, it has IPv6, and phone uses mobile data to access network. It is impossible to connect using QNAP DDNS. By using zerotier, the speed is about 30KB/s under IPv4, and word search is extremely slow; after the router turns on IPv6, the speed is about 2MB/s, which is the same speed under LAN.


### PWA support

When opening on the local browser, click the installing button on the address bar to install it as a PWA application. The query page is the default page. 

On non-local browsers, PWA installation requires https support. For example, on the Android Chrome browser, you can only choose to add to the home screen under http. Compared with adding ordinary web pages to the home screen, there is no address bar.

### Format support

Dictionary: mdx, mdd and zim

Audio:
* mp3,spx,ogg
* wav chrome supports it, firefox does not support it

image:
* png,jpg,svg,webp,tiff
* swf is not supported

Font:
* Chrome does not support fonts larger than 30MB

The picture dictionary recommends using the full-page version or the single-column version, because mobile browsers can zoom with two fingers, and the full-page version has less impact. The single-column version displays normally on mobile browsers, but the page is particularly long on computer browsers.

### not support

1. Dictionaries with unsorted word prefixes are not supported, and correct results will not be obtained.

2. Dictionaries produced by mdxbuilder4.0 are not supported.

3. IE browser is not supported.

4. Duplicate mdx file names are not supported, and only one of the mdx files with the same name will be loaded.

5. Fuzzy search is not supported.

6. Wildcard search and regular search are currently not supported.

### Common operations

[Common operations](doc/doc_op.md)

#### Modify dictionary library path

1. Rerun init_mdict_path.py, select the path, and the newly selected path will be inserted at the front.

2. Or manually modify the path of mdict_path.json. The format is as follows. mdict_path is the dictionary library path, and audio_path is the pronunciation library path.

The first path containing mdx files will be set as the dictionary library path, and the first path containing mdd files will be set as the pronunciation library path.

If mdict_path.json is empty, the dictionary library address is set to django-mdict/media/mdict/doc/, and the pronunciation library address is set to /django-mdict/media/mdict/audio/.

The d drive under windows is /mnt/d/ under wsl. Need double quotes and backslash or double slash as path separator.


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

#### Content scaling

Zoom page: Use the browser's zoom setting, and pinch to zoom on mobile browsers.

Scale text: Use the bottom button bar to increase font size and reduce font size buttons.

Zoom image:

1. Use the mobile browser to zoom directly with two fingers.
2. Open the computer browser to enable the magnifying glass button (effective for the next query).
3. Right-click on the image in your computer browser and open the image in a new tab.

#### In-page query

There is no in-page query function. You can only use the browser's own ctrl+F to search for expanded terms.

#### Merge terms with the same name

Modify the merge_entry_max_length in the configuration file django-mdict/config.ini.

The default value is 1000. When the same dictionary has multiple query results for the same query, entries with a length (length of the string, including html tags) less than 1000 will be merged and displayed. If no merging is required at all, set to 0.

#### Modify server port

The test server modifies 0.0.0.0:18000 in the startup script (run_server.bat, run_server_no_check.bat, run_server.sh, run_server_no_check.sh).

apache modifies VirtualHost *:80 in the configuration file django-mdict.conf.

#### initialization

When running the run_server script, initialization will only occur if the database db.sqlite3 in the root directory does not exist. If db.sqlite3 exists, the Django server will be started directly.

#### reduce size

In order to reduce the size, the following content can be deleted.

.git/ cannot operate git after deletion

deprecated/ can be deleted.

Media/font/ cannot be displayed in full Song font after deletion.

media/nltk_data/ has no English word prototype prediction function after deletion.

mdict/readlib/pyx/build/ intermediate file generated by cython compilation

mdict/readlib/pyx/mdict/ intermediate file generated by cython compilation

#### Word search API

1. Call the word search page in marginnote3

Settings/Research/Custom URL

[http://IP address:18000/mdict/?query={keyword}]()

2. Use the GET method to obtain the json results of the word search

[http://IP address:18000/api/mdict2/mdict/]()

The parameters are query:apple,page:1

3. Use url to get the json result of word search

[http://IP address:18000/api/mdict2/mdict/?query=apple&amp;page=2&amp;format=json]()

### Dependencies

1. requirements1.txt: required dependencies

The django version is 4

2. requirements2.txt: python-lzo needs to be installed manually on windows

[python-lzo](https://www.lfd.uci.edu/~gohlke/pythonlibs/#python-lzo)

### Admin operations and built-in dictionaries

[Admin operations](doc_admin.md)

### Full-text search

[Full-text search](doc_es.md)

### ANKI

[ANKI](doc_anki.md)

### Settings

[Settings](doc_config.md)
