import json
import mimetypes
import re
import time
import csv
from urllib.parse import quote, unquote

from django.http import HttpResponse
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.decorators import action, api_view, authentication_classes, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch
from elasticsearch.exceptions import ConnectionError, TransportError

from base.base_func import is_en_func, strQ2B, request_body_serialze, guess_mime, h2k, k2h, kh2f
from base.base_func2 import is_mobile
from base.base_func3 import t2s, s2t

from mdict.mdict_utils.mdict_func import write_to_history, get_history_file, compare_time
from mdict.mdict_utils.chaizi_reverse import HanziChaizi
from mdict.mdict_utils.data_utils import get_or_create_dic, init_database
from mdict.mdict_utils.decorator import loop_mdict_list, inner_object
from mdict.mdict_utils.init_utils import init_vars, sound_list, init_mdict_list
from mdict.mdict_utils.mdict_config import *
from mdict.mdict_utils.search_object import SearchObject
from mdict.mdict_utils.search_utils import search, clear_duplication, search_bultin_dic_sug, search_mdx_sug, \
    search_revise
from mdict.serializers import mdxentry

from .models import MdictDic, MyMdictEntry, MdictDicGroup, MdictOnline
from .serializers import MdictEntrySerializer, MyMdictEntrySerializer, MdictOnlineSerializer
from .mdict_utils.mdict_func import mdict_root_path, is_local, get_m_path

from .mdict_utils.search_cache import sug_cache, MdictPage, key_paginator, es_paginator

init_database()

reg = r'[ _=,.;:!?@%&#~`()\[\]<>{}/\\\$\+\-\*\^\'"\t]'
regp = re.compile(reg)

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
        force_refresh = json.loads(self.request.query_params.get('force_refresh', False))

        group = int(self.request.query_params.get('dic_group', 0))
        page = int(self.request.query_params.get('page', 1))

        if (force_refresh and page == 1) or key_paginator.get(query, group) is None:
            record_list = self.get_results(query, group)
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

    def get_results(self, query, group):
        record_list = []
        self.is_en = False

        if is_en_func(query):
            self.is_en = True

        query_list = get_query_list(query)

        if query_list:
            record_list = search(query_list, group)
            for query in query_list:
                record_list = search_revise(query, record_list, self.is_en)
            record_list = clear_duplication(record_list)

            if len(record_list) == 0 and query.find('.htm') != -1:
                query = query[:query.find('.htm')]
                record_list = search(query, group)
                # 二十五史词典有些词条比如 史记_06但在超链接错误写成了史记_06.htm

            record_list.sort(key=lambda k: k.mdx_pror)

        return record_list


@api_view(['GET', 'POST', ])
@permission_classes([])
@authentication_classes([])
def es_search(request):
    query = request.GET.get('query', '')
    # force_refresh = json.loads(request.GET.get('force_refresh', False))

    result_num = int(request.GET.get('result_num', 50))
    result_page = int(request.GET.get('result_page', 1))
    frag_size = int(request.GET.get('frag_size', 50))
    frag_num = int(request.GET.get('frag_num', 3))

    es_phrase = json.loads(request.GET.get('es-phrase', 'false'))
    es_entry = json.loads(request.GET.get('es-entry', 'false'))
    es_content = json.loads(request.GET.get('es-content', 'false'))
    es_and = json.loads(request.GET.get('es-and', 'false'))

    is_en = False

    if is_en_func(query):
        is_en = True

    if result_num > 1000:
        result_num = 1000

    if frag_num > 15:
        frag_num = 15

    if frag_size > 200:
        frag_size = 200

    group = int(request.GET.get('dic_group', 0))

    result, total_count = get_es_results(query, group, result_num, result_page, frag_size, frag_num, es_phrase,
                                         es_entry, es_content,
                                         es_and)

    result = search_revise(query, result, is_en)

    serializer = MdictEntrySerializer(result, many=True)

    # total_count = 2000

    ret = {
        "page_size": len(result),  # 每页显示
        "total_count": total_count,  # 一共有多少数据
        "total_page": int(total_count / result_num),  # 一共有多少页
        "current_page": result_page,  # 当前页数
        "data": serializer.data,
    }

    if result_page == 1:
        history_enable = get_config_con('history_enable')
        if history_enable:
            write_to_history(query)

    return Response(ret)


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
            file_path = os.path.join(BASE_DIR, file)
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


