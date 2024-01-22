- [Full-text search](#Full-text search)
  * [Full-text search](#Full-text search)
  * [Install es on windows](#Install es on windows)
  * [Install xapian](#Install xapian)
  * [Filter function](#Filter function)
  * [Precautions](#Precautions)
  * [es index operation](#es index operation)
  * [es settings](#es settings)
  * [Known issues](#Known issues)
  * [es index performance test](#es index performance test)

### Full-text search

For mdx files, use external elasticsearch to implement full-text search, and for zim files, use the built-in xapian index to implement full-text search.

Hardware requirements: multi-core CPU, large memory, large-capacity solid-state drive

### Install es on windows

1. Install dependencies


```
pip install elasticsearch
pip install elasticsearch-dsl
```

2. Download elasticsearch and unzip it.

[https://www.elastic.co/downloads/elasticsearch](https://www.elastic.co/downloads/elasticsearch)

3. (Can be skipped) Download and decompress the elasticsearch-ik Chinese word segmenter corresponding to the es version, and copy the decompressed folder to the plugins directory of elasticsearch.

If you skip this step, the built-in standard tokenizer will be used.

[https://github.com/medcl/elasticsearch-analysis-ik/releases](https://github.com/medcl/elasticsearch-analysis-ik/releases)

4. (Skipable) It is recommended that es allocate 4g or more memory during query and indexing, modify the parameters -Xms1g and -Xmx1g in config/jvm.options, change 1 to 4, and restart es to take effect.

8.10.2 needs to turn off SSL. The following settings in config/elasticsearch.yml are set to false, xpack.security.enabled, xpack.security.enrollment.enabled, xpack.security.http.ssl:xpack.security.transport.ssl.

5. Run elasticsearch/bin/elasticsearch.bat to start es.

6. Enter the admin of django-mdict, set the dictionary that needs to be indexed to enable es index, and then click Save below.

7. Enter the admin of django-mdict, check the dictionary to be indexed, select Create es index in the action drop-down box, and then click Execute to start creating the index. The index creation progress can be viewed in the command line window of the run_server script and the command line window of es.

8. After creating the index, open
   
   [http://127.0.0.1/mdict/es/](http://127.0.0.1/mdict/es/)
   
   or

   [http://127.0.0.1:18000/mdict/es/](http://127.0.0.1:18000/mdict/es/)

   When performing full-text query, eselasticsearch.bat needs to be running all the time, otherwise the query will have no results.

### Install xapian

* Install with apt-get on ubuntu


```
apt-get install -y python3-xapian libxapian-dev
```

* You need to compile it yourself under windows. It is recommended to run on wsl1 (ubuntu).

[https://xapian.org/docs/install.html](https://xapian.org/docs/install.html)

### Filter function

* Query prefix and query content to set the fields to be queried

* The default is OR (or) query, each word appears at least once. After turning on AND query, all words must appear.

* Turning on query by phrase will require each word to appear and meet the requirements of adjacency and consistent order. From default query to AND query to phrase query, the results will become more and more precise, and the number will become smaller and smaller.
There is a problem with the phrase query of zim, and the impact is not avoided. When querying the phrase, you can close the query zim and not query it.

### Precautions

* Note that the python dependencies should correspond to the versions of elasticsearch and ik word segmenter.

* A solid-state drive will greatly increase the indexing speed. It is recommended to place es on a solid-state drive. The index file size is about 2.5-3.5 times the size of the mdx file. Be careful to reserve enough space.

* What is saved in es is unprocessed HTML. You must ensure that the dictionary library path is set correctly, so that the mdx and mdd of the dictionary will be loaded when querying. Otherwise, the generated page will have no style and no pictures. If the mdx is modified, the file name or md5 will occur. Changes may result in the inability to load mdx correctly during full-text search, resulting in no style or images on the page.

* Dictionary grouping and starting and stopping a certain dictionary only modify the values in the database. You need to click the Start and Stop Index button to set the index of the corresponding dictionary to on or off. Note that starting and stopping a large number of indexes may be time-consuming. It's very long (the end of the circle indicates that the start and stop are completed, and the specific progress can be viewed in the ES window prompt).

* Entries that appear frequently have high scores and will be ranked first. Therefore, a large number of encyclopedia mdx entries may appear in the front pages, causing interference to the results. At this time, these dictionaries can be indexed by starting and stopping the index. No inquiry is made.

* There are three columns of icons in front of the dictionary name in the dictionary list. The first column sets whether it is enabled, and then click the start and stop index button to apply the changes to the es index. The second column indicates whether the es index is enabled for the current dictionary. The green check mark indicates that it is enabled, and the red check mark indicates that is disenabled. The cross indicates that it is closed, the third column is the current status of the index, the gray question mark indicates that it is unknown, the gray cloud indicates that es cannot be accessed, the green sun indicates that the index exists and is running, the orange moon indicates that the index exists but is closed, and the red cross indicates that the index does not exist.

* You can use kibana to view specific information about elasticsearch.

### es index operation

* Create index

Make sure elasticsearch is running, open the background management admin/Mdict dictionary, set the enable es dictionary option of the dictionary to be indexed to Yes, and click Save below.

Check the dictionary to be indexed, select Create es index in the action drop-down box, and click Execute.

* Delete index

Make sure elasticsearch is running, open the background management admin/Mdict dictionary, check the dictionary whose index you want to delete, select Delete es index in the action drop-down box, and click Execute.

* If django-mdict is not started through run_server.bat, but is deployed on the server, you cannot view the progress of creating and deleting indexes, and you can run the script manually.

To create indexes for all dictionaries that are set to enable es but the index does not exist, run /django-mdict/script/mdict_es.py directly.

Create an index for the dictionary with id value (pk value) of 66,68,51


```
# cmd
mdict_es.py -c 66 68 51
# powershell
./mdict_es.py -c 66 68 51
```

Delete the index of the dictionary with id value (pk value) 66, 68, 51


```
# cmd
mdict_es.py -d 66 68 51
# powershell
./mdict_es.py -d 66 68 51
```

Delete all indexes


```
# cmd
mdict_es.py -da
# powershell
./mdict_es.py -da
```

curl deletes the specified index (index name is mdict- prefix plus the md5 value of the mdx file)


```
curl -X DELETE localhost:9200/index_name 
```
  
curl delete all indexes


```
curl -X DELETE localhost:9200/_all 
```

### es settings

es setting file is config/elasticsearch.yml

1. To avoid changing the port every time you start it, you can manually specify the port. At the same time, es_host in config.ini needs to be modified to the corresponding port.


```
http.port: 9200
```

3. Setting use_real_memory to false helps reduce the occurrence of CircuitBreakingException Data too large, but may cause es to crash.


```
indices.breaker.total.use_real_memory: false
```

2. Disabling memory swapping will improve query efficiency, but may cause a crash when there is insufficient memory.


```
bootstrap.memory_lock: true
```

3. If you want to connect to es on another machine, you need to set network.host and discovery.type, open ports 9200 and 9300 in the firewall, and then modify the es_host parameter in django-mdict/config.ini.


```
network.host: 0.0.0.0
discovery.type: single-node
```

### Known issues

* 429 error occurred while creating index or query.

1. Increase the memory allocated by es.

2. Try restarting es and clearing cache

3. Close some indexes and reduce the number of indexes running at the same time.
  
4. Try to index only a few dictionaries at a time.

* When creating indexes for a large number of dictionaries, it gets stuck, CPU usage is 0%, and no error is reported.

1. Try selecting a piece of text in the command line window and right-clicking to copy it. The operation may be restored.

* show connectionError

The es connection fails. Make sure that es is turned on and the url and port settings are correct. Sometimes the port is not the default 9200 after es is started. You can check the publish_address in the es command line window to confirm.

* When querying, an error occurs org.elasticsearch.action.NoShardAvailableActionException: No shard available for...

Wait for es startup to complete and the window displays Cluster health status changed from [RED] to [GREEN] before querying normally.

* es query speed is extremely slow, and overhead, spent [1.1s] collecting in the last [1.1s] information is constantly displayed.

There are too many dictionaries and insufficient memory. You need to close the index of some dictionaries or allocate more memory.

* OutOfMemoryError error occurs when querying

Same as above

### es index performance test


```
device A：
cpu：i5-4200m(2 physical core，base frequency 2.5，max frequency 3.0)
memory：total 8G，es 1G
disk：SATA
system：win10

device B：
cpu：3900X(12 physical core，base frequency 3.8，lock frequency 3.8)
memory：total 32G，es 2G
disk：M.2
system：win10

dictionary 1：牛津高阶8简体.mdx，mdx大小27.6MB，词条数92667
index time：
A：54.86s=0.91min
B：16.63s=0.28min
dictionary 2：bk2011.mdx（百度百科2011），mdx大小3.84GB，词条数3166098
index time：
A：5915.86s=98.60min=1.64h
B：2115.82s=35.26min
dictionary 3：enwiki-20190401.part1.mdx（英文维基part1），mdx大小3.50GB，词条数1265107
index time：
A：2891.99s=48.20min
B：620.94s=10.35min

设备B对词典库进行索引，词典数519，mdx大小41.57GB，生成索引文件大小136.37GB，总耗时22864.14秒=381.07分=6.35小时。
```
