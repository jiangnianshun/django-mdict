import json
import os
import re
from urllib.parse import quote

from base.sys_utils import split_os_path, find_os_path
from mysite.settings import BASE_DIR

mdict_path = os.path.join('media', 'mdict', 'doc')
mdict_root_path = os.path.join(BASE_DIR, mdict_path)

audio_path = os.path.join(BASE_DIR, 'media', 'mdict', 'audio')

mdict_path_list = []
audio_path_list = []

mdict_path_json = os.path.join(BASE_DIR, 'mdict_path.json')

if os.path.exists(mdict_path_json):
    with open(mdict_path_json, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            mdict_path_list.extend(data['mdict_path'])
            audio_path_list.extend(data['audio_path'])
        except Exception:
            pass
else:
    con = {'mdict_path': [], 'audio_path': []}
    with open(mdict_path_json, 'w', encoding='utf-8') as f:
        json.dump(con, f, indent=4)
    os.chmod(mdict_path_json, 0o777)

mdict_path_list.append(mdict_root_path)


def set_mdict_path():
    global mdict_root_path, mdict_path_list, audio_path_list, audio_path
    for p in mdict_path_list:
        if os.path.exists(p):
            for root, dirs, files in os.walk(p):
                t = False
                for file in files:
                    if file.lower().endswith('mdx'):
                        mdict_root_path = p
                        t = True
                        break
                if t:
                    break
    for p in audio_path_list:
        if os.path.exists(p):
            for root, dirs, files in os.walk(p):
                t = False
                for file in files:
                    if file.lower().endswith('mdd'):
                        audio_path = p
                        t = True
                        break
                if t:
                    break


set_mdict_path()

reg = r'^\.+(\\|/)'
regp = re.compile(reg)


def replace_res_name(res_name):
    res_name = regp.sub('', res_name)
    # 在html中href是用/，在mdd中文件名用\，因此这里要替换。
    if res_name[0] != '/' and res_name[0] != '\\':
        res_name = '/' + res_name
    res_name = res_name.replace('/', '\\')
    return res_name


is_local = False


def is_mdict_media_local():
    global is_local
    path1_dict = split_os_path(mdict_root_path)
    local_mdict_media = os.path.join(BASE_DIR, 'media', 'mdict', 'doc')
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


is_mdict_media_local()


def get_m_path(mdx):
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
    return quote(m_path)