def get_es_results(query, group, result_num, result_page, frag_size, frag_num, es_phrase, es_entry, es_content, es_and):
    global meta_dict
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
        return [],0

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
        return [],0

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
                mdxentry(rd['name'], hit['entry'], record, 1, dic_pk, 1, 1, 1, extra=highlight_content_text))
            continue

        mdx = item.mdx
        mdd_list = item.mdd_list

        if len(dics) > 0:
            dic = dics[0]
            if not dic.mdict_es_enable:
                dic.mdict_es_enable = True
                dic.save()
            record = SearchObject(mdx, mdd_list, dic, '').substitute_record(hit['content'])

            # 去重
            duplication_dict.update({hit['entry'].strip(): [dic.pk]})
            if hit['content'].startswith('@@@LINK='):
                link2entry = hit['content'][8:].strip()
                if link2entry in duplication_dict.keys():
                    if dic.pk in duplication_dict[link2entry]:
                        continue
                    else:
                        duplication_dict[link2entry].append(dic.pk)
                else:
                    duplication_dict.update({link2entry: [dic.pk]})

            result.append(mdxentry(rd['name'], hit['entry'], record, 1, dic.pk, 1, 1, 1, extra=highlight_content_text))
        else:
            print(index_name, 'not exists in database.')

    return result, total_count


def get_query_list(query):
    # 找出query的各种变体（简繁，拆字反查，全角半角，假名）
    query_list = []

    query = query.strip()

    if query:  # 非空字符串为True
        query_list.append(query)

        fh_char_enable = get_config_con('fh_char_enable')
        if fh_char_enable:
            # 全角英文字母转半角
            q2b = strQ2B(query)
            if q2b != query:
                query_list.append(q2b)

        if not is_en_func(query):
            # 非纯英文的处理
            st_enable = get_config_con('st_enable')
            chaizi_enable = get_config_con('chaizi_enable')
            kana_enable = get_config_con('kana_enable')

            if chaizi_enable and len(query) > 1:
                # 长度大于1时拆字反查
                result = hc.reverse_query(query)
                if result:
                    for r in result:
                        query_list.append(r)

            if st_enable:
                # 繁简转化
                q_s = t2s.convert(query)
                q_t = s2t.convert(query)
                if q_t != query:
                    query_list.append(q_t)
                    if chaizi_enable and len(q_t) > 1:
                        result = hc.reverse_query(q_t)
                        if result:
                            for r in result:
                                query_list.append(r)
                elif q_s != query:
                    query_list.append(q_s)
                    if chaizi_enable and len(q_s) > 1:
                        result = hc.reverse_query(q_s)
                        if result:
                            for r in result:
                                query_list.append(r)

            if kana_enable:
                # 平假名、片假名转化
                k_kana = h2k(query)
                h_kana = k2h(query)
                f_kana = kh2f(query)
                if k_kana != query:
                    query_list.append(k_kana)
                elif h_kana != query:
                    query_list.append(h_kana)

                if f_kana != query:
                    query_list.append(f_kana)
                    fk_kana = k2h(f_kana)
                    if fk_kana != f_kana:
                        query_list.append(fk_kana)

    return query_list


hc = HanziChaizi()


@loop_mdict_list(return_type=1)
class search_mdx_key_object(inner_object):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.pk == self.target_pk:
            result_list = SearchObject(mdx, mdd_list, dic, '').search_key(self.query)
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
class search_mdx_record_object(inner_object):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.pk == self.target_pk:
            record = SearchObject(mdx, mdd_list, dic, self.query, g_id=g_id).search_record(self.start, self.end)
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

    history_enable = get_config_con('history_enable')
    if history_enable:
        write_to_history(query)

    return HttpResponse(json.dumps(return_list))


@loop_mdict_list(return_type=2)
class get_mdict_list_object(inner_object):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        file = mdx.get_fname()
        m_path = get_m_path(mdx)
        dic = get_or_create_dic(file)
        file = quote(file)
        if icon == 'none':
            dic_icon = os.path.join('/', 'static', 'mdict', 'img', 'book.png')
        else:
            if is_local:
                dic_icon = os.path.join('/', m_path, file + '.' + icon)
            else:
                if m_path == '':
                    t_path = file
                else:
                    t_path = m_path + '/' + file
                dic_icon = '/mdict/exfile/?path=' + t_path + '.' + icon
        item = {'dic_name': dic.mdict_name, 'dic_file': file, 'dic_icon': dic_icon, 'dic_pror': dic.mdict_priority,
                'dic_pk': dic.pk, 'dic_enable': dic.mdict_enable, 'dic_es_enable': dic.mdict_es_enable}
        self.inner_odict.update({file: item})


def get_mdict_list(requset):
    dic_list = list(get_mdict_list_object().values())
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
    # 这里应该在readmdict_search中处理，比较时去掉不比较点和扩展名
    bk = False
    for tp in audio_type_list:
        res_name = '\\' + res_name + tp
        for mdd in sound_list:
            f = open(mdd.get_fpath(), 'rb')
            rr_list = mdd.look_up(res_name, f)
            if len(rr_list) > 0:
                res_content = rr_list[0][5]
                if mime_type is None:
                    f_name = rr_list[0][4]
                    mime_type = guess_mime(f_name)
                bk = True
                break
        if bk:
            break
    if res_name.endswith('.spx'):
        mime_type = 'audio/speex'
    return HttpResponse(res_content, content_type=mime_type)


