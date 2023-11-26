import json
import math
import mimetypes
import re
import time
import csv
import random
from urllib.parse import quote, unquote

from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import get_language

from rest_framework import viewsets
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Index
from elasticsearch_dsl.query import MultiMatch
from elasticsearch.exceptions import ConnectionError, TransportError

from base.base_utils import is_en_func, strQ2B, request_body_serialze, guess_mime, h2k, k2h, kh2f, print_log_info
from base.base_utils2 import is_mobile
from base.base_utils3 import t2s, s2t
from base.base_constant import builtin_dic_prefix
from base.base_sys import check_system

from mdict.mdict_utils.mdict_utils import write_to_history, get_history_file, compare_time, get_dic_attrs, check_xapian
from mdict.mdict_utils.chaizi_reverse import HanziChaizi
from mdict.mdict_utils.data_utils import get_or_create_dic, init_database
from mdict.mdict_utils.loop_decorator import loop_mdict_list, innerObject
from mdict.mdict_utils.init_utils import init_vars, sound_list
from base.base_config import *
from mdict.mdict_utils.search_object import SearchObject
from mdict.mdict_utils.search_utils import search, search_bultin_dic_sug, search_mdx_sug, \
    search_revise, get_mdict_content
from .mdict_utils.entry_object import entryObject
from mdict.mdict_utils.romkan import to_hiragana, to_katakana, to_hepburn, to_kunrei

from mdict.models import MdictDic, MyMdictEntry, MdictDicGroup, MdictOnline, MyMdictItem, MyMdictEntryType
from mdict.serializers import MdictEntrySerializer, MyMdictEntrySerializer, MdictOnlineSerializer
from mdict.mdict_utils.mdict_utils import mdict_root_path, is_local, get_m_path
from mdict.mdict_utils.search_cache import sug_cache, MdictPage, key_paginator
from mdict.mdict_utils.anki import create_deck, get_decks, add_note

try:
    from mdict.readlib.lib.readzim import ZIMFile
except ImportError as e:
    # print_log_info('loading readzim lib failed!', 1)
    from mdict.readlib.src.readzim import ZIMFile

if check_xapian():
    import xapian
else:
    xapian = None

main_cur_language = 'en'

init_database()

reg = r'[ _=,.;:!?@%&#~`()\[\]<>{}/\\\$\+\-\*\^\'"\t]'
regp = re.compile(reg)

reght = r'<[^>]+>'
reghtml = re.compile(reght)
reght2 = r'<head[^>]+/head>'
reghtml2 = re.compile(reght)
reght3 = r'<script[^>]+/script>'
reghtml3 = re.compile(reght)
reght4 = r'<style[^>]+/style>'
reghtml4 = re.compile(reght)

meta_dict = {}


def init_meta_list(client):
    global meta_dict
    try:
        # get('mdict-*')只能获取open的index
        for index in client.indices.get_alias('mdict-*'):
            if index not in meta_dict:
                raw_data = client.indices.get_mapping(index=index)[index]['mappings']['_meta']
                meta_dict.update({index: raw_data})
        return True, None
    except ConnectionError as e:
        print(e)
        return False, e


class MdictEntryViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = []

    def retrieve(self, request, pk=None):
        query = self.request.query_params.get('query', '').strip()
        force_refresh = json.loads(self.request.query_params.get('force_refresh', 'false'))

        group = int(self.request.query_params.get('dic_group', 0))
        page = int(self.request.query_params.get('page', 1))

        fh_char_enable = self.request.query_params.get('fh_char_enable', None)
        st_enable = self.request.query_params.get('st_enable', None)
        chaizi_enable = self.request.query_params.get('chaizi_enable', None)
        kana_enable = self.request.query_params.get('kana_enable', None)
        romaji_enable = self.request.query_params.get('romaji_enable', None)
        magnifier_enable = self.request.query_params.get('magnifier_enable', None)

        query_params = {}

        if fh_char_enable is not None:
            query_params['fh_char_enable'] = json.loads(fh_char_enable)
        if st_enable is not None:
            query_params['st_enable'] = json.loads(st_enable)
        if chaizi_enable is not None:
            query_params['chaizi_enable'] = json.loads(chaizi_enable)
        if kana_enable is not None:
            query_params['kana_enable'] = json.loads(kana_enable)
        if romaji_enable is not None:
            query_params['romaji_enable'] = json.loads(romaji_enable)
        if magnifier_enable is not None:
            query_params['magnifier_enable'] = json.loads(magnifier_enable)

        if (force_refresh and page == 1) or key_paginator.get(query, group) is None:
            record_list = self.get_results(query, group, query_params)
            serializer = MdictEntrySerializer(record_list, many=True)
            p = MdictPage(query, group, serializer.data)
            key_paginator.put(p)

        k_page = key_paginator.get(query, group)
        ret = k_page.get_ret(page)

        if page == 1:
            history_enable = get_config_con('history_enable')
            if history_enable:
                write_to_history(query)

        return Response(ret)

    def get_results(self, query, group, query_params={}):
        record_list = []
        self.is_en = False

        if is_en_func(query):
            self.is_en = True

        query_list = get_query_list(query, query_params)

        if query_list:
            record_list = search(query_list, group)
            for query in query_list:
                record_list = search_revise(query, record_list, self.is_en)
            # record_list = clear_duplication(record_list)

            if len(record_list) == 0 and query.find('.htm') != -1:
                query = query[:query.find('.htm')]
                record_list = search(query, group)
                # 二十五史词典有些词条比如 史记_06但在超链接错误写成了史记_06.htm
            try:
                record_list.sort(key=lambda k: k.mdx_pror)
            except Exception as e:
                print(e)

        return record_list


def get_tokens(query):
    es_host = get_config_con('es_host')
    client = Elasticsearch(hosts=es_host)
    if not meta_dict:
        init_meta_list(client)
    index_name = ''
    for ind in meta_dict:
        if is_index_open(client, ind):
            index_name = ind
            break
    if index_name == '':
        return []

    tokenizer = 'standard'
    plugins_str = client.cat.plugins()
    if 'analysis-ik' in plugins_str:
        tokenizer = 'ik_smart'

    index = Index(index_name, using=client)
    tokens = index.analyze(
        body={
            "analyzer": tokenizer,
            "text": query
        }
    )

    token_list = []
    for tk in tokens['tokens']:
        token_list.append(tk['token'])

    return token_list


@api_view(['GET', 'POST', ])
@permission_classes([])
@authentication_classes([])
def fulltext_search(request):
    query = request.GET.get('query', '')
    # force_refresh = json.loads(request.GET.get('force-refresh', False))

    result_num = int(request.GET.get('result-num', 50))
    result_page = int(request.GET.get('result-page', 1))
    frag_size = int(request.GET.get('frag-size', 50))
    frag_num = int(request.GET.get('frag-num', 3))
    dic_pk = int(request.GET.get('dic-pk', -1))

    es_phrase = json.loads(request.GET.get('es-phrase', 'false'))
    es_entry = json.loads(request.GET.get('es-entry', 'false'))
    es_content = json.loads(request.GET.get('es-content', 'false'))
    es_and = json.loads(request.GET.get('es-and', 'false'))
    search_zim = json.loads(request.GET.get('search-zim', 'true'))

    is_en = False

    if is_en_func(query):
        is_en = True

    if result_num > 500:
        result_num = 500

    if frag_num > 15:
        frag_num = 15

    if frag_size < 5:
        frag_size = 5

    if frag_size > 200:
        frag_size = 200

    # group = int(request.GET.get('dic-group', 0))
    result = []
    total_count = 0
    tokens = []
    total_page_z = 0
    total_page_e = 0
    params = [query, dic_pk, result_num, result_page, frag_size, frag_num, es_entry, es_content, es_and, es_phrase]

    if dic_pk > -1:
        dics = MdictDic.objects.filter(pk=dic_pk)
        if len(dics) > 0:
            dic = dics[0]
            dic_file = dic.mdict_file
            temp_object = init_vars.mdict_odict[dic_file]
            if temp_object.mdx.get_fpath().endswith('.zim'):
                if check_xapian():
                    result, total_count, tokens, total_page_z = get_zim_results(*params)
            else:
                result, total_count, tokens = get_es_results(*params)
                total_page_z = 0
    else:
        tresult1 = []
        if search_zim and check_xapian():
            if len(init_vars.zim_list) > 30:
                params[2] = 3
            elif len(init_vars.zim_list) > 10:
                params[2] = 6
            else:
                params[2] = 15
            tresult1, ttotal_count1, tokens, total_page_z = get_zim_results(*params)
            total_count += ttotal_count1
            params[2] = 30
        try:
            # 连接es成功后再关闭es，下一次查询报ConnectionError
            tresult2, ttotal_count2, ttokens = get_es_results(*params)
            result.extend(tresult2)
            total_page_e = math.ceil(ttotal_count2 / params[2])
            total_count += ttotal_count2
            if ttokens:
                tokens = ttokens
        except ConnectionError:
            pass
        result.extend(tresult1)

    result = search_revise(query, result, is_en)

    serializer = MdictEntrySerializer(result, many=True)
    if total_page_z >= total_page_e:
        total_page = total_page_z
    else:
        total_page = total_page_e

    ret = {
        "page_size": len(result),  # 每页数据量
        "total_count": total_count,  # 总数据量
        "total_page": total_page,  # 总页数
        "current_page": result_page,  # 当前页数
        "data": serializer.data,
        "tokens": tokens
    }

    if result_page == 1:
        history_enable = get_config_con('history_enable')
        if history_enable:
            write_to_history(query)

    return Response(ret)


