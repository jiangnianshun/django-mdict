import os
import sys
import psutil
import time
import hashlib
import zlib

current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_path))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django

django.setup()

from mdict.mdict_utils.search_object import SearchObject
from mdict.models import MdictDic
from mdict.mdict_utils.init_utils import init_vars

from elasticsearch.helpers import parallel_bulk
from elasticsearch.helpers.errors import BulkIndexError
from elasticsearch_dsl import connections, analyzer, Text, Index, Document
from elasticsearch.exceptions import TransportError

error_log_path = os.path.join(current_path, 'error.log')

cpu_num = psutil.cpu_count(False)

connections.create_connection()

html_strip1 = analyzer('html_strip',
                       tokenizer="ik_smart",
                       filter=["lowercase", "stop", "snowball", "stemmer"],
                       char_filter=["html_strip"]
                       )

html_strip2 = analyzer('html_strip',
                       tokenizer="ik_smart",
                       filter=["lowercase", "stop", "snowball", "stemmer"],
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


def get_index_name_with_pk(dic_pk):
    return 'mdict-' + get_md5_with_pk(dic_pk)


def get_index_name(md5):
    return 'mdict-' + md5


def get_md5(mdx):
    mdict_path = mdx.get_fpath()
    with open(mdict_path, 'rb') as f:
        data = f.read()

    m = hashlib.md5(data)
    return m.hexdigest()


def get_md5_with_pk(dic_pk):
    dic = MdictDic.objects.get(pk=dic_pk)
    md5 = dic.mdict_md5
    if md5 == '':
        item = init_vars.mdict_odict[dic.mdict_file]
        mdx = item.mdx
        md5 = get_md5(mdx)
        dic.mdict_md5 = md5
        dic.save()
    return md5


def create_index(dic, md5):
    index = Index(get_index_name_with_pk(dic.pk))
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

    body = {
        "_meta": {
            "file": dic.mdict_file,
            "name": dic.mdict_name,
            "md5": md5,
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

    index_name = get_index_name_with_pk(dic.pk)

    for i in range(len(record_list)):
        entry = entry_list[i][0]
        content = record_list[i]

        if content.startswith('@@@LINK='):
            continue

        yield {
            '_index': index_name,
            "entry": entry,
            "content": content,
        }


def yield_data(data):
    for d in data:
        yield d


def write_error_log(*args):
    if not os.path.exists(error_log_path):
        with open(error_log_path, 'w', encoding='utf-8') as f:
            pass
    text = ''
    for arg in args:
        text += str(arg)
    with open(error_log_path, 'a', encoding='utf-8') as f:
        f.write('\n' + text)


def create_cache(dic, mdx):
    total_num = mdx.get_len()
    mdx_path = mdx.get_fpath()
    mdx_file_size = int(os.path.getsize(mdx_path) / (1024 * 1024))

    seg_size = cpu_num * 5
    seg_len = int(seg_size * total_num / mdx_file_size)

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

        t_list = list(get_content(dic, mdx, entry_list))
        t_size = sys.getsizeof(t_list)
        t_len = len(entry_list)
        chunk_size = int(cpu_num * 50 * t_len / t_size)
        if chunk_size < cpu_num:
            chunk_size = cpu_num

        try:
            for r in parallel_bulk(connections.get_connection(), yield_data(t_list),
                                   thread_count=cpu_num, chunk_size=chunk_size):
                pass
        except TransportError as e:
            index = Index(get_index_name_with_pk(dic.pk))
            index.delete()
            error_info = (get_index_name_with_pk(dic.pk), mdx.get_fname(), mdx.get_len(), str(e)[:2000])
            print(*error_info)
            write_error_log(error_info)
            break
        except BulkIndexError as e:
            index = Index(get_index_name_with_pk(dic.pk))
            index.delete()
            error_info = (get_index_name_with_pk(dic.pk), mdx.get_fname(), mdx.get_len(), str(e)[:2000])
            print(*error_info)
            write_error_log(error_info)
            break
        except zlib.error as e:
            error_info = (get_index_name_with_pk(dic.pk), mdx.get_fname(), mdx.get_len(), str(e)[:2000])
            print(*error_info)
            write_error_log(error_info)
        count += len(entry_list)

        if s_p1 == -1:
            break

    index = Index(get_index_name_with_pk(dic.pk))
    index.put_settings(body=settings2)


def close_index(dic):
    index = Index(get_index_name_with_pk(dic.pk))
    index.close()


def delete_index(dic):
    index = Index(get_index_name_with_pk(dic.pk))
    index.delete()


def create_es_with_pk(dic_pk):
    t1 = time.perf_counter()
    dics = MdictDic.objects.filter(pk=dic_pk)
    if len(dics) > 0:
        dic = dics[0]
        item = init_vars.mdict_odict[dic.mdict_file]
        mdx = item.mdx
        md5 = get_md5_with_pk(dic.pk)
        index_name = get_index_name(md5)
        index = Index(index_name)
        if index.exists():
            print('already exists', dic.mdict_name, index_name)
            return

        create_es(dic, mdx, md5)
        t2 = time.perf_counter()
        print(t2 - t1, mdx.get_fname(), mdx.get_len())
    else:
        print(dic_pk, 'not exists')


def create_es(dic, mdx, md5):
    create_index(dic, md5)
    create_cache(dic, mdx)


def create_all_es(pk_list=[]):
    t0 = time.perf_counter()
    odict = init_vars.mdict_odict
    odict_len = len(odict)
    i = 0
    for k in odict.keys():
        item = odict[k]
        mdx = item.mdx
        md5 = get_md5(mdx)
        dics = MdictDic.objects.filter(mdict_md5=md5)

        if len(dics) == 0:
            dics = MdictDic.objects.filter(mdict_file=mdx.get_fname())
            if len(dics) > 0:
                dic = dics[0]
                if dic.mdict_md5 == '' or dic.mdict_md5 is None:
                    dic.mdict_md5 = md5
                    dic.save()

        if len(dics) > 0:
            t1 = time.perf_counter()
            dic = dics[0]

            index_name = get_index_name_with_pk(dic.pk)
            index = Index(index_name)
            if index.exists():
                print('already exists', dic.mdict_name, index_name)
                continue

            if not dic.mdict_es_enable:
                print('index is disabled', dic.mdict_name, index_name)
                continue

            if pk_list:
                if dic.pk in pk_list:
                    create_es(dic, mdx, md5)
                    t2 = time.perf_counter()
                    print(i, '/', len(pk_list), get_index_name_with_pk(dic.pk), t2 - t1, mdx.get_fname(), mdx.get_len())
            else:
                create_es(dic, mdx, md5)
                t2 = time.perf_counter()
                print(i, '/', odict_len, get_index_name_with_pk(dic.pk), t2 - t1, mdx.get_fname(), mdx.get_len())
        else:
            print(mdx.get_fname(), 'not exists in database.')

        i += 1
    t3 = time.perf_counter()
    print('indexing time', t3 - t0)


create_es_with_pk(20)

# create_all_es()