def search_mdd(request, *args):
    dic_id = args[0]
    dics = MdictDic.objects.filter(pk=dic_id)
    res_content = ''
    mime_type = ''

    if len(dics) > 0:
        res_name = unquote(args[1]).replace('/', '\\')

        dic = dics[0]
        dic_name = dic.mdict_file
        if dic_name in init_vars.mdict_odict.keys():
            item = init_vars.mdict_odict[dic_name]
            mdx = item.mdx
            mdd_list = item.mdd_list
            res_content, mime_type = SearchObject(mdx, mdd_list, dic, res_name).search_mdd()

    return HttpResponse(res_content, content_type=mime_type)


@loop_mdict_list(return_type=1)
class mdict_all_entrys_object(inner_object):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.pk == self.target_pk:
            entry_list, r_s_p1, r_s_p2, r_e_p1, r_e_p2 = SearchObject(mdx, mdd_list, dic, '') \
                .search_key_list(self.p1, self.p2, self.num, self.direction)
            self.inner_dict = {'entry_list': entry_list, 's_p1': r_s_p1, 's_p2': r_s_p2, 'e_p1': r_e_p1, 'e_p2': r_e_p2}
            self.break_tag = True


def mdict_all_entrys(request):
    entry_list = []
    dic_pk = int(request.GET.get('dic_pk', -1))
    p1 = int(request.GET.get('p1', 0))
    p2 = int(request.GET.get('p2', 0))
    num = int(request.GET.get('num', 15))
    direction = int(request.GET.get('direction', 0))
    # >0从p1,p2位置向后查num个词条，<0向前查，0向前后各查num/2个词条

    if p1 == -1 or p2 == -1:
        return HttpResponse(json.dumps(entry_list))

    return_dict = mdict_all_entrys_object(
        {'target_pk': dic_pk, 'p1': p1, 'p2': p2, 'num': num, 'direction': direction})
    return HttpResponse(json.dumps(return_dict))


@loop_mdict_list(return_type=1)
class get_dic_info_object(inner_object):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        if dic.pk == self.target_pk:
            o = SearchObject(mdx, mdd_list, dic, '')
            header = o.get_header()
            num_entrys = o.get_len()
            self.inner_dict = {'header': header, 'num_entrys': num_entrys}
            self.break_tag = True


def get_dic_info(request):
    dic_pk = int(request.GET.get('dic_pk', -1))
    return_dict = get_dic_info_object({'target_pk': dic_pk})
    return HttpResponse(json.dumps(return_dict))


def mdict_index(request):
    query = request.GET.get('query', '')
    is_mb = is_mobile(request)
    return render(request, 'mdict/index.html', {'query': query, 'is_mobile': is_mb, 'type': 'index'})


def wordcloud(request):
    return render(request, 'mdict/wordcloud.html')


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
            file_path = os.path.join(BASE_DIR, file)
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
    query = request.GET.get('query', '')
    is_mb = is_mobile(request)
    return render(request, 'mdict/es-index.html', {'query': query, 'type': 'es', 'is_mobile': is_mb})


def mdict_dic(request):
    dic_pk = int(request.GET.get('dic_pk', -1))
    if dic_pk == -1:
        dics = MdictDic.objects.all().order_by('mdict_priority')
        if len(dics) > 0:
            dic_pk = dics[0].pk
    dic_name = MdictDic.objects.get(pk=dic_pk).mdict_name
    query = request.GET.get('query', '')
    is_mb = is_mobile(request)
    return render(request, 'mdict/dic.html',
                  {'dic_pk': dic_pk, 'name': dic_name, 'query': query, 'type': 'dic', 'is_mobile': is_mb})


def bujianjiansuo(request):
    return render(request, 'mdict/bujian.html')


def get_dic_group(request):
    dic_group = MdictDicGroup.objects.all()
    r_list = []
    for g in dic_group:
        r_list.append((g.pk, g.dic_group_name))
    return HttpResponse(json.dumps(r_list))


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
            f = -1

            for i in range(0, len(return_sug)):
                temp_str = return_sug[i].lower()
                # 对查询提示进行重排，将和query相等的词条设置位置第一
                # 1相等，2半角转化后相等，3去掉全角和半角空格后相等, 4stripkey后相等
                # 5繁简转化后相等
                if temp_str.find(query.lower()) == 0 or temp_str.find(q2b.lower()) == 0 \
                        or temp_str.find(query.lower().replace(' ', '').replace('　', '')) == 0 \
                        or temp_str.find(regp.sub('', query.lower())) == 0:
                    f = i
                    break
                elif not is_en_func(query):
                    q_s = t2s.convert(query)
                    q_t = s2t.convert(query)
                    if temp_str.find(q_s) == 0 or temp_str.find(q_t) == 0:
                        f = i
                        break

            if f == -1:
                t_list = return_sug[:sug_num]
            else:
                t_list = (return_sug[f:] + return_sug[:f])[:sug_num]

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
