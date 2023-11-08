# -*- coding: utf-8 -*-
import os
import re

from django.db.models.functions import Length
from spellchecker import SpellChecker

from base.base_utils import ROOT_DIR
from base.base_constant import builtin_dic_prefix, regp
from base.base_sys import check_system
from base.base_config import get_config_con, get_cpu_num
from base.base_utils import print_log_info
from mdict.models import MyMdictEntry, MyMdictItem
from mdict.mdict_utils.entry_object import entryObject
from mdict.mdict_utils.loop_search import loop_search_sug
from mdict.mdict_utils.ws_client import ws_search
from mdict.mdict_utils.data_utils import get_all_dics

from mdict.mdict_utils.multi_process import create_process_pool, multiprocess_search_mdx, pre_pool_search

prpool = None
thpool = None

if check_system() == 0:
    try:
        # 数据表不存在时，不创建进程池。
        all_dics = get_all_dics()
        prpool = create_process_pool()
        pre_pool_search(prpool)
    except Exception as e:
        print(e)
# else:
#     thpool = create_thread_pool()

try:
    from nltk.data import path as nltk_path
    from nltk.stem import WordNetLemmatizer

    nltk_path.append(os.path.join(ROOT_DIR, 'media', 'nltk_data'))
    lemmatizer = WordNetLemmatizer()
    lemmatizer.lemmatize('a')
    # WordNetLemmatizer()第一次运行lemmatize()慢，需要初始化，将本地语料库调入内存，耗时1秒多，因此这里要预加载。
except Exception as e:
    lemmatizer = None
    print(e)

spell = SpellChecker(distance=1)
# 默认距离为2，比较慢，大概1.6秒左右，设置距离为1后，大约0.001秒左右。

builtin_dic_name = '内置词典'


def search(query_list, group):
    record_list = []

    record_list = search_mdx_dic(query_list, record_list, group)

    builtin_dic_enable = get_config_con('builtin_dic_enable')

    if builtin_dic_enable:
        record_list = search_bultin_dic(query_list, record_list)

    return record_list


def search_revise(query, record_list, is_en):
    if len(record_list) == 0:
        words_list = lemmatize_func(query, record_list, is_en)
        c_list = key_spellcheck(query, record_list, is_en)
        if len(c_list) > 15:
            c_list = c_list[:15]

        if len(words_list) == 0 and len(c_list) == 0:
            return record_list

        mdict = [builtin_dic_prefix, f'<div>{query}</div>']
        if len(words_list) > 0:
            for w in words_list:
                mdict.append(
                    '<div><span class="badge bg-secondary">原形推测</span><span class="badge bg-primary text-dark">'
                    + w[1] + '</span><a href="entry://' + w[0] + '">'
                    + w[0] + '</a></div>')

        if len(c_list) > 0:
            for c in c_list:
                mdict.append('<div><span class="badge bg-secondary">拼写检查</span><a href="entry://' + c + '">'
                             + c + '</a></div>')
        record_list.append(entryObject(builtin_dic_name, query, ''.join(mdict), 0, -1, -1, -1, -1))
    return record_list


def process_link(matched):
    return '<a class="badge bg-info" style="text-decoration:underline" href="entry://' + matched.group(
        1) + '">' + matched.group(1) + '</a>'


def process_link2(matched):
    return f'<details><summary>点击展开</summary>{matched.group(1)}</details>'


def search_bultin_dic_sug(query):
    r_list = search_builtin(query)
    a_list = []
    for r in r_list:
        a_list.append(r.mdict_entry)

    return a_list


sug_temp_list = []


def sug_callback(request, result):
    global mdx_temp_list
    sug_temp_list.clear()
    sug_temp_list.extend(result)


