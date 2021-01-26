- [全文搜索](#全文搜索)
  * [全文搜索](#全文搜索)
  * [windows下的安装](#windows下的安装)
  * [注意事项](#注意事项)
  * [索引性能测试](#索引性能测试)

### 全文搜索

使用外置的elasticsearch实现全文搜索。

### windows下的安装

1. 安装依赖

```
pip install elasticsearch
pip install elasticsearch-dsl
```

linux下是

```
pip3 install elasticsearch
pip3 install elasticsearch-dsl
```

2. 下载elasticsearch并解压，版本7.10.2或7.10.1。

[https://www.elastic.co/downloads/elasticsearch](https://www.elastic.co/downloads/elasticsearch)

3. 下载和es版本对应的elasticsearch-ik中文分词器并解压，将解压后的文件夹复制到elasticsearch的plugins目录下。

[https://github.com/medcl/elasticsearch-analysis-ik/releases](https://github.com/medcl/elasticsearch-analysis-ik/releases)

4. 运行elasticsearch/bin/elasticsearch.bat。

5. 进入django-mdict的admin，将需要索引的词典设置为启用es索引。对于反查词典和进行了词组提取的词典（比如搜韵诗词全文检索.mdx、英汉•汉英(专业•科技)词典.mdx）不需要进行全文索引。

6. 手动运行/django-mdict/script/mdict_es.py开始索引。

7. 索引完成后，打开
   
   [http://127.0.0.1/mdict/es/](http://127.0.0.1/mdict/es/)
   
   或

   [http://127.0.0.1:8000/mdict/es/](http://127.0.0.1:8000/mdict/es/)

8. 在进行全文查询时，eselasticsearch.bat需要一直运行，如果需要一直开启，可以加入系统启动项随系统启动。

### 注意事项

* 注意python依赖和elasticsearch以及ik分词器的版本应当是对应的。

* 固态硬盘会大大提高索引速度，索引文件大小大约是mdx文件大小的2.5-3.5倍，注意保留足够的空间。

* 如果JVM heap满载，尝试分配给es更多的内存，修改config/jvm.options中的参数-Xms1g和-Xmx1g。

* 大量的429错误，资源不足，尝试降低单次提交的数量。

* 删除索引需要手动进行

删除id值(pk值)为66,68,51的词典的索引

```
# cmd
python mdict_es.py -d 66 68 51
# powershell
python ./mdict_es.py -d 66 68 51
```

删除全部索引

```
# cmd
python mdict_es.py -da
# powershell
python ./mdict_es.py -da
```

curl删除指定索引(index name是mdict-前缀加mdx文件的md5值)

```
curl -X DELETE localhost:9200/index_name 
```
  
curl删除全部索引

```
curl -X DELETE localhost:9200/_all 
```

### 索引性能测试

```
设备A：
cpu：i5-4200m(物理核心2，基频2.5，睿频3.0)
内存：物理内存8G，es分配内存1g
硬盘：SATA固态
系统：win10

设备B：
cpu：3900X(物理核心12，基频3.8，锁频3.8)
内存：物理内存32g，es分配内存2g
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
```
