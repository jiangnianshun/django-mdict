# coding:utf-8
import os
import sys
import psutil
import time
import hashlib
import zlib
import argparse

current_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_path))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django

django.setup()

from mdict.mdict_utils.search_object import SearchObject
from mdict.models import MdictDic
from mdict.mdict_utils.init_utils import init_vars
from mdict.mdict_utils.mdict_utils import get_dic_attrs

from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk
from elasticsearch.helpers.errors import BulkIndexError
from elasticsearch_dsl import connections, analyzer, Text, Index, Document
from elasticsearch.exceptions import TransportError, ConnectionError, NotFoundError

parser = argparse.ArgumentParser()
par = parser.add_mutually_exclusive_group()
par.add_argument('-c', '--create', nargs='+', default=[], help='create mdict index with id list')
par.add_argument('-ca', '--createall', action='store_false', help='create all mdict index')
par.add_argument('-d', '--delete', nargs='+', default=[], help='delete mdict index with id list')
par.add_argument('-da', '--deleteall', action='store_true', help='delete all mdict index')
args = parser.parse_args()
create_param = args.create
createall_param = args.createall
delete_param = args.delete
deleteall_param = args.deleteall

if not createall_param:
    createall_param = True

if deleteall_param:
    createall_param = False

if create_param:
    createall_param = False

if delete_param:
    createall_param = False

error_log_path = os.path.join(current_path, 'error.log')

cpu_num = psutil.cpu_count(False)

client = Elasticsearch()

tokenizer = 'standard'

plugins_str = client.cat.plugins()

if 'analysis-ik' in plugins_str:
    tokenizer = 'ik_smart'

html_strip1 = analyzer('html_analyzer',
                       tokenizer=tokenizer,
                       filter=["lowercase", "stemmer"],
                       char_filter=["html_strip"]
                       )
# stop停止词，去掉停止词会导致搜索词组出现问题
html_strip2 = analyzer('html_analyzer2',
                       tokenizer=tokenizer,
                       filter=["lowercase", "stemmer"],
                       char_filter=["html_strip"],
                       stopwords=["上一页", "下一页", "上一葉", "下一葉", "目录", "封面", "索引", "前言"]
                       )


class MdictEntry(Document):
    entry = Text(analyzer=html_strip1)
    content = Text(analyzer=html_strip2)


def get_list(dic, mdx, p1, p2, num, direction=1):
    s_obj = SearchObject(mdx, None, get_dic_attrs(dic), '')
    entry_list, r_s_p1, r_s_p2, r_e_p1, r_e_p2 = s_obj.search_key_list(p1, p2, num, direction)

    return {'entry_list': entry_list, 's_p1': r_s_p1, 's_p2': r_s_p2, 'e_p1': r_e_p1, 'e_p2': r_e_p2,
            'length': s_obj.get_len()}