def search_mdx_sug(dic_pk, sug_list, group, flag):
    global prpool, thpool
    cnum = get_cpu_num()
    sug = []
    if check_system() == 0 and dic_pk == -1:
        q_list = ((i, sug_list, group, False) for i in range(cnum))
        record_list = prpool.starmap(multiprocess_search_mdx, q_list)
        for r in record_list:
            sug.extend(r)
    elif check_system() == 1 and dic_pk == -1:
        try:
            sug.extend(ws_search(sug_list, group, 'sug'))
        except Exception as e:
            print(e)
            # if thpool is None:
            #     thpool = create_thread_pool()
            # q_list = ((i, sug_list, group) for i in range(cnum))
            # record_list = thpool.starmap(multithread_search_sug, q_list)
            # for r in record_list:
            #     sug.extend(r)
    else:  # 单个词典的查询提示
        sug.extend(loop_search_sug(dic_pk, sug_list, flag, group))

    return sug


def get_min_length(str1, str2):
    return len(str1) if len(str1) <= len(str2) else len(str2)


def get_mdict_content(mymdictentry):
    mymdictitem_set = mymdictentry.mymdictitem_set.all()
    mdict_content = list()

    if len(mymdictitem_set) == 1:
        mdict_content.append(
            "<div class='card-body mymdict_entry'><b>" + mymdictentry.mdict_entry + "</b><ol class='olnone'>")
    else:
        mdict_content.append(
            "<div class='card-body mymdict_entry'><b>" + mymdictentry.mdict_entry + "</b><ol class='olnum'>")

    for m in mymdictitem_set:
        item_entry = ''
        if m.item_entry is not None:
            item_entry = m.item_entry
        item_content = ''
        if m.item_content is not None:
            # 如果是自带的TextField，为了在html上显示，需要手动将\r\n替换成<br />，这里用了ckeditor，就不用替换了
            item_content = m.item_content
            item_content = re.sub(r'\[link\](.+?)\[/link\]', process_link, item_content)  # link标签，词条跳转
            item_content = re.sub(r'\[wrap\](.+?)\[/wrap\]', process_link2, item_content)  # wrap标签，折叠内容
            # 懒惰匹配写成r'\[link\](.+)?\[/link\]'是错误的
        if m.item_type is None:
            mdict_content.append('<li class="mymdict_item">')
            if m.item_entry is None:
                mdict_content.append('<div style="background:#F5F5F5;">' + item_content + "</div></li>")
            else:
                mdict_content.append(item_entry + '<br /><div style="background:#F5F5F5;">' + item_content
                                     + "</div></li>")
        else:
            mdict_content.append(
                "<li class='mymdict_item'>" + item_entry
                + "<span class='badge bg-secondary' style='margin-left:0.2rem;color:#FFF;background-color:#6C757D;'><b>"
                + m.item_type.mdict_type + "</b></span><br /><div style='background:#F5F5F5;'>"
                + item_content + "</div></li>")

    mdict_content.append('</ol></div>')
    return mdict_content


def extract_bultin_dic_all(r_list):
    mdict = []
    mdx_entry = []
    r_list_len = len(r_list)
    mdict.append(builtin_dic_prefix)

    for i in range(0, r_list_len):
        r = r_list[i]
        if i < r_list_len - 1:
            mdx_entry.append(f'{r.mdict_entry}｜')
        else:
            mdx_entry.append(r.mdict_entry)

        mdict_content = get_mdict_content(r)

        if i < r_list_len - 1:
            mdict_content.append('<hr />')
        mdict.append(''.join(mdict_content))

    if r_list_len > 1:
        mdx_entry.append(f'【{len(r_list)}】')

    if r_list_len > 0:
        return entryObject(builtin_dic_name, ''.join(mdx_entry), ''.join(mdict), 0, -1, -1, -1, -1)
    else:
        return None


def sort_key(item):
    return item.mdict_entry.lower()


