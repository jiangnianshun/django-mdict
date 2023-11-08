import collections
import pickle
import time
import os

from base.base_utils import print_log_info, ROOT_DIR
from base.base_sys import get_sys_name
from mdict.mdict_utils.mdict_utils import rename_history, mdict_root_path
from mdict.mdict_utils.mdict_utils2 import get_mdict_dict, sort_mdict_list

try:
    from mdict.readlib.lib.readzim import ZIMFile
except ImportError as e:
    # print_log_info('loading readzim lib failed!', 1)
    from mdict.readlib.src.readzim import ZIMFile

try:
    from mdict.readlib.lib.readmdict import MDX, MDD
except ImportError as e:
    # print_log_info('loading readmdict lib failed!', 1)
    from mdict.readlib.src.readmdict import MDX, MDD

from .mdict_utils import audio_path

cache_dir = os.path.join(ROOT_DIR, '.cache')
if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)
pickle_file_path = os.path.join(cache_dir, f'.{get_sys_name()}.cache')
change_file_path = os.path.join(cache_dir, f'.{get_sys_name()}.dat')
uploads_path = os.path.join(ROOT_DIR, 'media', 'uploads')

if not os.path.exists(uploads_path):
    try:
        os.mkdir(uploads_path)
    except Exception as e:
        print(e)


# 这里使用init_vars包裹mdit_list是因为，当其他模块引入mdict_list后，再修改mdict_list，其他模块引入的mdict_list没有改变，因此需要用类包裹。
class initVars:
    mdict_odict = collections.OrderedDict()
    zim_list = []
    indicator = []
    need_recreate = False
    mtime = None


init_vars = initVars()

sound_list = []

img_type = ['jpg', 'jpeg', 'png', 'webp', 'gif']


def init_zim_list():
    global init_vars
    if not init_vars.zim_list:
        for key in init_vars.mdict_odict.keys():
            mdx = init_vars.mdict_odict[key].mdx
            if mdx.get_fpath().endswith('.zim'):
                init_vars.zim_list.append(mdx)


def get_sound_list():
    if os.path.exists(audio_path):
        for s in os.listdir(audio_path):
            path = os.path.join(audio_path, s)
            dot = path.rfind('.')
            f_type = path[dot + 1:]
            if f_type == 'mdd':
                sound_list.append(MDD(path))


def read_pickle_file(path, tmdict_root_path):
    with open(path, 'rb') as f:
        try:
            pickle_list = pickle.load(f)
        except Exception:
            pickle_list, zim_list = get_mdict_dict(tmdict_root_path)
            write_pickle_file(path)
    return pickle_list


def write_pickle_file(path):
    with open(path, 'wb') as f:
        pickle.dump(init_vars.mdict_odict, f)
    os.chmod(path, 0o777)


def load_cache(tmdict_root_path):
    global init_vars
    init_vars.mdict_odict = read_pickle_file(pickle_file_path, tmdict_root_path)
    r = False
    if len(init_vars.mdict_odict) > 0:
        try:
            p = list(init_vars.mdict_odict.values())[0].mdx.get_fpath()
            if p[0] == '/':
                if get_sys_name() == 'Windows':
                    r = True
            else:
                if get_sys_name() == 'Linux':
                    r = True
        except Exception as e:
            print(e)
            r = True
    else:
        r = True

    if r:
        print('rewriting cache...')
        init_vars.mdict_odict, init_vars.zim_list = get_mdict_dict(tmdict_root_path)
        if len(init_vars.mdict_odict) > 0:
            write_cache()

    init_vars.mdict_odict, init_vars.indicator = sort_mdict_list(init_vars.mdict_odict)  # 生成indicator
    init_vars.mtime = os.path.getmtime(pickle_file_path)
    return init_vars


def write_cache():
    write_pickle_file(pickle_file_path)


def read_change():
    try:
        with open(change_file_path, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception as e:
        return None


def write_change(data):
    with open(change_file_path, 'wb') as f:
        pickle.dump(data, f)
    os.chmod(change_file_path, 0o777)


def check_dir_change():
    old_dir = read_change()

    if old_dir is None:
        print_log_info('dat cache file not exists.')
        return True

    if old_dir['root_dir'] != mdict_root_path:
        print_log_info(f'mdict_root_path({mdict_root_path}) has changed.')
        return True

    if not os.path.exists(mdict_root_path):
        print_log_info(f'mdict_root_path({mdict_root_path}) is not exists.')
        return True

    files_total_num = 1
    for root, dirs, files in os.walk(mdict_root_path):
        for file in files:
            if file.lower().endswith('.mdx') or file.lower().endswith('.mdd') or file.lower().endswith('.zim'):
                mdict_path = os.path.join(root, file)
                mtime = os.path.getmtime(mdict_path)
                files_total_num += 1
                if mdict_path not in old_dir.keys():
                    print_log_info('dir change founded.')
                    return True
                if old_dir[mdict_path] < mtime:
                    print_log_info('dir change founded.')
                    return True

    if files_total_num != len(old_dir):
        print_log_info('dir change founded.')
        return True

    print_log_info('no dir change founded.')
    return False


def write_dir_change():
    new_dir = {}
    new_dir.update({'root_dir': mdict_root_path})
    for root, dirs, files in os.walk(mdict_root_path):
        for file in files:
            if file.lower().endswith('.mdx') or file.lower().endswith('.mdd') or file.lower().endswith('.zim'):
                mdict_path = os.path.join(root, file)
                mtime = os.path.getmtime(mdict_path)
                new_dir.update({mdict_path: mtime})
    write_change(new_dir)


def rewrite_cache(tmdict_root_path):
    global init_vars
    t1 = time.perf_counter()
    sound_list.clear()
    get_sound_list()

    init_vars.mdict_odict.clear()
    init_vars.mdict_odict, init_vars.zim_list = get_mdict_dict(tmdict_root_path)
    init_vars.mdict_odict, init_vars.indicator = sort_mdict_list(init_vars.mdict_odict)
    t2 = time.perf_counter()
    print_log_info('initializing mdict_list', 0, t1, t2)
    write_cache()
    write_dir_change()
    init_vars.mtime = os.path.getmtime(pickle_file_path)
    print_log_info('creating cache file', 0, t2, time.perf_counter())


def init_mdict_list():
    global init_vars, mdict_root_path
    t1 = time.perf_counter()

    rename_history()

    if check_dir_change():
        rewrite_cache(mdict_root_path)
    else:
        get_sound_list()
        load_cache(mdict_root_path)
        init_zim_list()
        print_log_info('reading from cache file', 0, t1, time.perf_counter())

    print_log_info(['media root path:', mdict_root_path])
    print_log_info(['audio root path:', audio_path])
    print_log_info(['dictionary counts', len(init_vars.mdict_odict)])

    return init_vars