settings2 = {
    "settings": {
        "refresh_interval": '20s',
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
    dics = MdictDic.objects.filter(pk=dic_pk)
    if len(dics) > 0:
        dic = dics[0]
        md5 = dic.mdict_md5
        od = init_vars.mdict_odict
        if md5 == '':
            if dic.mdict_file in od.keys():
                item = od[dic.mdict_file]
                mdx = item.mdx
                md5 = get_md5(mdx)
                dic.mdict_md5 = md5
                dic.save()
            else:
                return ''
        return md5
    else:
        return ''


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

    record_list = SearchObject(mdx, None, get_dic_attrs(dic), '').search_record_list(p_list, raw=True)

    index_name = get_index_name_with_pk(dic.pk)

    for i in range(len(record_list)):
        entry = entry_list[i][0]
        content = record_list[i]

        # if content.startswith('@@@LINK='):
        #     continue

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

    text = time.strftime("%Y.%m.%d:%H:%M:%S", time.localtime(time.time()))
    for arg in args:
        text += str(arg)
    text = '\n' + text + '\n'
    with open(error_log_path, 'a', encoding='utf-8') as f:
        f.write(text)


def write_exception_error(mdx, dic_pk, error):
    error_info = (get_index_name_with_pk(dic_pk), mdx.get_fname(), mdx.get_len(), str(error)[:2000])
    print(error_info)
    write_error_log(error_info)


def delete_failed_index(mdx, dic_pk):
    try:
        print('try delete failed index', get_index_name_with_pk(dic_pk))
        index = Index(get_index_name_with_pk(dic_pk))
        index.delete()
    except Exception as e:
        write_exception_error(mdx, dic_pk, e)


def create_cache(dic, mdx):
    total_num = mdx.get_len()
    mdx_path = mdx.get_fpath()
    mdx_file_size = int(os.path.getsize(mdx_path) / (1024 * 1024))

    seg_size = cpu_num * 3
    if mdx_file_size == 0:
        seg_len = 50000
    else:
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

        try:
            t_list = list(get_content(dic, mdx, entry_list))
            t_size = sys.getsizeof(t_list)
            t_len = len(entry_list)
            if t_size == 0:
                chunk_size = 1000
            else:
                chunk_size = int(cpu_num * 30 * t_len / t_size)
            if chunk_size < cpu_num:
                chunk_size = cpu_num

            for r in parallel_bulk(connections.get_connection(), yield_data(t_list),
                                   thread_count=cpu_num, chunk_size=chunk_size):
                pass

        except TransportError as e:
            delete_failed_index(mdx, dic.pk)
            write_exception_error(mdx, dic.pk, e)
            break
        except BulkIndexError as e:
            delete_failed_index(mdx, dic.pk)
            write_exception_error(mdx, dic.pk, e)
            break
        except zlib.error as e:
            write_exception_error(mdx, dic.pk, e)

        count += len(entry_list)
        if s_p1 == -1:
            break

    try:
        index = Index(get_index_name_with_pk(dic.pk))
        if index.exists():
            index.put_settings(body=settings2)
    except TransportError as e:
        write_exception_error(mdx, dic.pk, e)


def close_index_with_pk(dic_pk):
    index_name = get_index_name_with_pk(dic_pk)
    if index_name == 'mdict-':
        print(dic_pk, 'not exists')
        return
    index = Index(index_name)
    try:
        index.close()
    except NotFoundError as e:
        print(e)
    print('close', dic_pk, index_name)


def open_index_with_pk(dic_pk):
    index_name = get_index_name_with_pk(dic_pk)
    if index_name == 'mdict-':
        print(dic_pk, 'not exists')
        return
    index = Index(index_name)
    try:
        index.open()
    except NotFoundError as e:
        print(e)
    print('open', dic_pk, index_name)


def delete_index_with_pk(dic_pk):
    index_name = get_index_name_with_pk(dic_pk)
    if index_name == 'mdict-':
        print(dic_pk, 'not exists')
        return
    index = Index(index_name)
    try:
        index.delete()
    except NotFoundError as e:
        print(e)
    print('delete', dic_pk, index_name)


def delete_all_es():
    for index in client.indices.get_alias('mdict-*'):
        index = Index(index)
        index.delete()
        print('delete', index)


def create_es_with_pk(dic_pk):
    t1 = time.perf_counter()
    odict = init_vars.mdict_odict
    dics = MdictDic.objects.filter(pk=dic_pk)
    if len(dics) > 0:
        dic = dics[0]
        if dic.mdict_file in odict.keys():
            item = odict[dic.mdict_file]
            mdx = item.mdx
            if not check_zim(mdx):
                md5 = get_md5_with_pk(dic.pk)
                index_name = get_index_name(md5)
                index = Index(index_name)

                if index.exists():
                    print('index already exists', dic.mdict_name, index_name)
                    return

                if not dic.mdict_es_enable:
                    print('mdict_es_enable is False, index will not be created.', dic.mdict_name, index_name)
                    return

                create_es(dic, mdx, md5)
                t2 = time.perf_counter()
                print(t2 - t1, mdx.get_fname(), mdx.get_len())
        else:
            print(dic.pk, dic.mdict_name, 'not exists in cache. maybe the mdict root path is not correct.')
    else:
        print(dic_pk, 'not exists')


def create_es(dic, mdx, md5):
    try:
        create_index(dic, md5)
        create_cache(dic, mdx)
    except Exception as e:
        write_exception_error(mdx, dic.pk, e)


def check_zim(mdx):
    mdx_path = mdx.get_fpath()
    if mdx_path.endswith('.zim'):
        print('not support zim', mdx.get_fname())
        return True
    else:
        return False


def create_all_es(pk_list=[]):
    t0 = time.perf_counter()
    odict = init_vars.mdict_odict
    odict_len = len(odict)
    i = 0
    for k in odict.keys():
        item = odict[k]
        mdx = item.mdx
        i += 1

        if check_zim(mdx):
            continue
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
            try:
                if index.exists():
                    print('index already exists', dic.mdict_name, index_name)
                    continue
            except TransportError as e:
                write_exception_error(mdx, dic.pk, e)

            if not dic.mdict_es_enable:
                print('mdict_es_enable is False, index will not be created.', dic.mdict_name, index_name)
                continue

            if pk_list:
                if dic.pk in pk_list:
                    print('...starting indexing', mdx.get_fname(), dic.pk)
                    create_es(dic, mdx, md5)
                    t2 = time.perf_counter()
                    print(i, '/', len(pk_list), get_index_name_with_pk(dic.pk), t2 - t1, mdx.get_fname(), dic.pk,
                          mdx.get_len())
            else:
                print('...starting indexing', mdx.get_fname(), dic.pk)
                create_es(dic, mdx, md5)
                t2 = time.perf_counter()
                print(i, '/', odict_len, get_index_name_with_pk(dic.pk), t2 - t1, mdx.get_fname(), dic.pk,
                      mdx.get_len())
        else:
            print(mdx.get_fname(), 'not exists in database.')

    t3 = time.perf_counter()
    print('indexing time', t3 - t0)


if __name__ == '__main__':
    print('create_param', create_param)
    print('createall_param', createall_param)
    print('delete_param', delete_param)
    print('deleteall_param', deleteall_param)
    try:
        connections.create_connection()
        print('operation starting...')
        if delete_param:
            delete_list = []
            for d in delete_param:
                delete_list.append(int(d))
            for d in delete_list:
                delete_index_with_pk(d)
        elif create_param:
            create_list = []
            for c in create_param:
                create_list.append(int(c))
            for c in create_list:
                create_es_with_pk(c)
            # create_all_es(pk_list=create_list)
        elif createall_param:
            create_all_es()
        elif deleteall_param:
            delete_all_es()
        print('index operation has completed.')
    except ConnectionError as e:
        print(e)
