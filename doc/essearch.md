### 全文搜索

使用外置的elasticsearch实现全文搜索。

1. 安装依赖

```
pip install elasticsearch
pip install elasticsearch-dsl
```

2. 下载elasticsearch并解压。

[https://www.elastic.co/downloads/elasticsearch](https://www.elastic.co/downloads/elasticsearch)

3. 下载对应版本的elasticsearch-ik中文分词器并解压，将解压后的文件夹复制到elasticsearch的plugins目录下。

[https://github.com/medcl/elasticsearch-analysis-ik](https://github.com/medcl/elasticsearch-analysis-ik)

4. 运行elasticsearch/bin/elasticsearch.bat。

5. 进入django-mdict的admin，将需要索引的词典设置为启用es索引。对于反查词典和进行了词组提取的词典（比如搜韵诗词 全文检索.mdx、	英汉•汉英(专业•科技)词典.mdx）不需要进行全文索引。

6. 手动运行/django-mdict/script/mdict_es.py进行索引。

7. 索引完成后，打开
   
   [http://127.0.0.1/es/](http://127.0.0.1/es/)
   
   或

   [http://127.0.0.1:8000/es/](http://127.0.0.1:8000/es/)

* 注意python依赖和elasticsearch以及ik分词器的版本应当是对应的，否则可能无法正常运行。
