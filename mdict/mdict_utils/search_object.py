# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 11:41:22 2019

@author: jiang
"""
import os
import re
import imghdr
from PIL import Image
from io import BytesIO
from urllib.parse import quote

from django.core.exceptions import AppRegistryNotReady

try:
    from mdict.models import MdictDic
    from mdict.serializers import mdxentry
except AppRegistryNotReady:
    pass

from .init_utils import init_vars
from .mdict_func import replace_res_name, is_local, get_m_path
from .decorator import search_exception
from base.base_func import guess_mime

# 超链接href包含sound://,entry://,file://,http://,https://，data:开头是base64，mailto:开头是邮件,javascript:脚本，#开头可能是锚点，www.开头可能是网址，这两个当在mdd中查询不存在时不处理。
reg = r'([ <\n])((src=("|\'| )*)|(href=("|\'| )*))(?!entry://)(?!sound://)(?!http://)(?!https://)(?!data:)(?!mailto:)(?!javascript:)(file://)*([^"\'>]+)(["\' >])'
regp = re.compile(reg, re.IGNORECASE)

reg2 = r'(url\(["|\']*)(?!http://)(?!https://)(?!data:)([^"\'\(\)]+)(["|\']*\))'
reg2p = re.compile(reg2)

excssreg = r'(href=")([\w\s-]+\.css")'
excssregp = re.compile(excssreg)

dotreg = r'^\.+'
dotregp = re.compile(dotreg)

scriptreg = r'<script.*?>'
scriptregp = re.compile(scriptreg)

values_list = init_vars.mdict_odict.values()


class SearchObject:
    def __init__(self, mdx, mdd_list, dic, required, **extra):
        self.dic = dic
        self.dic_id = dic.pk
        self.dic_name = dic.mdict_name
        self.dic_file = dic.mdict_file
        self.prior = dic.mdict_priority

        if isinstance(required, list):
            self.required = required
            self.query = required[0]
        elif isinstance(required, str):
            self.required = []
            self.query = required
        else:
            raise Exception('error query type')

        self.mdx = mdx
        self.mdd = mdd_list
        self.mdd_exist = False
        self.g_id = extra.get('g_id')

        self.f_p1 = -1
        self.f_p2 = -1
        self.f_pk = -1

        self.cmp = []
        self.result_list = []

        if len(self.mdd) > 0:
            self.mdd_exist = True

        self.m_path = get_m_path(self.mdx)

    @search_exception()
    def search_sug_required(self, num):
        return self.mdx.look_up_sug_required(self.required, num)

    @search_exception()
    def search_sug_entry(self, num):
        return self.mdx.look_up_sug(self.query, num)

    @search_exception()
    def search_list_entry(self, p1, p2, num, direction):
        return self.mdx.look_up_list(p1, p2, num, direction)

    def get_len(self):
        return self.mdx.get_len()

    @search_exception()
    def search_key(self, entry):
        f = open(self.mdx.get_fpath(), 'rb')
        result_list = self.mdx.look_up_key(entry, f)
        if not f.closed:
            f.close()
        return result_list

    @search_exception({})
    def get_header(self):
        header = self.mdx.header
        if 'Description' in header.keys():
            header['Description'] = self.substitute_record(header['Description'])

        r_h = {}
        for k in sorted(header):
            r_h.update({k: header[k]})
        return r_h

    @search_exception('')
    def search_record(self, s, e):
        f = open(self.mdx.get_fpath(), 'rb')
        record = self.mdx.look_up_record(s, e, f)
        if not f.closed:
            f.close()
        self.cmp.append(s)
        record = self.substitute_record(record)
        return record

    def substitute_record(self, record):
        if record == '':
            return ''

        if record.find('@@@LINK') == 0:  # 处理@@@LINK连接
            record = self.substitute_mdx_link(record)
        if self.mdd_exist:  # 处理图片，css和js的超链接
            record = regp.sub(self.substitute_hyper_link, record)
        else:
            record = self.check_external_css(record)

        record = scriptregp.sub(self.add_async_to_script, record)
        # Theoi Greek Mythology, 2019词条中含有外链到google的script，导致加载等待，因此设置为async。
        record = self.check_same_name_css_js(record)
        record = self.check_same_name_font(record)

        return record

    def add_async_to_script(self, matched):
        m = matched.group(0)
        if m.find('http') > -1 and m.find('async') == -1:
            return m[:len(m) - 1] + ' async>'
        else:
            return m

    def substitute_same_name_path(self, ext):
        if is_local:
            t_path = '/' + self.m_path + '/' + self.mdx.get_fname() + '.' + ext
        else:
            t_path = '/mdict/exfile/?path=' + self.m_path + '/' + quote(self.mdx.get_fname()) + '.' + ext
        return t_path

    def check_same_name_css_js(self, record):  # 加载同名css和js
        base_path = self.mdx.get_fpath()
        js_path = base_path[:-3] + 'js'
        css_path = base_path[:-3] + 'css'

        if os.path.exists(js_path):
            js_static = self.substitute_same_name_path('js')
            js_link = '<script src="' + js_static + '"></script>'
            record = js_link + record

        if os.path.exists(css_path):
            # if record.find(self.mdx.get_fname() + '.css') == -1:
            css_static = self.substitute_same_name_path('css')
            css_link = '<link href = "' + css_static + '" rel = "stylesheet" >'
            record = css_link + record
        return record

    def check_same_name_font(self, record):  # 加载同名字体
        global css_prefix
        mdx_path = self.mdx.get_fpath()
        ttf_path = mdx_path[:len(mdx_path) - 3] + 'ttf'
        woff_path = mdx_path[:len(mdx_path) - 3] + 'woff'

        ttf_name = os.path.basename(ttf_path)
        woff_name = os.path.basename(woff_path)

        css_prefix = '''<style>
        @font-face {{
        font-family: "{font_name}";
        src: url({url});
        font-display:swap;
        }}
        *{{font-family:"{font_name}"}}
        </style>
        '''

        if os.path.exists(ttf_path):
            if record.find(ttf_name) == -1:
                font_path = self.substitute_same_name_path('ttf')
                css_prefix = css_prefix.format(font_name=ttf_name.split('.')[0], url=font_path)
                return css_prefix + record
        elif os.path.exists(woff_path):
            if record.find(woff_name) == -1:
                font_path = self.substitute_same_name_path('woff')
                css_prefix = css_prefix.format(font_name=woff_name.split('.')[0], url=font_path)

                return css_prefix + record

        return record

    @search_exception()
    def search_mdx_required(self):
        # 查询一组词
        result_dict = self.mdx.look_up_required(self.required)
        self.f_pk = self.dic.pk
        r_list = []
        t_list = []
        for key in result_dict.keys():
            self.query = key
            self.result_list = result_dict[key]
            for rt in self.result_list:
                self.f_p1 = rt[2]
                self.f_p2 = rt[3]
                self.cmp.clear()
                record = self.substitute_record(rt[5])
                if record != '' and (self.f_p1, self.f_p2) not in t_list:
                    # 这里self.f_p2应该是不正确的，可能需要将自身的r_p1,r_p2也写入rsult_list中
                    t_list.append((self.f_p1, self.f_p2))
                    r_list.append(
                        mdxentry(self.dic_name, rt[4], record, self.prior, self.dic.pk, self.f_pk, self.f_p1,
                                 self.f_p2))
        return r_list

    @search_exception()
    def search_mdx_entry(self):
        # 查询一个词
        result_list = self.mdx.look_up(self.query)
        self.result_list = result_list
        # result_list 0:start,1:end,2:r_p1,3:r_p2:4:entry,5:record

        self.f_pk = self.dic.pk
        r_list = []
        for rt in result_list:
            self.f_p1 = rt[2]
            self.f_p2 = rt[3]
            self.cmp.clear()
            record = self.substitute_record(rt[5])
            if record != '':
                # 这里self.f_p2应该是不正确的，可能需要将自身的r_p1,r_p2也写入rsult_list中
                r_list.append(
                    mdxentry(self.dic_name, rt[4], record, self.prior, self.dic.pk, self.f_pk, self.f_p1, self.f_p2))

        # 英文维基part3查back substitution结果是@@@LINK=Triangular matrixForward and back substitution，
        # LINK指向词条不存在时原样返回

        return r_list

    @search_exception(('', ''))
    def search_mdd(self):
        res_content = ''
        mime_type = ''
        for mdd in self.mdd:
            r_list = mdd.look_up(self.query)
            if len(r_list) > 0:
                res_content = r_list[0][5]
                f_name = r_list[0][4]
                mime_type = guess_mime(f_name)
                break
        if self.query.endswith('.spx'):
            mime_type = 'audio/speex'

        if mime_type is not None:
            if 'css' in mime_type:
                res_content = reg2p.sub(self.substitute_css_link,
                                        res_content.decode(self.mdx.get_encoding(), errors='replace'))

            if mime_type.startswith('image/'):
                # 判断图片真实类型
                img_type = imghdr.what(None, res_content)
                if img_type is not None:
                    mime_type = 'image/' + img_type

            if mime_type == 'image/tiff':
                # tiff转png
                im = Image.open(BytesIO(res_content))
                temp = BytesIO()
                im.save(temp, format="png")
                res_content = temp.getvalue()

        return res_content, mime_type

    def check_external_css(self, record):
        # 如果没有mdd且有css文件，直接修改css文件超链接。
        # 当词库位置在服务器本地时，直接替换链接，如果在网站外，调用get_css返回文件内容。
        if is_local:
            record = excssregp.sub(self.substitute_css_path, record, 1)
            # 替换css样式地址，这里只替换1次，有含有多个外置css的词典吗？？？
        else:
            record = excssregp.sub(self.substitute_css_path_2, record, 1)
        return record

    def substitute_css_path(self, matched):
        return matched.group(1) + '/' + self.m_path + '/' + matched.group(2)

    def substitute_css_path_2(self, matched):
        return matched.group(1) + '/mdict/exfile/?path=' + self.m_path + '/' + matched.group(2)

    # 处理LINK指向的词条内容还是LINK的情况
    # 有两种情况：
    # 1：LINK指向的词条在本mdx中
    #   1.1：LINK指向的词条stripkey后和res_name stripkey后相同，即指向的词条在result_list中，此时查找result_list剩下的部分。
    #        比如：英文维基part3，词条Corona virus，stripkey后为coronavirus，其link指向Coronavirus，stripkey后还是coronavirus，导致自身指向自身无穷递归。
    #   1.2：LINK指向的词条stripkey后和res_name stripkey后不相同，此时调用substitute_mdx_link()重新对本mdx进行查找。
    #        比如：大辞海军事卷的词条863计划，link到“863”计划，再link到dacihaiJS0100
    # 2：LINK指向的词条在其他的mdx中
    #    当在本mdx无法找到指向的词条时，查找同名词典的其他part。
    def substitute_mdx_link(self, record):  # 处理LINK连接
        t_record = record
        res_name = record[8:].rstrip('\n').rstrip('\r')

        if self.result_list and self.mdx.process_str_keys(res_name) == self.mdx.process_str_keys(self.query):
            result_list = self.result_list
        else:
            result_list = self.mdx.look_up(res_name)

        record = ''

        for i in range(len(result_list)):
            result = result_list[i]
            # LINK指向的词条有时不只一个，这里只取第一个，这样不一定正确，但查询link的词条时可以都显示出来，因此这里将link指向的所有重复词条都显示出来，意义不大
            if result[0] not in self.cmp:  # self.cmp记录start位置，如果start相同，说明是同一个词条。
                record = result[5]
                self.f_p1 = result[2]
                self.f_p2 = result[3]
                self.cmp.append(result[0])

                if record.find('@@@LINK') != 0:  # 如果不是LINK，说明是正文，中断。
                    break
                elif self.mdx.process_str_keys(res_name) != self.mdx.process_str_keys(
                        record[8:].rstrip('\n').rstrip('\r')):  # 如果是新LINK，中断。
                    break

        if record.find('@@@LINK') == 0:
            record = self.substitute_mdx_link(record)

        if record == '':
            record = self.search_dic_group(res_name)
        if record == '':
            # 比如英文wiki-part1的(词条指向Bracket Parentheses，但该词条在所有part中都不存在，此时返回record原样。
            return t_record
        return record

    def search_dic_group(self, res_name):  # 同组词典查询
        # 比如英文维基词典分为多个part，某个part里的单词LINK指向的单词位于另一个part中，导致在本part中查询不到，此时查询其他part。
        record = ''
        for item in values_list:
            mdx = item.mdx
            g_id = item.g_id
            if self.g_id == g_id and mdx.get_fpath() != self.mdx.get_fpath():
                result_list = mdx.look_up(res_name)
                temp_cmp = []
                flag = False
                for i in range(len(result_list)):
                    result = result_list[i]
                    if result[0] not in temp_cmp:
                        record = result[5]
                        temp_cmp.append(result[0])

                        self.f_p1 = result[2]
                        self.f_p2 = result[3]
                        self.f_pk = MdictDic.objects.get(mdict_file=mdx.get_fname()).pk
                        if record.find('@@@LINK') != 0:  # 如果不是LINK，说明是正文，中断。
                            flag = True
                            break
                        else:
                            new_res_name = record[8:].rstrip('\n').rstrip('\r')
                            if mdx.process_str_keys(res_name) != mdx.process_str_keys(new_res_name):  # 如果是新LINK，中断。
                                record = self.search_dic_group(new_res_name)
                                if mdx.header['Compact'] == 'Yes' and mdx._stylesheet:
                                    record = mdx.substitute_stylesheet(record)
                                flag = True
                                break
                if flag:
                    break
        return record

    def substitute_css_link(self, matched):
        res_name = dotregp.sub('', matched.group(2))
        res_name = replace_res_name(res_name)

        start, end = -1, -1

        for m in self.mdd:
            f = open(m.get_fpath(), 'rb')
            result_list = m.look_up_key(res_name, f)

            if len(result_list) > 0:
                start = result_list[0][0]
                end = result_list[0][1]
                # 这里后面再处理
                break

        if start == -1:
            if res_name[0] == '\\':
                res_name = res_name[1:]
            if res_name[0] == '#' or res_name.startswith('www.'):
                return matched.group(0)
            if is_local:
                return str(matched.group(1)) + '/' + self.m_path + '/' + str(res_name) + str(matched.group(3))
            else:
                return str(matched.group(1)) + '/mdict/exfile/?path=' + self.m_path + '/' + \
                       str(res_name) + str(matched.group(3))
        # 浏览器会将反斜杠自动替换成斜杠，因此这里要对url进行编码。
        return str(matched.group(1)) + '/mdict/' + str(self.dic_id) + '/' + quote(str(res_name)) + \
               str(matched.group(3))

    def substitute_hyper_link(self, matched):  # 处理html词条，获取图片和css
        # 需不需要返回www.开头但没有http和https前缀的匹配
        matched_text = matched.group(0)
        if matched_text.find('.') == -1:
            return matched_text
        # 对于没有扩展名的不作处理，vocabulary2020查artefact有800多隐藏的连接，全部替换耗时6秒。

        res_name = replace_res_name(matched.group(8))

        start, end = -1, -1
        for m in self.mdd:
            f = open(m.get_fpath(), 'rb')
            result_list = m.look_up_key(res_name, f)
            if len(result_list) > 0:
                start = result_list[0][0]
                end = result_list[0][1]
                # 这里后面再处理
                break

        temp_1 = matched.group(4)
        temp_2 = matched.group(6)
        temp_3 = matched.group(9)
        delimiter_l, delimiter_r = '', '"'

        if temp_1 == '\'' or temp_2 == '\'':
            delimiter_r = '\''
        elif temp_1 is None and temp_2 is None:
            delimiter_l = '"'

        if temp_3[-1] == '>':
            delimiter_r += '>'

        if start == -1:
            if res_name[0] == '\\':
                res_name = res_name[1:]
            if res_name == '':
                return matched_text
            if res_name[0] == '#' or res_name.startswith('www.'):
                return matched_text
            if is_local:
                return str(matched.group(1)) + str(matched.group(2)) + delimiter_l + '/' + self.m_path + '/' + \
                       str(res_name) + delimiter_r
            else:
                return str(matched.group(1)) + str(matched.group(2)) + \
                       delimiter_l + '/mdict/exfile/?path=' + self.m_path + '/' + str(res_name) + delimiter_r
        # 浏览器会将反斜杠自动替换成斜杠，因此这里要对url进行编码。

        return str(matched.group(1)) + str(matched.group(2)) + delimiter_l + \
               str(self.dic_id) + '/' + quote(str(res_name)) + delimiter_r