def get_zim_results(query, dic_pk, result_num, result_page, frag_size, frag_num,
                    es_entry, es_content, es_and, es_phrase):
    query = query.strip()
    tokens = query.split(' ')
    zim_list = []

    if dic_pk > -1:
        dics = MdictDic.objects.filter(pk=dic_pk)
        if len(dics) > 0:
            dic = dics[0]
            dic_file = dic.mdict_file
            temp_object = init_vars.mdict_odict[dic_file]
            zim_list.append(temp_object.mdx)
        else:
            return [], 0, []
    else:
        for zim in init_vars.zim_list:
            dics = MdictDic.objects.filter(mdict_file=zim.get_fname())
            if len(dics) > 0:
                dic = dics[0]
                if dic.mdict_enable:
                    zim_list.append(zim)
    result = []
    total_num = 0

    tquery_list = query.split(' ')
    if es_phrase:
        tokens = [query]
        query = '"' + query.replace('"', '') + '"'
    else:
        if es_and:
            query = ' AND '.join(tquery_list)
        else:
            query = ' OR '.join(tquery_list)
    total_page_z = 0

    for zim in zim_list:
        index_path_list = []
        if es_entry:
            index_path_list.append(zim.title_index_path)
        if es_content:
            index_path_list.append(zim.full_index_path)
        url_list = []

        for index_path in index_path_list:
            if index_path == '' or not os.path.exists(index_path):
                continue
            dics = MdictDic.objects.filter(mdict_file=zim.get_fname())
            if len(dics) > 0:
                dic = dics[0]
            else:
                continue
            try:
                t_result, url_list, total_num, ttotal_page_z = search_xapian(zim, index_path, query, dic_pk, dic,
                                                                             result_page, result_num, total_num,
                                                                             tquery_list, frag_num, frag_size, url_list)
                if ttotal_page_z > total_page_z:
                    total_page_z = ttotal_page_z
                result.extend(t_result)
            except Exception as e:
                print(e)

    return result, total_num, tokens, total_page_z


def search_xapian(zim, index_path, query, dic_pk, dic, result_page, result_num, total_num,
                  tquery_list, frag_num, frag_size, url_list):
    database = xapian.Database(index_path)
    # for index_path in zim_path:
    #     tdata = xapian.Database(index_path)
    #     database.add_database(tdata)
    # 合并多个数据库查询，不知道查询结果来自哪个数据库。
    enquire = xapian.Enquire(database)

    qp = xapian.QueryParser()
    qp.set_database(database)
    qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
    query_obj = qp.parse_query(query)
    enquire.set_query(query_obj)
    matches = enquire.get_mset((result_page - 1) * result_num, result_num)
    # 从参数1的位置取参数2个结果
    total_num += matches.get_matches_estimated()

    ttotal_page_z = math.ceil(matches.get_matches_estimated() / result_num)

    t_url_list = []
    result = []
    for match in matches:
        url = match.document.get_data().decode('utf-8')
        if url in url_list:
            # 去重
            continue
        else:
            t_url_list.append(url)
        if dic_pk > -1:
            sobj = SearchObject(zim, [], get_dic_attrs(dic), url, is_dic=True)
        else:
            sobj = SearchObject(zim, [], get_dic_attrs(dic), url, is_dic=False)
        entry_list = sobj.search_entry_list()
        if len(entry_list) == 0:
            continue
        entryobj = entry_list[0]
        entryobj.extra = get_highlight_frag(entryobj.mdx_record, tquery_list, frag_num, frag_size)
        result.append(entryobj)
    database.close()
    return result, t_url_list, total_num, ttotal_page_z


def get_hight_mark(content, tquery_list, frag_size):
    query = ' '.join(tquery_list)
    start_mark = content.find(query)
    if start_mark < 0:
        tqi = 0
        while tqi < len(tquery_list):
            start_mark = content.find(tquery_list[tqi])
            end_mark = start_mark + len(tquery_list[tqi])
            if start_mark > -1:
                break
            tqi += 1
    else:
        end_mark = start_mark + len(query)
    if start_mark < 0:
        start_mark = 0
        end_mark = 0

    s_mark = start_mark
    if start_mark - int(frag_size / 2) >= 0:
        s_mark = start_mark - int(frag_size / 2)
    if end_mark == 0:
        e_mark = 0
    else:
        e_mark = end_mark + int(frag_size / 2)
    if e_mark > len(content):
        e_mark = len(content) - 1
    frag_content = content[:e_mark + 1]
    frag_content = frag_content[s_mark:start_mark] + '<b style="background-color:yellow;color:red;font-size:0.8rem;">' \
                   + frag_content[start_mark:end_mark] + '</b>' + frag_content[end_mark + 1:e_mark]
    content = content[e_mark + 1:]
    return frag_content, content


def get_highlight_frag(record, tquery_list, frag_num, frag_size):
    content = remove_html_tags(record)
    # content=content.replace('<','').replace('>','')
    frag_content, content = get_hight_mark(content, tquery_list, frag_size)
    frag_count = 1

    while frag_count <= frag_num:
        f_content, content = get_hight_mark(content, tquery_list, frag_size)
        if f_content == '' or content == '':
            break
        frag_count += 1
        frag_content += '<br>' + f_content
        break
    return frag_content

    # return matches.snippet(content[high_mark:], frag_size, xapian.Stem('english'), 1,
    #                                  '<b style="background-color:yellow;color:red;font-size:0.8rem;">',
    #                                  '</b>', '...').decode('utf-8')


def remove_html_tags(content):
    content = content.replace('\n', '').replace('\r', '').replace(' ', '')
    content = reghtml2.sub('', content)
    content = reghtml3.sub('', content)
    content = reghtml4.sub('', content)
    return reghtml.sub('', content)


def init_index(request):
    group = int(request.GET.get('dic_group', 0))
    try:
        t1 = time.perf_counter()
        es_host = get_config_con('es_host')
        client = Elasticsearch(hosts=es_host)
        if not meta_dict:
            status, error = init_meta_list(client)
            if not status:
                return HttpResponse('error:' + str(error))
        init_index_list(group, client)
        t2 = time.perf_counter()
        return HttpResponse('success:' + str(t2 - t1))
    except Exception as e:
        print(e)
        return HttpResponse('error:' + str(e))


