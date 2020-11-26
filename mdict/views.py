import json
import mimetypes
import re
from urllib.parse import quote, unquote

from django.db.utils import OperationalError
from django.http import HttpResponse
from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from base.base_func import print_log_info, is_en_func, strQ2B, request_body_serialze, guess_mime
from base.base_func3 import t2s, s2t

from mdict.mdict_utils.chaizi_reverse import HanziChaizi
from mdict.mdict_utils.data_utils import get_or_create_dic, init_database
from mdict.mdict_utils.decorator import loop_mdict_list, inner_object
from mdict.mdict_utils.init_utils import init_vars, sound_list, init_mdict_list
from mdict.mdict_utils.mdict_config import *
from mdict.mdict_utils.search_object import SearchObject
from mdict.mdict_utils.search_utils import search, clear_duplication, search_bultin_dic_sug, search_mdx_sug, \
    search_revise
from base.sys_utils import check_system
from .models import MdictDic, MyMdictEntry, MdictDicGroup, MdictOnline
from .serializers import MdictEntrySerializer, MyMdictEntrySerializer, MdictOnlineSerializer
from .mdict_utils.mdict_func import mdict_root_path, is_local, get_m_path

if check_system() == 0:
    from .mdict_utils.multiprocess_search import loop_create_model
elif check_system() == 1:
    from .mdict_utils.multithread_search import loop_create_thread_model

from .mdict_utils.search_cache import sug_cache, MdictPage, key_paginator

init_database()

reg = r'[ _=,.;:!?@%&#~`()\[\]<>{}/\\\$\+\-\*\^\'"\t]'
regp = re.compile(reg)


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

        return Response(ret)

    def get_results(self, query, group):
        record_list = []
        self.is_en = False

        if is_en_func(query):
            self.is_en = True

        required = get_query_list(query)

        if required:
            record_list = search(required, group)
            for query in required:
                record_list = search_revise(query, record_list, self.is_en)
            record_list = clear_duplication(record_list)

            if len(record_list) == 0 and query.find('.htm') != -1:
                query = query[:query.find('.htm')]
                record_list = search(query, self.is_en, group)
                # 二十五史词典有些词条比如 史记_06但在超链接错误写成了史记_06.htm

            record_list.sort(key=lambda k: k.mdx_pror)

        return record_list


def get_query_list(query):
    required = []

    query = query.strip()

    if query:  # 非空字符串为True
        required.append(query)
        if not is_en_func(query):  # 繁简转化

            st_enable = get_config_con('st_enable')
            chaizi_enable = get_config_con('chaizi_enable')

            if chaizi_enable and len(query) > 1:  # 长度大于1时拆字反查
                # required.append(chaizi_search(query, group))
                result = hc.reverse_query(query)
                if result:
                    for r in result:
                        required.append(r)

            if st_enable:
                q_s = t2s.convert(query)
                q_t = s2t.convert(query)
                if q_t != query:
                    required.append(q_t)
                    if chaizi_enable and len(q_t) > 1:
                        result = hc.reverse_query(q_t)
                        if result:
                            for r in result:
                                required.append(r)
                elif q_s != query:
                    required.append(q_s)
                    if chaizi_enable and len(q_s) > 1:
                        result = hc.reverse_query(q_s)
                        if result:
                            for r in result:
                                required.append(r)
            fh_char_enable = get_config_con('fh_char_enable')
            if fh_char_enable:
                q2b = strQ2B(query)

                if q2b != query:  # 全角字符进行转换
                    required.append(q2b)
    return required


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
    if s == -1 or e == -1:
        return_list = []
    else:
        return_list = search_mdx_record_object({'query': query, 'target_pk': dic_pk, 'start': s, 'end': e})

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
                'dic_pk': dic.pk, 'dic_enable': dic.mdict_enable}
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
            rr_list = mdd.look_up(res_name)
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
    dic = MdictDic.objects.get(pk=dic_id)
    res_name = unquote(args[1]).replace('/', '\\')

    res_content = ''
    mime_type = ''

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
                .search_list_entry(self.p1, self.p2, self.num, self.direction)
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
    return render(request, 'mdict/index.html', {'query': query})


def mdict_dic(request):
    dic_pk = int(request.GET.get('dic_pk', -1))
    if dic_pk == -1:
        dics = MdictDic.objects.all().order_by('mdict_priority')
        if len(dics) > 0:
            dic_pk = dics[0].pk
    dic_name = MdictDic.objects.get(pk=dic_pk).mdict_name
    query = request.GET.get('query', '')
    return render(request, 'mdict/dic.html', {'dic_pk': dic_pk, 'name': dic_name, 'query': query})


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
    flag = request.GET.get('flag', 20)
    group = int(request.GET.get('dic_group', 0))

    if query and sug_cache.get(query, group, dic_pk) is None:
        sug = []
        t_list = []

        required = get_query_list(query)

        if required:
            if dic_pk == -1:  # index页面才需要内置词典的查询提示
                sug.extend(search_bultin_dic_sug(query))

            try:
                sug.extend(search_mdx_sug(dic_pk, required, group, flag))
            except FileNotFoundError:
                print_log_info('mdx file not found, suggestion search failed, need recache!', 2)
                init_mdict_list(True)
                sug.extend(search_mdx_sug(dic_pk, required, group, flag))
            except OperationalError as e:
                print(e)
                print_log_info('modify database failed!', 2)
                # 多进程对sqlite的读写失败，使用for循环来创建数据库
                # 当添加了多个新词典时，有时会报错django.db.utils.OperationalError: disk I/O error，原因可能是sqlite在nfs文件系统上的lock不可靠。
                if check_system() == 0:
                    loop_create_model()
                elif check_system() == 1:
                    loop_create_thread_model()
                sug.extend(search_mdx_sug(dic_pk, required, group, flag))

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
                t_list = return_sug[:flag]
            else:
                t_list = (return_sug[f:] + return_sug[:f])[:flag]

        sug_cache.put(query, group, dic_pk, t_list)

    r_list = sug_cache.get(query, group, dic_pk)

    return HttpResponse(json.dumps(r_list))


def get_external_file(request):
    path = request.GET.get('path', '')
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
    id = json.loads(request.GET.get('mdict_pk', -1))
    enable = json.loads(request.GET.get('mdict_enable', "false"))

    if id > -1:
        dic = MdictDic.objects.filter(pk=id)
        if len(dic) > 0:
            dic.update(mdict_enable=enable)
        else:
            return HttpResponse("failed")
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
        queryset = self.queryset.order_by('pk')
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