def search_builtin(query):
    # 查询内置词典
    query = regp.sub('', query).lower()
    if len(query) == 1:
        max_query_len = 1
    elif len(query) == 2:
        max_query_len = 3
    else:
        max_query_len = len(query) * 1.5

    r_list = MyMdictEntry.objects.all() \
        .filter(mdict_entry_strip__icontains=query) \
        .annotate(text_len=Length('mdict_entry_strip')) \
        .filter(text_len__lte=max_query_len)
    entry_list = MyMdictItem.objects.all() \
        .filter(item_entry_strip__icontains=query) \
        .annotate(text_len=Length('item_entry_strip')) \
        .filter(text_len__lte=max_query_len)

    r_dict = {}
    for r_item in r_list:
        r_dict.update({r_item.mdict_entry: r_item})
    for e_item in entry_list:
        if e_item.item_mdict is not None:
            i_mdict = e_item.item_mdict
            r_dict.update({i_mdict.mdict_entry: i_mdict})
    r_list2 = list(r_dict.values())
    r_list2.sort(key=sort_key)
    return r_list2


def search_bultin_dic(required, record_list):
    for query in required:
        r_list = search_builtin(query)

        m_entry = extract_bultin_dic_all(r_list)
        if m_entry is not None:
            record_list.append(m_entry)
    return record_list


mdx_temp_list = []


def mdx_callback(request, result):
    global mdx_temp_list
    mdx_temp_list.clear()
    mdx_temp_list.extend(result)


def search_mdx_dic(query_list, record_list, group):
    global prpool, thpool
    # 查询mdx词典
    cnum = get_cpu_num()
    if check_system() == 0:
        # prpool = check_pool_recreate(pool)
        q_list = ((i, query_list, group) for i in range(cnum))
        a_list = prpool.starmap(multiprocess_search_mdx, q_list)
        for a in a_list:
            record_list.extend(a)

    else:
        try:
            record_list.extend(ws_search(query_list, group, 'dic'))
        except Exception as e:
            print('ws server connection failed', e)
            # if thpool is None:
            #     thpool = create_thread_pool()
            # q_list = ((i, query_list, group) for i in range(cnum))
            # a_list = thpool.starmap(multithread_search_mdx, q_list)
            # for a in a_list:
            #     record_list.extend(a)

    return record_list


def key_spellcheck(query, record_list, is_en):
    # 拼写检查
    # 对只含字母，短横杠、撇号和空格的单词进行拼写检查
    c_list = []
    if is_en:
        c_list = spellcheck(query)
        for i in range(len(c_list) - 1, -1, -1):
            if c_list[i] == query.lower():
                del c_list[i]

    return c_list


def lemmatize_func(query, record_list, is_en):
    # 设置成自定义功能，全局启用原形推测，仅在查询无结果时启用原形推测，关闭原形推测，推荐第二种设置。
    words_list = []
    if is_en:
        words_list = lemmatize_word(query)

    return words_list


def lemmatize_word(query):  # 使用nltk的WordNetLemmatizer()获得单词变体的原形
    r_list = []
    if lemmatizer is not None:
        query = query.lower()
        words_list = list()
        # n名词,a形容词,r副词,v动词
        words_list.append((lemmatizer.lemmatize(query, pos='n'), 'n.'))
        words_list.append((lemmatizer.lemmatize(query, pos='a'), 'adj.'))
        words_list.append((lemmatizer.lemmatize(query, pos='r'), 'adv.'))
        words_list.append((lemmatizer.lemmatize(query, pos='v'), 'v.'))
        for w in words_list:
            if w[0] != query and not w[0] in r_list:
                r_list.append(w)

    return r_list


def spellcheck(query):  # 使用SpellChecker()来实现拼写检查
    misspelled = spell.unknown([query])
    c_list = []
    for word in misspelled:
        # Get the one `most likely` answer
        co = spell.correction(word)

        # Get a list of `likely` options
        ca = spell.candidates(word)
        if ca is not None:
            c_list.extend(list(ca))
            if co not in c_list:
                c_list.insert(0, co)

    return c_list