def download_history(request):
    file_list = get_history_file()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="history.csv"'
    writer = csv.writer(response)

    for file in file_list:
        try:
            file_path = os.path.join(ROOT_DIR, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                results = f.readlines()
            for result in results:
                if result.strip() != '':
                    data_item = result.strip().split('\t')
                    writer.writerow(data_item)
        except Exception as e:
            print(e)

    return response


def is_index_open(client, index_name):
    index_info = client.cat.indices(index=index_name, format='json')[0]
    index_status = index_info['status']
    if index_status == 'open':
        return True
    else:
        return False


def get_index_status(request):
    status_dict = {}
    try:
        es_host = get_config_con('es_host')
        client = Elasticsearch(hosts=es_host)
        indices = client.indices
        all_dics = MdictDic.objects.all()

        if not meta_dict:
            status, error = init_meta_list(client)
            if not status:
                return HttpResponse('error:' + str(error))

        mdict_keys = init_vars.mdict_odict.keys()

        for index_name in meta_dict:
            is_open = is_index_open(client, index_name)
            md5 = index_name[6:]
            dics = all_dics.filter(mdict_md5=md5)

            if len(dics) == 0:
                rd = meta_dict[index_name]
                if rd['file'] in mdict_keys:
                    item = init_vars.mdict_odict[rd['file']]
                    mdx = item.mdx
                    dics = MdictDic.objects.filter(mdict_file=mdx.get_fname())
                    if len(dics) > 0:
                        dic = dics[0]
                        if dic.mdict_md5 == '' or dic.mdict_md5 is None:
                            dic.mdict_md5 = md5
                            dic.save()
                else:
                    indices.close(index=index_name, ignore=[400, 404])

            if len(dics) > 0:
                dic = dics[0]
                # 1:index存在且打开，0:index存在但关闭，-1:index不存在
                if is_open:
                    index_status = 1
                else:
                    index_status = 0
                status_dict.update({dic.pk: index_status})

        for dic in all_dics:
            if dic.pk not in status_dict.keys():
                status_dict.update({dic.pk: -1})

        return HttpResponse(json.dumps({'status': status_dict, 'error': ''}))
    except Exception as e:
        return HttpResponse(json.dumps({'status': [], 'error': str(e)}))


def init_index_list(group, client):
    indices = client.indices
    all_dics = MdictDic.objects.all()
    all_groups = MdictDicGroup.objects.all()

    mdict_keys = init_vars.mdict_odict.keys()

    for index_name in meta_dict:
        is_open = is_index_open(client, index_name)
        md5 = index_name[6:]
        dics = all_dics.filter(mdict_md5=md5)

        if len(dics) == 0:
            rd = meta_dict[index_name]
            if rd['file'] in mdict_keys:
                item = init_vars.mdict_odict[rd['file']]
                mdx = item.mdx
                dics = MdictDic.objects.filter(mdict_file=mdx.get_fname())
                if len(dics) > 0:
                    dic = dics[0]
                    if dic.mdict_md5 == '' or dic.mdict_md5 is None:
                        dic.mdict_md5 = md5
                        dic.save()
            else:
                indices.close(index=index_name, ignore=[400, 404])

        if len(dics) == 0:
            if is_open:
                indices.close(index=index_name, ignore=[400, 404])
        else:
            dic = dics[0]
            if not dic.mdict_es_enable:
                dic.mdict_es_enable = True
                dic.save()

            if dic.mdict_enable:
                if group <= 0:
                    if not is_open:
                        indices.open(index=index_name, ignore=[400, 404])
                else:
                    group_list = all_groups.filter(pk=group)
                    if len(group_list) > 0:
                        temp = group_list[0].mdict_group.filter(pk=dic.pk)
                        if len(temp) > 0:
                            if not is_open:
                                indices.open(index=index_name, ignore=[400, 404])
                        else:
                            if is_open:
                                indices.close(index=index_name, ignore=[400, 404])
                    else:
                        if is_open:
                            indices.close(index=index_name, ignore=[400, 404])
            else:
                if is_open:
                    indices.close(index=index_name, ignore=[400, 404])


def sub_highlight(matched):
    text = matched.group(0)
    return '<b style="background-color:yellow;color:red;font-size:0.8rem;">' + text + '</b>'


def get_es_results(query, dic_pk, result_num, result_page, frag_size, frag_num, es_entry, es_content,
                   es_and, es_phrase):
    global meta_dict
    tokens = get_tokens(query)

    es_host = get_config_con('es_host')
    client = Elasticsearch(hosts=es_host)

    if not meta_dict:
        init_meta_list(client)

    # init_index_list(group)
    # 如果指定单独的index，当index_list长度超出后会报错RequestError 400 An HTTP line is larger than 4096 bytes.
    # 通过开关index实现指定index搜索，会增加耗时。

    search_fields = []

    if es_entry:
        search_fields.append('entry')
    if es_content:
        search_fields.append('content')

    if not search_fields:
        return [], 0, []

    if es_phrase:
        if es_and:
            q = MultiMatch(query=query, fields=search_fields, type='phrase', operator='AND')
        else:
            q = MultiMatch(query=query, fields=search_fields, type='phrase')
    else:
        if es_and:
            q = MultiMatch(query=query, fields=search_fields, operator='AND')
        else:
            q = MultiMatch(query=query, fields=search_fields)

    if dic_pk > -1:
        dics = MdictDic.objects.filter(pk=dic_pk)
        index_name = ''

        if len(dics) > 0:
            dic = dics[0]
            dic_md5 = dic.mdict_md5

            if dic_md5 == '' or dic_md5 is None:
                for meta_name, meta_body in meta_dict.items():
                    if dic.mdict_file == meta_body['file']:
                        index_name = meta_name
                        dic.mdict_md5 = index_name[6:]
                        dic.save()
                        break
            else:
                index_name = 'mdict-' + dic_md5

            if index_name == '':
                return [], 0, []
            else:
                s = Search(index=index_name).using(client).query(q)
        else:
            return [], 0, []
    else:
        # 查询全部索引
        s = Search(index='mdict-*').using(client).query(q)
    # s = Search(index='mdict-*').using(client).query("match_phrase", content=query)

    s = s[(result_page - 1) * result_num:result_page * result_num]
    # 默认只返回10个结果

    s = s.highlight('content', fragment_size=frag_size)

    s = s.highlight_options(order='score', pre_tags='@flag1', post_tags='@flag2', encoder='default',
                            number_of_fragments=frag_num)
    # html encoder会将html标签转换为实体

    try:
        response = s.execute()
    except TransportError as e:
        print(e)
        return [], 0, []

    total_count = response.hits.total.value
    # 结果总数，默认最大值是10000.

    result = []

    mdict_keys = init_vars.mdict_odict.keys()
    meta_dict_keys = meta_dict.keys()

    duplication_dict = {}

    for hit in response:
        meta = hit.meta

        index_name = meta.index

        if index_name not in meta_dict_keys:
            init_meta_list(client)

        highlight_content_text = ''

        if 'highlight' in meta:
            highlight = meta.highlight

            if 'content' in highlight:
                highlight_content = meta.highlight.content
                for hl in highlight_content:
                    hl = re.sub('<[^<]+?>', '', hl)

                    lflag = hl.find('>')
                    ltflag = hl.find('@flag1')
                    if -1 < lflag < ltflag:
                        hl = hl[lflag + 1:]

                    rflag = hl.rfind('<')
                    rtflag = hl.rfind('@flag2')
                    if rflag > -1 and rflag > rtflag + 6:
                        hl = hl[:rflag]

                    hl = hl.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '')

                    hl = hl.strip()

                    if len(hl) > frag_size * 2:
                        # 有时候会出现长度4000多的摘要
                        flag1 = hl.find('@flag1')
                        flag2 = hl.rfind('@flag2')
                        hl = hl[:flag2 + 6 + frag_size]
                        if flag1 > frag_size:
                            hl = hl[flag1 - frag_size:]

                    if highlight_content_text == '':
                        if hl not in highlight_content_text:
                            highlight_content_text = hl
                    else:
                        if hl not in highlight_content_text:
                            highlight_content_text = highlight_content_text + '<br/>' + hl

                highlight_content_text = highlight_content_text \
                    .replace('@flag1', '<b style="background-color:yellow;color:red;font-size:0.8rem;">') \
                    .replace('@flag2', '</b>')

        rd = meta_dict[index_name]

        md5 = index_name[6:]

        dics = MdictDic.objects.filter(mdict_md5=md5)

        if len(dics) == 0:
            dics = MdictDic.objects.filter(mdict_file=rd['file'])
            if len(dics) > 0:
                dic = dics[0]
                if dic.mdict_md5 == '' or dic.mdict_md5 is None:
                    dic.mdict_md5 = md5
                    dic.save()

        if rd['file'] in mdict_keys:
            item = init_vars.mdict_odict[rd['file']]
        elif rd['name'] in mdict_keys:
            item = init_vars.mdict_odict[rd['name']]
        else:
            print(rd['file'], rd['name'], 'not in the dic cache, the html cannot be rendered.')
            if len(dics) > 0:
                dic_pk = dics[0].pk
            else:
                dic_pk = 1
            record = hit['content']
            result.append(
                entryObject(rd['name'], hit['entry'], record, 1, dic_pk, 1, 1, 1, extra=highlight_content_text))
            continue

        mdx = item.mdx
        mdd_list = item.mdd_list

        if len(dics) > 0:
            dic = dics[0]
            if not dic.mdict_es_enable:
                dic.mdict_es_enable = True
                dic.save()
            if dic_pk > -1:
                is_dic = True
            else:
                is_dic = False
            record = SearchObject(mdx, mdd_list, get_dic_attrs(dic), '', is_dic=is_dic).substitute_record(
                hit['content'])

            # 去重
            if hit['content'].startswith('@@@LINK='):
                link2entry = hit['content'][8:].strip()
                if link2entry in duplication_dict.keys():
                    if dic.pk in duplication_dict[link2entry]:
                        continue
                    else:
                        duplication_dict[link2entry].append(dic.pk)
                else:
                    duplication_dict.update({link2entry: [dic.pk]})
            else:
                if hit['entry'] in duplication_dict.keys():
                    if dic.pk in duplication_dict[hit['entry']]:
                        continue
            duplication_dict.update({hit['entry'].strip(): [dic.pk]})

            result.append(
                entryObject(rd['name'], hit['entry'], record, 1, dic.pk, 1, 1, 1, extra=highlight_content_text))
        else:
            print(index_name, 'not exists in database.')

    return result, total_count, tokens


def get_query_list(query, query_params={}):
    # 找出query的各种变体（简繁，拆字反查，全角半角，假名）
    query_set = set()

    query = query.strip()

    if query:  # 非空字符串为True
        query_set.add(query)

        if 'fh_char_enable' in query_params.keys():
            fh_char_enable = query_params['fh_char_enable']
        else:
            fh_char_enable = get_config_con('fh_char_enable')

        if fh_char_enable:
            # 全角英文字母转半角
            q2b = strQ2B(query)
            if q2b != query:
                query_set.add(q2b)

        if 'romaji_enable' in query_params.keys():
            romaji_enable = query_params['romaji_enable']
        else:
            romaji_enable = get_config_con('romaji_enable')

        if romaji_enable:
            query_set.add(to_hiragana(query))
            query_set.add(to_katakana(query))
            query_set.add(to_hepburn(query))
            query_set.add(to_kunrei(query))

        if not is_en_func(query):
            # 非纯英文的处理
            if 'st_enable' in query_params.keys():
                st_enable = query_params['st_enable']
            else:
                st_enable = get_config_con('st_enable')
            if 'chaizi_enable' in query_params.keys():
                chaizi_enable = query_params['chaizi_enable']
            else:
                chaizi_enable = get_config_con('chaizi_enable')
            if 'kana_enable' in query_params.keys():
                kana_enable = query_params['kana_enable']
            else:
                kana_enable = get_config_con('kana_enable')

            if chaizi_enable and len(query) > 1:
                # 长度大于1时拆字反查
                result = hc.reverse_query(query)
                if result:
                    for r in result:
                        query_set.add(r)

            if st_enable:
                # 繁简转化
                q_s = t2s.convert(query)
                q_t = s2t.convert(query)
                if q_t != query:
                    query_set.add(q_t)
                    if chaizi_enable and len(q_t) > 1:
                        result = hc.reverse_query(q_t)
                        if result:
                            for r in result:
                                query_set.add(r)
                elif q_s != query:
                    query_set.add(q_s)
                    if chaizi_enable and len(q_s) > 1:
                        result = hc.reverse_query(q_s)
                        if result:
                            for r in result:
                                query_set.add(r)

            if kana_enable:
                # 平假名、片假名转化
                k_kana = h2k(query)
                h_kana = k2h(query)
                f_kana = kh2f(query)

                query_set.add(k_kana)
                query_set.add(h_kana)

                if f_kana != query:
                    query_set.add(f_kana)
                    fk_kana = k2h(f_kana)
                    query_set.add(fk_kana)

    return list(query_set)


