- [全文搜索](#全文搜索)
  * [全文搜索](#全文搜索)
  * [windows下安装es](#windows下安装es)
  * [安装xapian](#安装xapian)
  * [筛选功能](#筛选功能)
  * [注意事项](#注意事项)
  * [es索引操作](#es索引操作)
  * [es设置](#es设置)
  * [可能的问题](#可能的问题)
  * [es索引性能测试](#es索引性能测试)

### 全文搜索

对于mdx文件使用外置的elasticsearch实现全文搜索，对于zim文件使用内置xapian索引实现全文搜索。

硬件需求：多核CPU、大内存、大容量固态硬盘

### windows下安装es

1. 安装依赖

```
pip install elasticsearch
pip install elasticsearch-dsl
```

2. 下载elasticsearch并解压。

[https://www.elastic.co/downloads/elasticsearch](https://www.elastic.co/downloads/elasticsearch)

3. （可跳过）下载和es版本对应的elasticsearch-ik中文分词器并解压，将解压后的文件夹复制到elasticsearch的plugins目录下。

如果跳过该步，将会使用内置的standard分词器。

[https://github.com/medcl/elasticsearch-analysis-ik/releases](https://github.com/medcl/elasticsearch-analysis-ik/releases)

4. （可跳过）建议查询和索引时es分配4g或以上内存，修改config/jvm.options中的参数-Xms1g和-Xmx1g，将1改为4，重启es生效。

8.10.2需要关闭SSL，config/elasticsearch.yml以下均设置为false，xpack.security.enabled，xpack.security.enrollment.enabled，xpack.security.http.ssl:
xpack.security.transport.ssl。

5. 运行elasticsearch/bin/elasticsearch.bat启动es。

6. 进入django-mdict的admin，将需要索引的词典设置为启用es索引，然后单击下面的保存。

7. 进入django-mdict的admin，勾选要创建索引的词典，选择动作下拉框中的创建es索引，然后单击执行，开始创建索引。
   创建索引进度在run_server脚本的命令行窗口和es的命令行窗口中查看。

8. 创建索引完成后，打开
   
   [http://127.0.0.1/mdict/es/](http://127.0.0.1/mdict/es/)
   
   或

   [http://127.0.0.1:18000/mdict/es/](http://127.0.0.1:18000/mdict/es/)

   在进行全文查询时，eselasticsearch.bat需要一直运行，否则查询无结果，如果需要一直开启，需设置开机启动。

### 安装xapian

* ubuntu下使用apt-get安装

```
apt-get install -y python3-xapian libxapian-dev
```

* windows下需要自己编译，建议在wsl1(ubuntu)上运行。

[https://xapian.org/docs/install.html](https://xapian.org/docs/install.html)

### 筛选功能

* 查询词头和查询内容设置要查询的字段

* 默认是OR（或）查询，每个词至少出现一次，开启按照AND（与）查询后要求所有词都要出现。

* 开启按照词组查询会要求每个词都出现并满足相邻和顺序一致的要求，从默认查询到AND查询到词组查询，结果越来越精确，数量越来越少。
zim的词组查询有问题，未避免影响，在词组查询时可关闭查询zim，不对其进行查询。

### 注意事项

* 注意python依赖和elasticsearch以及ik分词器的版本应当是对应的。

* 固态硬盘会大大提高索引速度，建议将es放置在固态硬盘上，索引文件大小大约是mdx文件大小的2.5-3.5倍，注意保留足够的空间。

* es中保存的是未处理的html，必须保证正确设置词典库路径，这样查询时词典的mdx和mdd才会被加载，否则生成的页面无样式且无图片，mdx修改过使得文件名或md5发生变化，可能导致全文搜索时无法正确载入mdx，导致页面无样式、无图片。

* 词典分组和某个词典的启停仅修改了数据库中的值，需要单击启停索引按钮，才能将对应的词典的索引设置为开启或关闭状态，注意对大量索引进行启停操作可能耗时很长（转圈结束表示启停完成，具体进度可查看es的窗口提示）。

* 出现频率高的词条的得分高，会排在前面，因此百科类的mdx的词条可能会大量出现在前排，对结果造成干扰，此时可以将这些词典通过启停索引将索引关闭，不进行查询。

* 词典列表中词典名前面有三列图标，第一列设置是否启用，然后单击启停索引按钮，将改动应用到es索引，第二列表示当前词典是否开启es索引，绿色对号表示开启，红色叉号表示关闭，
  第三列是索引的当前状态，灰色问号表示未知，灰色云表示无法访问es，绿色太阳表示索引存在且运行中，橘色月亮表示索引存在但已关闭，红色叉号表示索引不存在。

* 可以使用kibana来查看elasticsearch的具体信息。

* 从主查询界面打开词典列表的某个词典，对该词典进行顺序查询。从全文搜索页面打开词典列表的某个词典，对该词典进行全文搜索。

### es索引操作

* 创建索引

确保elasticsearch已运行，打开后台管理admin/Mdict词典，将要索引的词典的启用es词典选项设置为是，然后单击下面的保存。

勾选要创建索引的词典，选择动作下拉框中的创建es索引，然后单击执行。

* 删除索引

确保elasticsearch已运行，打开后台管理admin/Mdict词典，勾选要删除索引的词典，选择动作下拉框中的删除es索引，然后单击执行。

* 如果django-mdict不是通过run_server.bat启动的，而是部署在服务器上，那么创建和删除索引无法查看进度，可以手动运行脚本。

创建所有设置为启用es但是索引不存在的词典的索引，直接运行/django-mdict/script/mdict_es.py。

创建id值(pk值)为66,68,51的词典的索引

```
# cmd
mdict_es.py -c 66 68 51
# powershell
./mdict_es.py -c 66 68 51
```

删除id值(pk值)为66,68,51的词典的索引

```
# cmd
mdict_es.py -d 66 68 51
# powershell
./mdict_es.py -d 66 68 51
```

删除全部索引

```
# cmd
mdict_es.py -da
# powershell
./mdict_es.py -da
```

curl删除指定索引(index name是mdict-前缀加mdx文件的md5值)

```
curl -X DELETE localhost:9200/index_name 
```
  
curl删除全部索引

```
curl -X DELETE localhost:9200/_all 
```

### es设置

es设置文件为config/elasticsearch.yml

1. 为避免每次启动端口发生变化，可以手动指定端口。同时config.ini中的es_host要修改为对应的端口。

```
http.port: 9200
```

3. 设置use_real_memory为false有助于减少CircuitBreakingException Data too large的发生，但是可能导致es崩溃。

```
indices.breaker.total.use_real_memory: false
```

2. 禁止内存交换会提高查询效率，但是当内存不足时可能导致崩溃。

```
bootstrap.memory_lock: true
```

3. 如果要连接另一台机器上的es，需要设置network.host和discovery.type，并在防火墙中放开9200和9300端口，然后在django-mdict/config.ini中修改es_host参数。

```
network.host: 0.0.0.0
discovery.type: single-node
```

### 可能的问题

* 创建索引或查询时出现429错误。

1. 增大es分配内存。

2. 尝试重启es，清除缓存

3. 将部分索引关闭，减小同时运行的索引数量。
  
4. 尝试每次只对少量词典创建索引。

* 大量词典创建索引时，卡住不动，cpu占用0%，无报错。

1. 原因未知，尝试在命令行窗口内选择一段文字，右键复制，可能恢复运行。

* 显示connectionError

es连接失败，确认es已开启且url和端口设置正确，有时es启动后不是默认的9200端口，通过查看es命令行窗口中的publish_address来确定。

* 查询时报错org.elasticsearch.action.NoShardAvailableActionException: No shard available for ...

等待es启动完成，窗口显示Cluster health status changed from [RED] to [GREEN]后可正常查询。

* es查询速度特别慢，且不断显示overhead, spent [1.1s] collecting in the last [1.1s]信息。

词典过多，内存不足，需要关闭部分词典的索引或者分配更大的内存。

* 查询时报错OutOfMemoryError

同上

### es索引性能测试

```
设备A：
cpu：i5-4200m(物理核心2，基频2.5，睿频3.0)
内存：物理内存8G，es分配内存1G
硬盘：SATA固态
系统：win10

设备B：
cpu：3900X(物理核心12，基频3.8，锁频3.8)
内存：物理内存32G，es分配内存2G
硬盘：M.2固态
系统：win10

词典1：牛津高阶8简体.mdx，mdx大小27.6MB，词条数92667
索引耗时：
A：54.86秒=0.91分
B：16.63秒=0.28分
词典2：bk2011.mdx（百度百科2011），mdx大小3.84GB，词条数3166098
索引耗时：
A：5915.86秒=98.60分=1.64小时
B：2115.82秒=35.26分
词典3：enwiki-20190401.part1.mdx（英文维基part1），mdx大小3.50GB，词条数1265107
索引耗时：
A：2891.99秒=48.20分
B：620.94秒=10.35分

设备B对词典库进行索引，词典数519，mdx大小41.57GB，生成索引文件大小136.37GB，总耗时22864.14秒=381.07分=6.35小时。
```
