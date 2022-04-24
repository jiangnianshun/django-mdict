import json
import os
import re
import time
from urllib.parse import quote

from base.base_sys import split_os_path, find_os_path
from base.base_utils import is_number, ROOT_DIR

history_path = os.path.join(ROOT_DIR, 'history.dat')


def set_mdict_path():
    tmdict_path = os.path.join('media', 'mdict', 'doc')
    tmdict_path_json = os.path.join(ROOT_DIR, 'mdict_path.json')
    tmdict_root_path = os.path.join(ROOT_DIR, tmdict_path)
    taudio_path = os.path.join(ROOT_DIR, 'media', 'mdict', 'audio')

    tmdict_path_list = []
    taudio_path_list = []

    if os.path.exists(tmdict_path_json):
        with open(tmdict_path_json, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                tmdict_path_list.extend(data['mdict_path'])
                taudio_path_list.extend(data['audio_path'])
            except Exception:
                pass
    else:
        con = {'mdict_path': [], 'audio_path': []}
        with open(tmdict_path_json, 'w', encoding='utf-8') as f:
            json.dump(con, f, indent=4)
        os.chmod(tmdict_path_json, 0o777)

    tmdict_path_list.append(tmdict_root_path)

    for p in tmdict_path_list:
        t = False
        if os.path.exists(p):
            p = p
        else:
            if len(p) > 1 and p[0] == '~':
                p = os.path.join(os.path.expanduser('~'), p[2:])
                if not os.path.exists(p):
                    p = None
            else:
                p = None

        if p is not None:
            for root, dirs, files in os.walk(p):
                for file in files:
                    if file.lower().endswith('.mdx') or file.lower().endswith('.zim'):
                        tmdict_root_path = p
                        t = True
                        break
                if t:
                    break
        if t:
            break
    for p in taudio_path_list:
        t = False
        if os.path.exists(p):
            p = p
        else:
            if len(p) > 1 and p[0] == '~':
                p = os.path.join(os.path.expanduser('~'), p[2:])
                if not os.path.exists(p):
                    p = None
            else:
                p = None

        if p is not None:
            # for root, dirs, files in os.walk(p):
            #     for file in files:
            #         if file.lower().endswith('.mdd'):
            #             taudio_path = p
            #             t = True
            #             break
            #     if t:
            #         break

            # 遍历深度1
            for file in os.listdir(p):
                file_path = os.path.join(p, file)
                if os.path.isfile(file_path):
                    if file.lower().endswith('.mdd'):
                        taudio_path = p
                        t = True
                        break
                # else:
                #     for file2 in os.listdir(file_path):
                #         file2_path = os.path.join(file_path, file2)
                #         if os.path.isfile(file2_path):
                #             if file2.lower().endswith('.mdd'):
                #                 taudio_path = p
                #                 t = True
                #                 break
        if t:
            break
    return tmdict_root_path, taudio_path, tmdict_path_list, taudio_path_list


mdict_root_path, audio_path, mdict_path_list, audio_path_list = set_mdict_path()

reg = r'^\.+(\\|/)'
regp = re.compile(reg)


def replace_res_name(res_name):
    res_name = regp.sub('', res_name)
    if res_name[0] == "'" or res_name[0] == "'":
        res_name = res_name[1:]
    if res_name[-1] == "'" or res_name[-1] == "'":
        res_name = res_name[:-1]
    # 在html中href是用/，在mdd中文件名用\，因此这里要替换。
    # res_name = res_name.strip()
    # Concise Oxford English Dictionary and Thesaurus中部分图片名前后有不可见字符\1E和\1F干扰，需要去掉。strip后可能为空字符串。
    if res_name[0] != '/' and res_name[0] != '\\':
        res_name = '/' + res_name
    res_name = res_name.replace('/', '\\')
    return res_name


def replace_res_name21(res_name):
    if res_name[0] == "'" or res_name[0] == "'":
        res_name = res_name[1:]
    if res_name[-1] == "'" or res_name[-1] == "'":
        res_name = res_name[:-1]
    if res_name.startswith('../'):
        res_name = res_name[3:]
    elif res_name.startswith('/'):
        res_name = res_name[1:]
    return res_name


def replace_res_name2(res_name):
    while True:
        res_name = replace_res_name21(res_name)
        if not res_name.startswith('../'):
            break
    return res_name


is_local = False


def set_media_is_local():
    global is_local
    if ROOT_DIR == '/code':
        # 当前在docker中运行
        is_local = False
    else:
        path1_dict = split_os_path(mdict_root_path)
        local_mdict_media = os.path.join(ROOT_DIR, 'media', 'mdict', 'doc')
        path2_dict = split_os_path(local_mdict_media)

        ab1 = path1_dict['absolute']
        ab2 = path2_dict['absolute']

        if ab1 == '' and ab2 != '':
            is_local = False
        elif ab1 != '' and ab2 == '':
            is_local = False
        elif ab1 != '' and ab2 != '':
            if ab1 != ab2:
                is_local = False

        path1 = path1_dict['path']
        path2 = path2_dict['path']

        s, e = find_os_path(path1, path2)
        if s == -1:
            is_local = False
        else:
            is_local = True


set_media_is_local()


def get_m_path(mdx, enable_quote=True):
    m_path = ''
    mdict_path_dict = split_os_path(mdict_root_path)
    mdict_path_t = mdict_path_dict['path']

    mdx_path_dict = split_os_path(mdx.get_fpath())
    mdx_path = mdx_path_dict['path']

    s, e = find_os_path(mdx_path, mdict_path_t)
    # e已经+1了
    if s > -1:
        t_path = mdx_path[e:-1]
        m_path = '/'.join(t_path)
    if enable_quote:
        return quote(m_path)
    else:
        return m_path


def write_to_history(query):
    time_str = time.strftime("%Y.%m.%d:%H:%M:%S", time.localtime(time.time()))
    history_str = time_str + '\t' + query + '\n'
    if os.path.exists(history_path):
        try:
            with open(history_path, 'a', encoding='utf-8') as f:
                f.write(history_str)
        except Exception as e:
            print(e)
    else:
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                f.write(history_str)
        except Exception as e:
            print(e)


def get_history_file():
    file_list = []
    for file in os.listdir(ROOT_DIR):
        if file.startswith('history.dat') and file != 'history.dat':
            file_list.append(file)

    file_list.sort(key=lambda x: int(x.split('.')[2]))
    if os.path.exists(os.path.join(ROOT_DIR, 'history.dat')):
        file_list.append('history.dat')
    return file_list


def rename_history():
    if os.path.exists(history_path) and os.path.getsize(history_path) / (1024 * 1024) > 1:
        try:
            max_num = 0
            for file in os.listdir(ROOT_DIR):
                if file.startswith('history.dat') and file != 'history.dat':
                    file_split = file.split('.')
                    if len(file_split) == 3:
                        if is_number(file_split[2]):
                            tmp_num = int(file_split[2])
                            if tmp_num > max_num:
                                max_num = tmp_num
            os.rename(history_path, history_path + '.' + str(max_num + 1))
        except Exception as e:
            print(e)


def compare_time(time1, time2):
    try:
        s_time = time.mktime(time.strptime(time1, '%Y-%m-%d'))
        e_time = time.mktime(time.strptime(time2, '%Y-%m-%d'))
        return int(s_time) - int(e_time)
    except Exception as e:
        return 0


def get_dic_attrs(dic):
    return dic.pk, dic.mdict_name, dic.mdict_file, dic.mdict_priority


def check_xapian():
    # 是否已安装xapian
    try:
        import xapian
        database = xapian.Database()
    except Exception:
        return False

    return True


def clear_duplication(record_list):
    # 查询coaling station,enwiki-p1指向fuelling station，enwiki-p3指向Fuelling station，最后是重复的词条，因此这里比较f_pk,f_p1,f_p2，如果相同，说明重复
    # 其2是简繁查询，有的词典自带简繁转化，因此查一遍简，再查一遍繁，合并，导致结果重复
    for i in range(len(record_list) - 1, -1, -1):
        mdx_i = record_list[i]
        i_pk = mdx_i.f_pk
        i_p1 = mdx_i.f_p1
        i_p2 = mdx_i.f_p2
        d_list = []
        if i_pk != -1:
            for j in range(len(record_list) - 1, -1, -1):
                mdx_j = record_list[j]
                j_pk = mdx_j.f_pk
                j_p1 = mdx_j.f_p1
                j_p2 = mdx_j.f_p2
                if i_pk == j_pk and i_p1 == j_p1 and i_p2 == j_p2:
                    d_list.append(j)
        if len(d_list) > 1:
            del record_list[i]
    return record_list