hc = HanziChaizi()


@loop_mdict_list(return_type=1)
class search_mdx_key_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.pk == self.target_pk:
            result_list = SearchObject(mdx, mdd_list, get_dic_attrs(dic), '', is_dic=True).search_key(self.query)
            s = -1
            e = -1
            r_p1 = -1
            r_p2 = -1
            r_entry = ''
            if len(result_list) > 0:
                s = result_list[0][0]
                e = result_list[0][1]
                r_p1 = result_list[0][2]
                r_p2 = result_list[0][3]
                r_entry = result_list[0][4]
            # 这里后面再处理
            self.inner_dict = {'start': s, 'end': e, 'p1': r_p1, 'p2': r_p2, 'entry': r_entry}
            self.break_tag = True


def search_mdx_key(request):
    query = request.GET.get('entry')
    dic_pk = int(request.GET.get('dic_pk', -1))
    return_dict = search_mdx_key_object({'query': query, 'target_pk': dic_pk})
    if return_dict['start'] == -1:
        if not is_en_func(query):
            q_s = t2s.convert(query)
            q_t = s2t.convert(query)
            if q_s != query:
                return_dict = search_mdx_key_object({'query': q_s, 'target_pk': dic_pk})
                if return_dict['start'] == -1 and len(q_s) > 1:
                    result = hc.reverse_query(q_s)
                    if result:
                        for r in result:
                            return_dict = search_mdx_key_object({'query': r, 'target_pk': dic_pk})
                            if return_dict['start'] > -1:
                                break
            else:
                return_dict = search_mdx_key_object({'query': q_t, 'target_pk': dic_pk})
                if return_dict['start'] == -1 and len(q_t) > 1:
                    result = hc.reverse_query(q_t)
                    if result:
                        for r in result:
                            return_dict = search_mdx_key_object({'query': r, 'target_pk': dic_pk})
                            if return_dict['start'] > -1:
                                break

        q2b = strQ2B(query)

        if return_dict['start'] == -1 and q2b != query:
            return_dict = search_mdx_key_object({'query': q2b, 'target_pk': dic_pk})

    return HttpResponse(json.dumps(return_dict))


@loop_mdict_list()
class search_mdx_record_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.pk == self.target_pk:
            record = SearchObject(mdx, mdd_list, get_dic_attrs(dic), self.query, g_id=g_id, is_dic=True).search_record(
                self.start,
                self.end)
            self.inner_list = [
                {'mdx_name': dic.mdict_name, 'mdx_entry': self.query, 'mdx_record': record, 'pk': dic.pk}]
            self.break_tag = True


def search_mdx_record(request):
    query = request.GET.get('entry', '')
    dic_pk = int(request.GET.get('dic_pk', -1))
    s = int(request.GET.get('start', -1))
    e = int(request.GET.get('end', -1))
    if s == -1:
        return_list = []
    else:
        return_list = search_mdx_record_object({'query': query, 'target_pk': dic_pk, 'start': s, 'end': e})

    # 单词典查询不记录历史
    # history_enable = get_config_con('history_enable')
    # if history_enable:
    #     write_to_history(query)

    return HttpResponse(json.dumps(return_list))


def get_icon_path(mdx, icon):
    file = quote(mdx.get_fname())
    m_path = get_m_path(mdx)
    if icon == 'none':
        dic_icon = '/static/mdict/img/book.png'
    else:
        if is_local:
            dic_icon = os.path.join('/', m_path, file + '.' + icon)
        else:
            if m_path == '':
                t_path = file
            else:
                t_path = m_path + '/' + file
            dic_icon = '/mdict/getexfile/?path=' + t_path + '.' + icon
    return dic_icon


@loop_mdict_list()
class get_mdict_list_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        file = mdx.get_fname()
        if mdx.get_fpath().endswith('.zim'):
            m_type = 'zim'
        else:
            m_type = 'mdx'
        dic_icon = get_icon_path(mdx, icon)
        item = {'dic_name': dic.mdict_name, 'dic_file': quote(file), 'dic_icon': dic_icon,
                'dic_pror': dic.mdict_priority,
                'dic_pk': dic.pk, 'dic_enable': dic.mdict_enable, 'dic_es_enable': dic.mdict_es_enable,
                'dic_type': m_type}
        self.inner_list.append(item)


def get_mdict_list(requset):
    dic_list = get_mdict_list_object()
    dic_list.sort(key=lambda k: k['dic_pror'])

    return HttpResponse(json.dumps(dic_list))


def search_audio(request):
    key = request.GET.get('query', '')
    res_content = ''
    if key == '':
        return HttpResponse(res_content)
    res_name = unquote(key)
    f_name = res_name[res_name.rfind('\\') + 1:]
    mime_type = guess_mime(f_name)
    audio_type_list = ['.spx', '.mp3', '.wav']
    # 这里应该在readmdict中处理，比较时去掉不比较点和扩展名
    bk = False
    for tp in audio_type_list:
        t_res_name = '\\' + res_name + tp
        for mdd in sound_list:
            f = open(mdd.get_fpath(), 'rb')
            rr_list = mdd.look_up(t_res_name, f)
            if len(rr_list) > 0:
                res_content = rr_list[0][5]
                if mime_type is None:
                    f_name = rr_list[0][4]
                    mime_type = guess_mime(f_name)
                if t_res_name.endswith('.spx'):
                    mime_type = 'audio/speex'
                bk = True
                break
        if bk:
            break
    return HttpResponse(res_content, content_type=mime_type)


@loop_mdict_list()
class search_zim_dic_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.pk == self.target_pk:
            r_list = SearchObject(mdx, mdd_list, get_dic_attrs(dic), self.query, g_id=g_id,
                                  is_dic=True).search_entry_list()
            if len(r_list) > 0:
                record = r_list[0].mdx_record
                self.inner_list = [
                    {'mdx_name': dic.mdict_name, 'mdx_entry': self.query, 'mdx_record': record, 'pk': dic.pk}]
            else:
                self.inner_list = []

            self.break_tag = True


def search_zim_dic(request):
    query = request.GET.get('entry', '')
    dic_pk = int(request.GET.get('dic_pk', -1))

    if dic_pk == -1:
        return_list = []
    else:
        return_list = search_zim_dic_object({'query': query, 'target_pk': dic_pk})

    # 单词典查询不记录历史
    # history_enable = get_config_con('history_enable')
    # if history_enable:
    #     write_to_history(query)

    return HttpResponse(json.dumps(return_list))


def search_zim(request, *args):
    res_name = '/' + '/'.join(args[1:])
    res_name = unquote(res_name)
    dic_id = args[0]
    dics = MdictDic.objects.filter(pk=dic_id)
    res_content = ''
    mime_type = ''

    if len(dics) > 0:
        dic = dics[0]
        dic_name = dic.mdict_file
        if dic_name in init_vars.mdict_odict.keys():
            item = init_vars.mdict_odict[dic_name]
            mdx = item.mdx
            mdd_list = item.mdd_list
            res_content, mime_type = SearchObject(mdx, mdd_list, get_dic_attrs(dic), res_name, is_dic=True).search_mdd()

    return HttpResponse(res_content, content_type=mime_type)


def random_search(request, *args):
    mdict_odict_keys = list(init_vars.mdict_odict.keys())
    random_key = random.sample(mdict_odict_keys, 1)[0]
    random_mdict = init_vars.mdict_odict[random_key]
    dic = get_or_create_dic(random_key)
    mdx = random_mdict.mdx
    mdd_list = random_mdict.mdd_list
    g_id = random_mdict.g_id
    random_entry = SearchObject(mdx, mdd_list, get_dic_attrs(dic), '', g_id=g_id).random_search()
    return HttpResponse(random_entry)


zim_script = '''
<style>
.mdict-tooltip{
	background-color:gray !important;
	color:#EEEEEE !important;
	border-radius:5px !important;
	font-size:1.1em !important;
	z-index:999 !important;
}
.mdict-tooltip span{
	white-space:nowrap !important;
	margin:5px !important;
}
.mdict-tooltip span a{
	background-color:gray !important;
	text-decoration:none !important;
	color:#EEEEEE !important;
	font-style:normal !important;
}
</style>
<script src="/static/jquery/jquery.min.js"></script>
<script src="/static/mdict/js/base_func.js"></script>
<script src="/static/mdict/js/mdict_base.js"></script>
<script src="/static/mdict/js/iframe_base.js"></script>
<script>
$(document).ready(function(){init_iframe()});
</script>
'''


