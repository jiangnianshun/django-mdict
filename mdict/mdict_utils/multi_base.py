import copy
import gc
import os
import time

from base.base_utils import ROOT_DIR
from base.base_config import get_config_con
from base.base_sys import check_system, check_apache
from mdict.mdict_utils.data_utils import get_or_create_dic, get_all_dics, check_dic_in_group
from mdict.mdict_utils.init_utils import initVars, load_cache
from mdict.mdict_utils.search_object import SearchObject
from mdict.mdict_utils.mdict_utils import get_dic_attrs, mdict_root_path
from mdict.mdict_utils.mdict_utils2 import sort_mdict_list
from mdict.mdict_utils.dic_object import dicObject

from mdict.mdict_utils.entry_object import entryObject

try:
    from mdict.models import MdictDicGroup
except Exception as e:
    pass

try:
    all_dics = get_all_dics()
except Exception as e:
    all_dics = None
    print(e)

if check_system() == 0:
    pickle_file_path = os.path.join(ROOT_DIR, '.cache', '.Linux.cache')
    from .init_utils import init_vars
else:
    pickle_file_path = os.path.join(ROOT_DIR, '.cache', '.Windows.cache')
    init_vars = initVars()
k_list = []


def merge_record(record_list):
    # 多于1个的词条进行合并，比如国家教育研究院双语词汇双向词典，该词典查variation有27个词条。
    # 长度小于500才合并，原因是英和中词典的a词条都合并起来，特别特别长，iframe展开时，台式机要卡住好长时间才能显示
    merge_entry_max_length = get_config_con('merge_entry_max_length')

    if merge_entry_max_length == 0:
        return record_list

    t_list = []
    name = ''
    entry = ''
    record = ''
    pror = 1
    counter = 0

    del_list = []
    del_item = []
    old_mdx_pk = 0
    for i in range(len(record_list) - 1, -1, -1):
        item = record_list[i]
        mdx_name = item.mdx_name
        mdx_entry = item.mdx_entry
        mdx_record = item.mdx_record
        mdx_pror = item.mdx_pror
        mdx_pk = item.pk

        if name == '':
            name = mdx_name

        if mdx_name == name:
            if len(mdx_record) < merge_entry_max_length:
                if mdx_entry.strip() not in entry:
                    entry = entry + '｜' + mdx_entry
                record = record + '<br/>' + mdx_record
                pror = mdx_pror
                counter += 1
                old_mdx_pk = mdx_pk
                del_item.append(i)
        else:
            if counter > 1:
                entry = entry[1:] + '【' + str(counter) + '】'
                t_list.append(entryObject(name, entry, record, pror, old_mdx_pk, -1, -1, -1))
                del_list.append(del_item.copy())

            name = mdx_name
            entry = '/' + mdx_entry
            record = mdx_record
            pror = mdx_pror
            counter = 1

            del_item.clear()
            del_item.append(i)

        if i == 0:
            if counter > 1:
                entry = entry[1:] + '【' + str(counter) + '】'
                t_list.append(entryObject(name, entry, record, pror, old_mdx_pk, -1, -1, -1))
                del_list.append(del_item.copy())

    for item in del_list:
        for i in item:
            del record_list[i]

    record_list.extend(t_list)
    return record_list


def init_obj(proc_flag):
    global init_vars, k_list

    # init_vars.mdict_odict = read_pickle_file(pickle_file_path, mdict_root_path)
    init_vars = load_cache(mdict_root_path)
    init_vars.mdict_odict, init_vars.indicator = sort_mdict_list(init_vars.mdict_odict)
    init_vars.mtime = os.path.getmtime(pickle_file_path)

    temp_list = []
    k_list = []
    if check_system() == 0:
        k_list = init_vars.indicator[proc_flag]
    else:
        # indicator_set = set(init_vars.indicator[proc_flag])
        for k in init_vars.indicator[proc_flag]:
            k_list.append(k)
            temp_list.append(init_vars.mdict_odict[k])

        init_vars.mdict_odict = temp_list
        gc.collect()
        # 每个进程只保存自己的数据，其他数据会被gc掉，减少windows下内存占用。但是ubuntu apache2下会导致占用内存暴增。


def multi_search_mdx(n, query_list, group_pk, is_mdx=True):
    global init_vars, k_list, all_dics

    try:
        # 获取最新数据
        all_dics = get_all_dics()
    except Exception as e:
        print(e)

    r_list = []

    if all_dics is None:
        return r_list

    if init_vars is None:
        init_obj(n)
    else:
        if init_vars.mtime is None:
            init_obj(n)
        else:
            if not check_apache():
                now_mtime = os.path.getmtime(pickle_file_path)
                cache_size = os.path.getsize(pickle_file_path)
                if init_vars.mtime < now_mtime and cache_size > 0:
                    init_obj(n)

    if check_system() == 0:
        k_list = init_vars.indicator[n]

    count = 0
    pcount = 0
    kcount = len(k_list)
    t1 = time.perf_counter()
    for k in k_list:
        if check_system() == 0:
            temp_object = init_vars.mdict_odict[k]
        else:
            temp_object = init_vars.mdict_odict[count]
            count += 1

        mdx = temp_object.mdx
        mdd_list = temp_object.mdd_list
        g_id = temp_object.g_id
        dict_file = mdx.get_fname()

        if isinstance(all_dics, dict):
            if k not in all_dics.keys():
                dic = get_or_create_dic(dict_file)
                all_dics = get_all_dics()
            else:
                dic_tuple = all_dics[k]
                dic = dicObject(*dic_tuple)
        else:
            dic_list = all_dics.filter(mdict_file=dict_file)
            if len(dic_list) == 0:
                dic = get_or_create_dic(dict_file)
            else:
                dic = dic_list[0]

        if dic is not None and dic.mdict_enable:
            params = (mdx, mdd_list, get_dic_attrs(dic), copy.copy(query_list))
            # query_list需要浅拷贝
            if group_pk == 0:  # 默认查询全部词典
                if is_mdx:
                    r_list.extend(SearchObject(*params, g_id=g_id).search_entry_list())
                else:
                    r_list.extend(SearchObject(*params).search_sug_list(3))
            else:  # 查询某个词典分组下的词典
                if check_dic_in_group(group_pk, dic.pk):
                    if is_mdx:
                        r_list.extend(SearchObject(*params, g_id=g_id).search_entry_list())
                    else:
                        r_list.extend(SearchObject(*params).search_sug_list(3))
        pcount += 1
        t2 = time.perf_counter()
        if t2 - t1 > 10:
            # 在nas（开启固态加速）上第一次查词非常慢，需要显示进度。
            print('Process', n, 'has completed', pcount / kcount, '...')

    if is_mdx:
        r_list = merge_record(r_list)
    return r_list
