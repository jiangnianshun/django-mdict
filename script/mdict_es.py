import os
import psutil
import time
import hashlib

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django
django.setup()

from mdict.mdict_utils.search_object import SearchObject
from mdict.models import MdictDic
from mdict.mdict_utils.init_utils import init_vars

from elasticsearch.helpers import parallel_bulk
from elasticsearch_dsl import connections, analyzer, Text, Index, Document
from elasticsearch.exceptions import TransportError

cpu_num = psutil.cpu_count(False)

connections.create_connection(hosts=['localhost'])

html_strip1 = analyzer('html_strip',
                       tokenizer="standard",
                       filter=["lowercase", "stop", "snowball"],
                       char_filter=["html_strip"]
                       )

html_strip2 = analyzer('html_strip',
                       tokenizer="standard",
                       filter=["lowercase", "stop", "snowball"],
                       char_filter=["html_strip"],
                       stopwords=["上一页", "下一页", "上一葉", "下一葉", "目录", "封面", "索引", "前言"]
                       )


class MdictEntry(Document):
    entry = Text(analyzer=html_strip1)
    content = Text(analyzer=html_strip2)


def get_list(dic, mdx, p1, p2, num, direction=1):
    s_obj = SearchObject(mdx, None, dic, '')
    entry_list, r_s_p1, r_s_p2, r_e_p1, r_e_p2 = s_obj.search_key_list(p1, p2, num, direction)

    return {'entry_list': entry_list, 's_p1': r_s_p1, 's_p2': r_s_p2, 'e_p1': r_e_p1, 'e_p2': r_e_p2,
            'length': s_obj.get_len()}


settings2 = {
    "settings": {
        "refresh_interval": '30s',
    },
}


def get_index_name(pk):
    return 'mdict-' + str(pk)


def create_index(dic, mdx):
    index = Index(get_index_name(dic.pk))
    index.settings(
        refresh_interval=-1,
        number_of_replicas=0,
        number_of_shards=1,
    )

    index.document(MdictEntry)
    # index.analyzer(html_strip)
    if not index.exists():
        index.create()
    else:
        print('index', dic.pk, 'already exists.')

    mdict_path = mdx.get_fpath()
    with open(mdict_path, 'rb') as f:
        data = f.read()

    m = hashlib.md5(data)
    mh = m.hexdigest()

    body = {
        "_meta": {
            "file": dic.mdict_file,
            "name": dic.mdict_name,
            "md5": mh,
        }
    }

    index.put_mapping(body=body)


def gen_data(content_list):
    for obj in content_list:
        yield obj


def get_content(dic, mdx, entry_list):
    p_list = []
    for entry in entry_list:
        s = entry[1]
        e = entry[2]
        p_list.append((s, e))

    record_list = SearchObject(mdx, None, dic, '').search_record_list(p_list, raw=True)

    for i in range(len(record_list)):
        entry = entry_list[i][0]
        query = entry[0]
        content = record_list[i]

        if content.startswith('@@@LINK='):
            continue

        yield {
            '_index': get_index_name(dic.pk),
            "entry": entry,
            "content": content,
        }


def create_cache(dic, mdx):
    seg_len = 50000
    chunk_size = 1000

    total_num = mdx.get_len()
    mdx_path = mdx.get_fpath()
    mdx_file_size = int(os.path.getsize(mdx_path) / 1000000)
    seg_size = seg_len * mdx_file_size / total_num
    if seg_size > 50:
        seg_len = int(50 * total_num / mdx_file_size)
        if seg_len < 1:
            seg_len = 1
        if seg_len < 1000:
            chunk_size = seg_len

    count = 0
    e_p1 = 0
    e_p2 = -1

    while True:
        try:
            r_dict = get_list(dic, mdx, e_p1, e_p2 + 1, seg_len)
            entry_list = r_dict['entry_list']
            if len(entry_list) == 0:
                r_dict = get_list(dic, mdx, e_p1 + 1, 0, seg_len)
                entry_list = r_dict['entry_list']
        except Exception:
            r_dict = get_list(dic, mdx, e_p1 + 1, 0, seg_len)
            entry_list = r_dict['entry_list']

        if len(entry_list) == 0:
            break
        s_p1 = r_dict['s_p1']
        # s_p2 = r_dict['s_p2']
        e_p1 = r_dict['e_p1']
        e_p2 = r_dict['e_p2']

        try:
            for r in parallel_bulk(connections.get_connection(), get_content(dic, mdx, entry_list), thread_count=cpu_num,
                                   chunk_size=chunk_size):
                pass
        except TransportError as e:
            print(get_index_name(dic.pk), e)
        count += len(entry_list)

        if s_p1 == -1:
            break

    index = Index(get_index_name(dic.pk))
    index.put_settings(body=settings2)


def close_index(dic):
    index = Index(get_index_name(dic.pk))
    index.close()


def delete_index(dic):
    index = Index(get_index_name(dic.pk))
    index.delete()


def create_es_with_pk(dic_pk):
    t1 = time.perf_counter()
    dic = MdictDic.objects.get(pk=dic_pk)
    item = init_vars.mdict_odict[dic.mdict_file]
    mdx = item.mdx
    create_index(dic, mdx)
    create_cache(dic, mdx)
    t2 = time.perf_counter()
    print(t2 - t1, mdx.get_fname(), mdx.get_len())


def create_es(dic, mdx):
    create_index(dic, mdx)
    create_cache(dic, mdx)


def create_all_es(pk_list=[]):
    t1 = time.perf_counter()
    odict = init_vars.mdict_odict
    odict_len = len(odict)
    i = 0
    for k in odict.keys():
        item = odict[k]
        mdx = item.mdx
        dics = MdictDic.objects.filter(mdict_file=mdx.get_fname())

        if len(dics) > 0:
            t1 = time.perf_counter()
            dic = dics[0]

            index_name = get_index_name(dic.pk)
            index = Index(index_name)
            if index.exists():
                print(index_name, 'already exists.')
                continue

            if not dic.mdict_es_enable:
                print(index_name, 'skip')
                continue

            if pk_list:
                if dic.pk in pk_list:
                    create_es(dic, mdx)

                    t2 = time.perf_counter()
                    print(i, '/', len(pk_list), get_index_name(dic.pk), t2 - t1, mdx.get_fname(), mdx.get_len())
            else:
                create_es(dic, mdx)
                t2 = time.perf_counter()
                print(i, '/', odict_len, get_index_name(dic.pk), t2 - t1, mdx.get_fname(), mdx.get_len())
        i += 1
    t2 = time.perf_counter()
    print('indexing time', t2 - t1)


create_es_with_pk(740)

# create_all_es()