def search_mdd(request, *args):
    # path = request.GET.get('path', '')
    # if path == '' and len(args) > 0:
    #     # 处理外置css中的url
    #     path = '/'.join(args)

    dic_id = args[0]
    dics = MdictDic.objects.filter(pk=dic_id)
    res_content = ''
    mime_type = ''

    if len(dics) > 0:
        res_name = unquote(args[1])
        # flag = res_name.rfind('?path=')
        # if flag > -1:
        #     res_name = res_name[:flag]

        dic = dics[0]
        dic_name = dic.mdict_file
        if dic_name in init_vars.mdict_odict.keys():
            item = init_vars.mdict_odict[dic_name]
            mdx = item.mdx
            if mdx.get_fpath().find('.mdx') > -1:
                res_name = res_name.replace('/', '\\')
                if res_name[0] != '\\':
                    res_name = '\\' + res_name

            mdd_list = item.mdd_list
            sobj = SearchObject(mdx, mdd_list, get_dic_attrs(dic), res_name, is_dic=True)
            res_content, mime_type = sobj.search_mdd()
            if len(res_content) == 0 and res_name.startswith('\\data'):
                # 韩国国立国语院韩汉学习词典中资源链接以\data开头，但实际mdd中文件夹结构中没有data。
                sobj = SearchObject(mdx, mdd_list, get_dic_attrs(dic), res_name[5:], is_dic=True)
                res_content, mime_type = sobj.search_mdd()
            if len(res_content) == 0 and sobj.is_zim:
                # wikihow_en_maxi_2023-03的文章和图片都在C类下，但路径里没有C，需要手动添加
                if '.jpg' in res_name or '.png' in res_name or '.svg' in res_name or 'webp' in res_name or 'js' in res_name or 'css' in res_name:
                    if res_name.startswith('images') or res_name.startswith('videos') or res_name.startswith('assets'):
                        res_name = 'C/' + res_name
                        sobj = SearchObject(mdx, mdd_list, get_dic_attrs(dic), res_name, is_dic=True)
                        res_content, mime_type = sobj.search_mdd()

            if sobj.is_zim:
                if mime_type is not None:
                    from .mdict_utils.search_object import regpz
                    if 'html' in mime_type:
                        # zim跳转的而非查询的.html页面需要插入脚本
                        res_content = regpz.sub(sobj.substitute_hyper_link, res_content)
                        res_content = zim_script + res_content
        else:
            mdx = None

        if res_content == '' and mdx is not None:
            if res_name[0] == '\\' or res_name[0] == '/':
                res_name = res_name[1:]
            file_path = os.path.join(mdict_root_path, get_m_path(mdx, False), res_name)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    res_content = f.read()

    return HttpResponse(res_content, content_type=mime_type)


@loop_mdict_list(return_type=1)
class get_entry_list_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.pk == self.target_pk:
            entry_list, r_s_p1, r_s_p2, r_e_p1, r_e_p2 = SearchObject(mdx, mdd_list, get_dic_attrs(dic), '') \
                .search_key_list(self.p1, self.p2, self.num, self.direction)
            self.inner_dict = {'entry_list': entry_list, 's_p1': r_s_p1, 's_p2': r_s_p2, 'e_p1': r_e_p1, 'e_p2': r_e_p2}
            self.break_tag = True


def get_entry_list(request):
    dic_pk = int(request.GET.get('dic_pk', -1))
    p1 = int(request.GET.get('p1', 0))
    p2 = float(request.GET.get('p2', 0))
    num = int(request.GET.get('num', 15))
    direction = int(request.GET.get('direction', 0))
    # >0从p1,p2位置向后查num个词条，<0向前查，0向前后各查num/2个词条

    # if p1 == -1 or p2 == -1:
    #     return HttpResponse(json.dumps(entry_list))

    return_dict = get_entry_list_object(
        {'target_pk': dic_pk, 'p1': p1, 'p2': p2, 'num': num, 'direction': direction})
    return HttpResponse(json.dumps(return_dict))


def get_block_num(request):
    dic_pk = int(request.GET.get('dic_pk', -1))
    dics = MdictDic.objects.filter(pk=dic_pk)
    block_num = 0
    if len(dics) > 0:
        dic = dics[0]
        if dic.mdict_file in init_vars.mdict_odict.keys():
            item = init_vars.mdict_odict[dic.mdict_file]
            mdx = item.mdx
            if not mdx.get_fpath().endswith('.zim'):
                block_num = len(mdx._key_list)
    return HttpResponse(json.dumps({'block_num': block_num}))


@loop_mdict_list(return_type=1)
class get_dic_info_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.pk == self.target_pk:
            o = SearchObject(mdx, mdd_list, get_dic_attrs(dic), '', is_dic=self.is_dic)
            header = o.get_header()
            num_entrys = o.get_len()
            mdx_path = mdx.get_fpath().replace('\\', '/')
            mdd_path_list = []
            for mdd in mdd_list:
                mdd_path_list.append(mdd.get_fpath())
            mdd_path = '<br>'.join(mdd_path_list).replace('\\', '/')
            self.inner_dict = {'header': header, 'num_entrys': num_entrys, 'mdx_path': mdx_path, 'mdd_path': mdd_path}
            self.break_tag = True


def get_dic_info(request):
    dic_pk = int(request.GET.get('dic_pk', -1))
    is_dic = json.loads(request.GET.get('is_dic', "true"))
    return_dict = get_dic_info_object({'target_pk': dic_pk, 'is_dic': is_dic})

    # zim的info中含有图片导致json序列化失败
    for k1, v1 in return_dict.items():
        if isinstance(v1, bytes):
            return_dict[k1] = ''
        elif isinstance(v1, dict):
            for k2, v2 in v1.items():
                if isinstance(v2, bytes):
                    return_dict[k1][k2] = ''
    return HttpResponse(json.dumps(return_dict))


def mdict_index(request):
    global main_cur_language
    main_cur_language = get_language()
    query = request.GET.get('query', '')
    is_mb = is_mobile(request)
    return render(request, 'mdict/mdict-index.html', {'query': query, 'is_mobile': is_mb, 'type': 'index'})


def mdict_index_simple(request):
    global main_cur_language
    main_cur_language = get_language()
    query = request.GET.get('query', '')
    is_mb = is_mobile(request)
    return render(request, 'mdict/mdict-index-simple.html', {'query': query, 'is_mobile': is_mb, 'type': 'index'})


def mdict_index_simple2(request):
    global main_cur_language
    main_cur_language = get_language()
    query = request.GET.get('query', '')
    is_mb = is_mobile(request)
    return render(request, 'mdict/mdict-index-simple2.html', {'query': query, 'is_mobile': is_mb, 'type': 'simple2'})


@login_required()
def wordcloud(request):
    return render(request, 'mdict/wordcloud.html')


def shelf(request):
    request_url = request.META['REMOTE_ADDR']
    if request_url == "127.0.0.1":
        address = 'local'
    else:
        address = 'nonlocal'
    return render(request, 'mdict/shelf.html', {'address': address})


def shelf2(request):
    request_url = request.META['REMOTE_ADDR']
    if request_url == "127.0.0.1":
        address = 'local'
    else:
        address = 'nonlocal'
    return render(request, 'mdict/shelf2.html', {'address': address})


def shelf3(request):
    request_url = request.META['REMOTE_ADDR']
    if request_url == "127.0.0.1":
        address = 'local'
    else:
        address = 'nonlocal'
    return render(request, 'mdict/shelf3.html', {'address': address})


def doc(request):
    return render(request, 'mdict/md.html')


def grouping(request):
    return render(request, 'mdict/grouping.html')


special_char = {"punctuation-marks", "kharoshthi", "pahlavi", "runic", "avestan", "balinese", "bamum", "bassa-vah",
                "batak", "buhid", "caucasian-albanian", "cham", "elbasan", "grantha", "hanunoo", "kaithi", "kayah-li",
                "khojki", "khudawadi", "lepcha", "limbu", "linear-b-Syllabary", "mahajani", "mandaic", "manichaean",
                "mende-kikakui", "modi", "mro", "nabataean", "old-north-arabian", "old-permic", "pahawh-hmong",
                "palmyrene", "pau-cin-hau", "pollard", "rejang", "samaritan", "saurashtra", "sharada", "siddham",
                "sundanese", "syloti-nagri", "tagalog", "tagbanwa", "tai-tham", "tai-viet", "takri", "tirhuta",
                "varang-kshiti"}


def characters(request):
    char_path = os.path.join(ROOT_DIR, 'media', 'char', 'characters.json')
    data = {}
    with open(char_path, 'r', encoding='utf-8') as f:
        char_data = json.load(f)
    for key, value in char_data.items():
        if key in special_char:
            data.update({key: {'type': 'mark1', 'content': value}})
        else:
            data.update({key: {'type': 'mark2', 'content': value}})
    return render(request, 'mdict/characters.html', {'data': data})


@login_required()
def network(request):
    return render(request, 'mdict/builtin-network.html')


def get_mymdictentry(request):
    entry = request.GET.get('entry', '')
    mdictentry_list = MyMdictEntry.objects.filter(mdict_entry=entry)
    data = {'entry': entry, 'content': '该词条不存在！', 'pk': 0}
    if len(mdictentry_list) > 0:
        item = mdictentry_list[0]
        data['entry'] = item.mdict_entry
        mdict_content = ''.join(get_mdict_content(item)).replace('\r', '').replace('\n', '')
        data['content'] = builtin_dic_prefix + mdict_content + '\n</>'
        data['pk'] = item.pk
        return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(json.dumps(data))


def get_node_id(request):
    label = request.GET.get('label', '')
    data = {'pk': 0, 'error': ''}
    if label != '':
        try:
            mymdict_set = MyMdictEntry.objects.filter(mdict_entry=label)
            if len(mymdict_set) > 0:
                data['pk'] = mymdict_set[0].pk
                return HttpResponse(json.dumps(data))
            else:
                data['error'] = '词条不存在'
                return HttpResponse(json.dumps(data))
        except Exception as e:
            data['error'] = e
            return HttpResponse(json.dumps(data))
    data['error'] = 'error'
    return HttpResponse(json.dumps(data))


def add_node(request):
    label = request.GET.get('label', '')
    if label != '':
        try:
            MyMdictEntry.objects.create(mdict_entry=label)
            return HttpResponse('success')
        except Exception as e:
            return HttpResponse(e)
    return HttpResponse('error')


def add_edge(request):
    from_label = request.GET.get('from', '')
    to_label = request.GET.get('to', '')
    if from_label != '' and to_label != '':
        try:
            from_obj = MyMdictEntry.objects.get(mdict_entry=from_label)
            mymdictitem_set = from_obj.mymdictitem_set.all()
            if len(mymdictitem_set) == 0:
                item_content = '<p>[link]' + to_label + r'[/link]</p>'
                MyMdictItem.objects.create(item_content=item_content, item_mdict=from_obj)
            else:
                mdict_item = mymdictitem_set[0]
                item_content = mdict_item.item_content
                item_content += '<p>[link]' + to_label + r'[/link]</p>'
                mdict_item.item_content = item_content
                mdict_item.save()
            return HttpResponse('success')
        except Exception as e:
            return HttpResponse(e)
    return HttpResponse('error')


def edit_edge(request):
    from_label = request.GET.get('from', '')
    to_label = request.GET.get('to', '')
    old_from_label = request.GET.get('old_from', '')
    old_to_label = request.GET.get('old_to', '')
    if from_label != '' and to_label != '':
        try:
            old_from_obj = MyMdictEntry.objects.get(mdict_entry=old_from_label)
            mymdictitem_set = old_from_obj.mymdictitem_set.all()

            old_to_text = r'\[link\]' + old_to_label + r'\[/link\]'
            if from_label == old_from_label:
                to_text = '[link]' + to_label + '[/link]'
            else:
                to_text = ''

            if len(mymdictitem_set) == 0:
                return HttpResponse('error')
            for mdict_item in mymdictitem_set:
                item_content = mdict_item.item_content
                if re.search(old_to_text, item_content) is not None:
                    item_temp = re.sub(old_to_text, to_text, item_content)
                    mdict_item.item_content = item_temp
                    mdict_item.save()

            if from_label != old_from_label:
                from_obj = MyMdictEntry.objects.get(mdict_entry=from_label)
                mymdictitem_set = from_obj.mymdictitem_set.all()
                add_text = '<p>[link]' + to_label + '[/link]</p>'
                if len(mymdictitem_set) == 0:
                    MyMdictItem.objects.create(item_content=add_text, item_mdict=from_obj)
                else:
                    mdict_item = mymdictitem_set[0]
                    item_content = mdict_item.item_content
                    item_content += add_text
                    mdict_item.item_content = item_content
                    mdict_item.save()
            return HttpResponse('success')
        except Exception as e:
            return HttpResponse(e)
    return HttpResponse('error')


def get_node_group(mdict_entry):
    mymdict_set = MyMdictEntry.objects.filter(mdict_entry=mdict_entry)
    if len(mymdict_set) > 0:
        node_group = 'commonGroup'
    else:
        node_group = 'noneGroup'
    return node_group


def get_labels(request):
    label_set = MyMdictEntryType.objects.all().order_by('mdict_type')
    label_list = []
    for label in label_set:
        label_list.append((label.pk, label.mdict_type))
    return HttpResponse(json.dumps(label_list))


def get_nodes(request):
    only_edge_node = json.loads(request.GET.get('only_edge_node', 'false'))
    show_label = json.loads(request.GET.get('show_label', 'false'))

    entry_list = MyMdictEntry.objects.all()

    data_set = {}
    data_id = 1

    edge_list = []

    for entry in entry_list:
        mdict_entry = entry.mdict_entry

        link_set = {}
        label_list = []

        for mdict_item in entry.mymdictitem_set.all():
            item_entry = mdict_item.item_entry
            item_content = mdict_item.item_content
            item_type = mdict_item.item_type

            if item_type is not None:
                label_list.append(item_type.mdict_type)
            link_list = re.findall(r'\[link\](.+?)\[/link\]', item_content)
            if show_label:
                if item_entry is None and item_type is None:
                    item_label = ''
                elif item_entry is None:
                    item_label = item_type.mdict_type
                elif item_type is None:
                    item_label = item_entry
                else:
                    item_label = item_type.mdict_type + ':' + item_entry
            else:
                item_label = ''
            for link in link_list:
                if link in link_set.keys():
                    if item_label != '' and item_label not in link_set[link]:
                        link_set[link].append(item_label)
                else:
                    link_set.update({link: [item_label]})
        nlink_set = link_set

        data_set_keys = data_set.keys()
        if len(nlink_set) > 0:
            if mdict_entry not in data_set_keys:
                data_set.update(
                    {mdict_entry: {'id': data_id, 'label': mdict_entry, 'group': get_node_group(mdict_entry),
                                   'extra': label_list}})
                from_id = data_id
                data_id += 1
            else:
                from_id = data_set[mdict_entry]['id']
            for link, label_list in nlink_set.items():
                label = ','.join(label_list)
                if link not in data_set_keys:
                    data_set.update(
                        {link: {'id': data_id, 'label': link, 'group': get_node_group(link), 'extra': label_list}})
                    to_id = data_id
                    data_id += 1
                else:
                    to_id = data_set[link]['id']
                edge_list.append({'id': str(from_id) + '_' + str(to_id), 'from': from_id, 'to': to_id, 'label': label})
        else:
            if not only_edge_node:
                if mdict_entry not in data_set_keys:
                    data_set.update(
                        {mdict_entry: {'id': data_id, 'label': mdict_entry, 'group': get_node_group(mdict_entry),
                                       'extra': label_list}})
                    data_id += 1

    node_list = list(data_set.values())
    return HttpResponse(json.dumps({'nodes': node_list, 'edges': edge_list}))


def create_li(content, is_dir, file_type=''):
    if is_dir:
        return '<li data-path="' + str(content) + '" class="jstree-closed path-dir">' + str(content) + '</li>'
    else:
        dic_name = content[:-4]
        if dic_name in init_vars.mdict_odict.keys():
            item = init_vars.mdict_odict[dic_name]
            mdx = item.mdx
            icon = item.icon
            icon_path = get_icon_path(mdx, icon)
            if file_type == 'mdd':
                return '<li class="path-file" data-path="' + str(content) + '" data-jstree=\'{"disabled":true,"icon":"' \
                    + icon_path + '"}\'>' + str(content) + '</li>'
            else:
                return '<li class="path-file" data-path="' + str(content) + '" data-jstree=\'{"icon":"' \
                    + icon_path + '"}\'>' + str(
                        content) + '</li>'
        else:
            return ''


def create_li2(group_name, group_pk):
    return '<li data-pk="' + str(
        group_pk) + '" class="jstree-closed group-item" data-jstree=\'{"icon":"bi-window-dock"}\'>' + str(
        group_name) + '</li>'


def create_li3(mdict_name, mdict_file, mdict_pk):
    if mdict_name == mdict_file:
        return '<li class="dic-item" data-pk="' + str(mdict_pk) \
            + '" data-jstree=\'{"icon":"bi-file-earmark-fill"}\'>' \
            + str(mdict_name) + '</li>'
    else:
        return '<li class="dic-item" data-pk="' + str(mdict_pk) \
            + '" data-jstree=\'{"icon":"bi-file-earmark-fill"}\'>' \
            + str(mdict_name) + '<span style="color:red;"> (' + mdict_file + ')</span></li>'


def create_ul(path):
    ul_ele = "<ul>"
    for fl in os.listdir(path):
        fl_path = os.path.join(path, fl)
        if os.path.isdir(fl_path):
            ul_ele += create_li(fl, True)
        elif fl.endswith('mdd'):
            ul_ele += create_li(fl, False, 'mdd')
        elif fl.endswith('mdx') or fl.endswith('zim'):
            ul_ele += create_li(fl, False)
    ul_ele += '</ul>'
    return ul_ele


def create_ul2(group_list):
    ul_ele = '<ul><li class="group-root" data-jstree=\'{"opened":true,"icon":"bi-wallet-fill"}\'>分组<ul>'
    for gp in group_list:
        ul_ele += create_li2(gp.dic_group_name, gp.pk)
    ul_ele += '</ul></li></ul>'
    return ul_ele


def create_ul3(dic_list):
    ul_ele = '<ul>'
    for dic in dic_list:
        ul_ele += create_li3(dic.mdict_name, dic.mdict_file, dic.pk)
    ul_ele += '</ul>'
    return ul_ele


def grouping_mdictpath(request):
    path_name = request.GET.get("path", "")
    if path_name == "":
        root_content = "词典库(" + mdict_root_path + ")"
        jt_ele = '<ul><li data-path="_root" data-jstree=\'{"opened":true,"icon":"bi-wallet-fill"}\' class="path-root">' + root_content
        jt_ele += create_ul(mdict_root_path)
        jt_ele += '</li></ul>'
    else:
        if path_name == '_root':
            jt_ele = create_ul(mdict_root_path)
        else:
            jt_ele = create_ul(os.path.join(mdict_root_path, path_name))
    return HttpResponse(jt_ele)


def grouping_mdictgroup(request):
    group_pk = int(request.GET.get("group", 0))
    if group_pk == 0:
        group_list = MdictDicGroup.objects.all()
        jt_ele = create_ul2(group_list)
    else:
        group_list = MdictDicGroup.objects.filter(pk=group_pk)
        if len(group_list) > 0:
            dic_list = group_list[0].mdict_group.all().order_by('mdict_name')
            jt_ele = create_ul3(dic_list)
        else:
            jt_ele = ''

    return HttpResponse(jt_ele)


def create_group(request):
    group_name = request.GET.get('group_name', '')
    if group_name != "":
        try:
            MdictDicGroup.objects.create(dic_group_name=group_name)
            return HttpResponse('success')
        except Exception as e:
            return HttpResponse(e)
    return HttpResponse('failed')


def create_anki_deck(request):
    deck_name = request.GET.get('deck_name', '')
    if deck_name != "":
        result = create_deck(deck_name)
        return HttpResponse(result)
    return HttpResponse('failed')


def deck_group(request):
    deck_list = get_decks()
    return HttpResponse(json.dumps(deck_list))


def add_to_deck(request):
    deck_name = request.POST.get('deck_name', '')
    front_content = request.POST.get('front', '')
    back_content = request.POST.get('back', '')
    result = add_note(deck_name, front_content, back_content)
    return HttpResponse(str(result))


def open_folder(folder_path):
    if check_system() == 0:
        import subprocess
        subprocess.check_call(['gnome-open', '--', folder_path])
    elif check_system() == 1:
        os.startfile(folder_path)


def open_path(request):
    request_url = request.META['REMOTE_ADDR']
    open_path_enable = get_config_con('open_path_enable')
    if request_url == "127.0.0.1" and open_path_enable:
        # 只允许本地访问打开路径
        dic_pk = int(request.GET.get("dic_pk", -1))
        if dic_pk > -1:
            dics = MdictDic.objects.filter(pk=dic_pk)
            if len(dics) > 0:
                dic_file = dics[0].mdict_file
                item = init_vars.mdict_odict[dic_file]
                dic_path = item.mdx.get_fpath()
                if os.path.exists(dic_path):
                    try:
                        open_folder(os.path.dirname(dic_path))
                    except Exception as e:
                        print(e)
    return HttpResponse('success')


def add_dic_to_group(mdict_name, group_pk):
    groups = MdictDicGroup.objects.filter(pk=group_pk)
    if len(groups) == 0:
        return
    dics = MdictDic.objects.filter(mdict_file=mdict_name)
    groups[0].mdict_group.add(*dics)


def add_to_group(request):
    group_pk = int(request.GET.get("group_pk", -1))
    checked_path = request.GET.getlist('path', [])
    if group_pk >= 0 and checked_path:
        for cpath in checked_path:
            if cpath.endswith('.mdx') or cpath.endswith('.zim'):
                add_dic_to_group(cpath[:-4], group_pk)
            else:
                if cpath == '_root':
                    fpath = mdict_root_path
                else:
                    fpath = os.path.join(mdict_root_path, cpath)
                if os.path.exists(fpath):
                    for root, dirs, files in os.walk(fpath):
                        for file in files:
                            if file.endswith('.mdx') or file.endswith('.zim'):
                                add_dic_to_group(file[:-4], group_pk)
    return HttpResponse('success')


def delete_item(request):
    item_pk = int(request.GET.get("item_pk", -1))
    parent_pk = int(request.GET.get("parent_pk", -1))
    is_group = json.loads(request.GET.get("is_group", "false"))
    if item_pk >= 0:
        if is_group:
            groups = MdictDicGroup.objects.filter(pk=item_pk)
            if len(groups) > 0:
                groups[0].delete()
        elif parent_pk >= 0:
            groups = MdictDicGroup.objects.filter(pk=parent_pk)
            if len(groups) > 0:
                dics = MdictDic.objects.filter(pk=item_pk)
                if len(dics) > 0:
                    groups[0].mdict_group.remove(dics[0])

    return HttpResponse('success')


def rename_item(request):
    text = request.GET.get("text", "")
    item_pk = int(request.GET.get("item_pk", -1))
    is_group = json.loads(request.GET.get("is_group", "false"))
    if text != "" and item_pk >= 0:
        if is_group:
            groups = MdictDicGroup.objects.filter(pk=item_pk)
            if len(groups) > 0:
                groups.update(dic_group_name=text)
        else:
            dics = MdictDic.objects.filter(pk=item_pk)
            if len(dics) > 0:
                dics.update(mdict_name=text)

    return HttpResponse('success')


def move_item(request):
    item_pk = int(request.GET.get("item_pk", -1))
    new_group_pk = int(request.GET.get("new_group_pk", -1))
    old_group_pk = int(request.GET.get("old_group_pk", -1))
    if item_pk >= 0 and 0 <= new_group_pk != old_group_pk >= 0:
        dics = MdictDic.objects.filter(pk=item_pk)
        if len(dics) > 0:
            groups = MdictDicGroup.objects.filter(pk=new_group_pk)
            if len(groups) > 0:
                groups[0].mdict_group.add(dics[0])
            groups = MdictDicGroup.objects.filter(pk=old_group_pk)
            if len(groups) > 0:
                groups[0].mdict_group.remove(dics[0])

    return HttpResponse('success')


def read_doc(doc_path):
    data = ''
    mime_type = 'text/markdown'
    if os.path.exists(doc_path):
        if doc_path.endswith('.jpg') or doc_path.endswith('.png'):
            with open(doc_path, 'rb') as f:
                data = f.read()
            mime_type = mimetypes.guess_type(doc_path)
        else:
            with open(doc_path, 'r', encoding='utf-8') as f:
                data = f.read()
    return data, mime_type


def doc_md(request, *args):
    doc_name = args[0]
    flag = doc_name.find('?')
    if flag > 0:
        doc_name = doc_name[:flag + 1]
    doc_path = os.path.join(ROOT_DIR, doc_name)
    data, mime_type = read_doc(doc_path)
    if data == '':
        data, mime_type = read_doc(os.path.join(ROOT_DIR, 'doc', doc_name))
    return HttpResponse(data, mime_type)


def getwordlist(request):
    start_time = request.GET.get('start_time', '')
    end_time = request.GET.get('end_time', '')
    wordcloud_length = int(request.GET.get('wordcloud_length', 2000))

    if wordcloud_length <= 0:
        wordcloud_length = 2000

    file_list = get_history_file()

    word_dict = {}
    for file in file_list:
        try:
            file_path = os.path.join(ROOT_DIR, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                results = f.readlines()
            for result in results:
                if result.strip() != '':
                    data_item = result.strip().split('\t')
                    if len(data_item) > 1:
                        time = data_item[0]
                        src_time = time[:time.find(':')].replace('.', '-')
                        word = data_item[1]
                        if start_time != '':
                            cmp = compare_time(src_time, start_time)
                            if cmp < 0:
                                continue
                        if end_time != '':
                            cmp = compare_time(src_time, end_time)
                            if cmp > 0:
                                continue
                        if word in word_dict.keys():
                            word_dict[word] += 1
                        else:
                            word_dict[word] = 1
        except Exception as e:
            print(e)

    word_list = []

    if len(word_dict) == 0:
        word_dict['无记录'] = 200

    max_num = max(word_dict.items(), key=lambda x: x[1])[1]

    if max_num < 200:
        scale = int(200 / max_num)
    else:
        scale = int(max_num / 200)

    for word, num in word_dict.items():
        tmp_num = num * scale
        if tmp_num < 1:
            tmp_num = 1
        word_list.append([word, tmp_num])

    word_list.sort(key=lambda k: k[1], reverse=True)

    return HttpResponse(json.dumps(word_list[:wordcloud_length]))


def es_index(request):
    global main_cur_language
    main_cur_language = get_language()
    query = request.GET.get('query', '')
    is_mb = is_mobile(request)
    return render(request, 'mdict/mdict-es-index.html', {'query': query, 'type': 'es', 'is_mobile': is_mb})


def mdict_dic(request, *args):
    global main_cur_language
    main_cur_language = get_language()
    # dic_pk = int(request.GET.get('dic_pk', -1))
    dic_pk = args[0]

    if dic_pk == -1:
        dics = MdictDic.objects.all().order_by('mdict_priority')
        if len(dics) > 0:
            dic_pk = dics[0].pk
    dic = MdictDic.objects.get(pk=dic_pk)
    dic_name = dic.mdict_name
    query = request.GET.get('query', '')
    is_mb = is_mobile(request)

    item = init_vars.mdict_odict[dic.mdict_file]
    mdx = item.mdx
    if mdx.get_fpath().endswith('.zim'):
        # isinstance(mdx, ZIMFile)判断不可靠
        return render(request, 'mdict/mdict-zim.html',
                      {'dic_pk': dic_pk, 'name': dic_name, 'query': '', 'type': 'zim', 'is_mobile': is_mb})
    else:
        return render(request, 'mdict/mdict-dic.html',
                      {'dic_pk': dic_pk, 'name': dic_name, 'query': query, 'type': 'dic', 'is_mobile': is_mb})


def es_dic(request, *args):
    # dic_pk = int(request.GET.get('dic_pk', -1))
    dic_pk = args[0]
    if dic_pk == -1:
        dics = MdictDic.objects.all().order_by('mdict_priority')
        if len(dics) > 0:
            dic_pk = dics[0].pk
    dic_name = MdictDic.objects.get(pk=dic_pk).mdict_name
    query = request.GET.get('query', '')
    is_mb = is_mobile(request)
    return render(request, 'mdict/mdict-es-dic.html',
                  {'dic_pk': dic_pk, 'name': dic_name, 'query': query, 'type': 'esdic', 'is_mobile': is_mb})


def bujianjiansuo(request):
    return render(request, 'mdict/bujian.html')


def get_dic_group(request):
    dic_group = MdictDicGroup.objects.all()
    r_list = []
    for g in dic_group:
        r_list.append((g.pk, g.dic_group_name))
    return HttpResponse(json.dumps(r_list))


def get_pk_in_group(request):
    group_pk = int(request.GET.get('dic_group', 0))
    group_list = MdictDicGroup.objects.filter(pk=group_pk)
    pk_list = []
    if len(group_list) > 0:
        pk_list = list(group_list[0].mdict_group.values_list('pk', flat=True))
    return HttpResponse(json.dumps(pk_list))


def edit_dic(request):
    cur_pk = int(request.GET.get('cur_pk', 0))
    prev_pk = int(request.GET.get('prev_pk', 0))
    if cur_pk > 0:
        cur_dic = MdictDic.objects.get(pk=cur_pk)
        if prev_pk > 0:
            prev_dic = MdictDic.objects.get(pk=prev_pk)
            dic_priority = prev_dic.mdict_priority + 1
        else:
            dic_priority = 1
        cur_dic.mdict_priority = dic_priority
        cur_dic.save()
        return HttpResponse('success')
    return HttpResponse('error')


def get_prior(request):
    dic_set = MdictDic.objects.all().order_by('mdict_priority')
    pk_list = []
    for dic in dic_set:
        pk_list.append((dic.pk, dic.mdict_priority))
    return HttpResponse(json.dumps(pk_list))


def search_suggestion(request):
    query = request.GET.get('query', '').strip()
    dic_pk = int(request.GET.get('dic_pk', -1))

    if query == '':  # jquery-ui的下拉框的请求是term
        query = request.GET.get('term', '').strip()
    sug_num = request.GET.get('sug_num', 0)
    if sug_num == 0:
        sug_num = get_config_con('suggestion_num')
    group = int(request.GET.get('dic_group', 0))

    if query and sug_cache.get(query, group, dic_pk) is None:
        sug = []
        t_list = []

        required = get_query_list(query)

        if required:
            if dic_pk == -1:  # index页面才需要内置词典的查询提示
                sug.extend(search_bultin_dic_sug(query))

            sug.extend(search_mdx_sug(dic_pk, required, group, sug_num))

            q2b = strQ2B(query)

            return_sug = []

            for s in sug:
                if s.lower().strip() not in return_sug:
                    return_sug.append(s.lower().strip())
            return_sug.sort()
            tf1 = -1
            tf2 = -1
            tf3 = -1

            is_eng = is_en_func(query)

            for i in range(0, len(return_sug)):
                temp_str = return_sug[i].lower()
                # 对查询提示进行重排，将和query相等的词条设置位置第一
                # 1相等，2半角转化后相等，3去掉全角和半角空格后相等, 4stripkey后相等
                # 5繁简转化后相等
                if is_eng:
                    if temp_str.startswith(query.lower()):
                        tf1 = i
                        break
                    elif temp_str.startswith(query.lower()) > 0 \
                            or temp_str.startswith(q2b.lower()) > 0 \
                            or temp_str.startswith(query.lower().replace(' ', '').replace('　', '')) > 0 \
                            or temp_str.startswith(regp.sub('', query.lower())) > 0:
                        if tf2 == -1:
                            tf2 = i
                    elif temp_str.startswith(query.lower()[0]) or temp_str.startswith(q2b.lower()[0]):
                        if tf3 == -1:
                            tf3 = i
                else:
                    q_s = t2s.convert(query)
                    q_t = s2t.convert(query)
                    if temp_str.startswith(query.lower()):
                        tf1 = i
                        break
                    if temp_str.startswith(q_s) > 0 or temp_str.startswith(q_t) > 0:
                        if tf2 == -1:
                            tf2 = i
                    elif temp_str.startswith(q_s[0]) or temp_str.startswith(q_t[0]):
                        if tf3 == -1:
                            tf3 = i
            if tf2 == -1:
                tf2 = tf3
            if tf1 == -1:
                tf1 = tf2

            if tf1 == -1:
                t_list = return_sug[:sug_num]
            else:
                t_list = (return_sug[tf1:] + return_sug[:tf1])[:sug_num]

        sug_cache.put(query, group, dic_pk, t_list)

    r_list = sug_cache.get(query, group, dic_pk)

    return HttpResponse(json.dumps(r_list))


def get_external_file(request, *args):
    path = request.GET.get('path', '')
    if path == '' and len(args) > 0:
        # 处理外置css中的url
        path = '/'.join(args)

    if path[0] == '/':
        path = path[1:]
    file_path = os.path.join(mdict_root_path, path)
    mime_type = mimetypes.guess_type(file_path)[0]

    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            file_content = f.read()
    else:
        file_content = ''
    return HttpResponse(file_content, mime_type)


def set_mdict_enable(request):  # 将这里改成在viewsets里处理
    id = json.loads(request.GET.get('mdict_pk', "-1"))
    enable = json.loads(request.GET.get('mdict_enable', "false"))
    dic_list = request.GET.getlist('dic_list', [])

    if id > -1:
        dic = MdictDic.objects.filter(pk=id)
        if len(dic) > 0:
            dic.update(mdict_enable=enable)
        else:
            return HttpResponse("failed")
    else:
        if len(dic_list) > 0:
            update_list = []

            for pk in dic_list:
                qset = MdictDic.objects.filter(pk=pk)
                if len(qset) > 0:
                    qset[0].mdict_enable = enable
                    update_list.extend(qset)
            MdictDic.objects.bulk_update(update_list, ['mdict_enable'])
        else:
            return HttpResponse("failed")
    return HttpResponse("success")


def retrieve_config(request):
    con = get_config()
    search_config = {}

    for k, v in con['SEARCH'].items():
        search_config.update({k: v})

    r_config = {}
    for k2, v2 in con['SEARCH'].items():
        if v2 == 'True' or v2 == 'False':
            r_config.update({k2: con['SEARCH'].getboolean(k2)})
        elif isinstance(v2, str) and v2.isdigit():
            r_config.update({k2: con['SEARCH'].getint(k2)})
        else:
            print('error configuration ', k2, v2, type(v2))

    return HttpResponse(json.dumps(r_config))


def retrieve_config_dict(request):
    global main_cur_language
    if main_cur_language == 'zh-hans':
        r_config = {'force-refresh': '强制刷新', 'st-enable': '繁简转换', 'chaizi-enable': '拆字反查',
                    'fh-char-enable': '英文全角转半角',
                    'kana-enable': '平片假名转换', 'romaji-enable': '罗马字假名转换', 'link-new-label': '跳转新标签页',
                    'force-font': '强制全宋体',
                    'card-show': '展开多个词典', 'select-btn-enable': '启用查询菜单', 'new-label-link': '新标签页正查',
                    'fixed-height': '固定高度',
                    'magnifier-enable': '启用放大镜', 'hide-bottom-bar': '隐藏底部栏'}
    else:
        r_config = {'force-refresh': 'Force Refresh', 'st-enable': 'Chinese Simplified/Traditional', 'chaizi-enable': '拆字反查',
                    'fh-char-enable': 'Full-width to Half-width',
                    'kana-enable': 'Katakana/Hiragana', 'romaji-enable': 'Romaji Convert', 'link-new-label': 'Open Link in New Tab',
                    'force-font': 'Force 全宋体',
                    'card-show': 'Show Multiple Tabs', 'select-btn-enable': 'Enable Select Menu', 'new-label-link': 'New Tab in Search Page',
                    'fixed-height': 'Iframe Fixed Height',
                    'magnifier-enable': 'Enable Magnifier', 'hide-bottom-bar': 'Hide Bottom Bar'}

    return HttpResponse(json.dumps(r_config))


def save_config(request):
    config_dict = {}

    for k, v in request.GET.lists():
        config_dict.update({k: json.loads(v[0])})

    set_config('SEARCH', config_dict)
    return HttpResponse('success')


class MyPageNumberPagination(PageNumberPagination):
    page_size = 15
    max_page_size = 20
    page_size_query_param = 'size'
    page_query_param = 'page'
    '''
分页设置
在网络地址中加问号来传参
比如
/?page=2
得到每页显示2个的第二页json数据
/?page=2&size=5
得到每页显示5个的第二页json数据
page_size是默认每页显示数量
max_page_size设置最大每页数量，请求超过这个值则无效。
    '''


class MdictOnlineViewSet(viewsets.ModelViewSet):
    queryset = MdictOnline.objects.all()
    serializer_class = MdictOnlineSerializer
    pagination_class = MyPageNumberPagination
    authentication_classes = []
    permission_classes = []

    def filter_queryset(self, request):
        queryset = self.queryset.order_by('mdict_priority')
        # query = self.request.query_params.get('query')
        return queryset

    def partial_update(self, request, *args, **kwargs):
        # 通过/api/onlinedic/pk/来访问，使用PATCH
        data = request_body_serialze(request)
        instance = self.queryset.get(pk=kwargs.get('pk'))
        serializer = self.serializer_class(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['PATCH'])
    def list_update(self, request):
        data = request_body_serialze(request)
        for k, v in data.items():
            onlinedic = self.queryset.filter(mdict_name=k)
            if len(onlinedic) > 0:
                onlinedic.update(mdict_enable=v)
        return HttpResponse('success')


class MyMdictEntryViewSet(viewsets.ModelViewSet):
    queryset = MyMdictEntry.objects.all()
    serializer_class = MyMdictEntrySerializer
    pagination_class = MyPageNumberPagination
    authentication_classes = []
    permission_classes = []

    def filter_queryset(self, request):
        queryset = self.queryset.order_by('pk')
        # query = self.request.query_params.get('query')
        return queryset
