import collections
import pickle
import threading
import time
import os

from base.base_func import print_log_info, guess_mime, ROOT_DIR
from base.sys_utils import get_sys_name
from base.base_config import set_cpu_num, get_cpu_num
from .mdict_func import rename_history, check_xapian


try:
    from mdict.readlib.lib.readzim import ZIMFile
except ImportError as e:
    print_log_info('loading readzim lib failed!', 1)
    from mdict.readlib.src.readzim import ZIMFile

try:
    from mdict.readlib.lib.readmdict import MDX, MDD
except ImportError as e:
    print_log_info('loading readmdict lib failed!', 1)
    from mdict.readlib.src.readmdict import MDX, MDD

from .mdict_func import mdict_root_path, audio_path

pickle_file_path = os.path.join(ROOT_DIR, '.' + get_sys_name() + '.cache')
change_file_path = os.path.join(ROOT_DIR, '.' + get_sys_name() + '.dat')
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


init_vars = initVars()

sound_list = []


class MdictItem:
    def __init__(self, mdx, mdd_list, g_id, icon, num):
        self.mdx = mdx
        self.mdd_list = mdd_list
        self.g_id = g_id
        self.icon = icon
        self.num = num


img_type = ['jpg', 'jpeg', 'png', 'webp', 'gif']


def get_mdict_dict():
    g_id = 0

    m_dict = collections.OrderedDict()
    idx_list = []
    zim_list = []
    # 词典结尾是mdx或MDX
    # ntfs下文件名不区分大小写，但ext4下区分大小写

    for root, dirs, files in os.walk(mdict_root_path):
        for file in files:
            if file.lower().endswith('.mdx'):
                f_name = file[:file.rfind('.')]

                mdx_path = os.path.join(root, file)

                mdd_list = []
                for f in files:
                    if f.lower().endswith('.mdd') and f.startswith(f_name):
                        f2_name = f[:f.rfind('.')]
                        if f2_name != f_name:
                            if f2_name + '.mdx' in files:
                                continue
                        mdd_path = os.path.join(root, f)
                        try:
                            mdd_list.append(MDD(mdd_path))
                        except Exception as e:
                            print_log_info([f_name, 'mdd loading failed', e])

                if mdx_path.find('.part') != -1:
                    for item in m_dict.values():
                        x = item.mdx
                        g = item.g_id
                        if x.get_fpath().find('.part'):
                            x_fname = os.path.basename(x.get_fpath())
                            if x_fname[:x_fname.rfind('.part')] == f_name[:f_name.rfind('.part')]:
                                g_id = g
                                break

                icon = 'none'
                for f in files:
                    if f.startswith(f_name):
                        mime_type = guess_mime(f)
                        if mime_type is not None and mime_type.startswith('image'):
                            if f[:f.rfind('.')] == f_name:
                                icon = f.split('.')[-1]
                                break
                try:
                    mdx = MDX(mdx_path)
                    m_dict.update({f_name: MdictItem(mdx, tuple(mdd_list), g_id, icon, mdx.get_len())})
                except Exception as e:
                    print_log_info([f_name, 'mdx loading failed', e])

                g_id += 1
            elif file.lower().endswith('.zim'):
                f_name = file[:file.rfind('.')]
                zim_path = os.path.join(root, file)
                zim = ZIMFile(zim_path, encoding='utf-8')
                m_dict.update({f_name: MdictItem(zim, [], -1, 'none', len(zim))})
                zim_list.append(zim)

                idx_list.append((root, zim))

    if idx_list and check_xapian():
        # 抽取zim内置索引
        tdx = threading.Thread(target=extract_index, args=(idx_list,))
        tdx.start()

    return m_dict, zim_list


def init_zim_list():
    global init_vars
    if not init_vars.zim_list:
        for key in init_vars.mdict_odict.keys():
            mdx = init_vars.mdict_odict[key].mdx
            if mdx.get_fpath().endswith('.zim'):
                init_vars.zim_list.append(mdx)


def extract_index(idx_list):
    t1 = time.perf_counter()
    for root, zim in idx_list:
        extract_index_from_zim(root, zim)
    t2 = time.perf_counter()
    print_log_info('all indexes extracting completed.', start=t1, end=t2)


def extract_index_from_zim(root, zim):
    for url, index in zim.index_list:
        url = url.replace('/', '_')
        idx_name = zim.get_fname() + '_' + url + '.idx'
        idx_path = os.path.join(root, idx_name)
        if not os.path.exists(idx_path):
            t1 = time.perf_counter()
            zim_file = open(zim.get_fpath(), 'rb')
            idx_data = zim._get_article_by_index(zim_file, index)[0]
            zim_file.close()
            if idx_data is None:
                continue
            with open(idx_path, 'wb') as f:
                f.write(idx_data)
            t2 = time.perf_counter()
            print_log_info(['index extracting', idx_name], start=t1, end=t2)


def get_sound_list():
    if os.path.exists(audio_path):
        for s in os.listdir(audio_path):
            path = os.path.join(audio_path, s)
            dot = path.rfind('.')
            f_type = path[dot + 1:]
            if f_type == 'mdd':
                sound_list.append(MDD(path))


def read_pickle_file(path):
    with open(path, 'rb') as f:
        try:
            pickle_list = pickle.load(f)
        except Exception:
            pickle_list, zim_list = get_mdict_dict()
            write_pickle_file(path)
    return pickle_list


def write_pickle_file(path):
    with open(path, 'wb') as f:
        pickle.dump(init_vars.mdict_odict, f)
    os.chmod(path, 0o777)


def load_cache():
    init_vars.mdict_odict = read_pickle_file(pickle_file_path)
    r = False
    if len(init_vars.mdict_odict) > 0:
        p = list(init_vars.mdict_odict.values())[0].mdx.get_fpath()
        if p[0] == '/':
            if get_sys_name() == 'Windows':
                r = True
        else:
            if get_sys_name() == 'Linux':
                r = True
    else:
        r = True

    if r:
        init_vars.mdict_odict, init_vars.zim_list = get_mdict_dict()
        if len(init_vars.mdict_odict) > 0:
            write_cache()

    init_vars.mdict_odict, init_vars.indicator = sort_mdict_list(init_vars.mdict_odict)  # 生成indicator


def write_cache():
    write_pickle_file(pickle_file_path)


# indicator = []


def sort_mdict_list(t_list):
    sorted(t_list.items(), key=lambda k: k[1].num)
    indicator = []
    set_cpu_num(len(t_list))
    cnum = get_cpu_num()

    for i in range(cnum):
        indicator.append(list())

    n = 0
    inc = True

    for k, v in t_list.items():
        indicator[n].append(k)

        if inc:
            n += 1
        else:
            n -= 1
        if n >= cnum:
            inc = False
            n = cnum - 1
        elif n < 0:
            inc = True
            n = 0

    return t_list, indicator


def read_change():
    try:
        with open(change_file_path, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception:
        return None


def write_change(data):
    with open(change_file_path, 'wb') as f:
        pickle.dump(data, f)
    os.chmod(change_file_path, 0o777)


def check_dir_change():
    old_dir = read_change()

    if old_dir is None:
        print_log_info('change.dat not exists.')
        return True

    if old_dir['root_dir'] != mdict_root_path:
        print_log_info('mdict_root_path has changed.')
        return True

    if not os.path.exists(mdict_root_path):
        print_log_info('mdict_root_path not exists.')
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


def init_mdict_list(rewrite_cache):
    global init_vars
    t1 = time.perf_counter()
    print_log_info(['media root path:', mdict_root_path])
    print_log_info(['audio root path:', audio_path])

    rename_history()

    if rewrite_cache:
        init_vars.need_recreate = True

    if not os.path.exists(pickle_file_path) or os.path.getsize(pickle_file_path) == 0:
        rewrite_cache = True

    if rewrite_cache or check_dir_change():
        sound_list.clear()
        get_sound_list()

        init_vars.mdict_odict.clear()
        init_vars.mdict_odict, init_vars.zim_list = get_mdict_dict()
        init_vars.mdict_odict, init_vars.indicator = sort_mdict_list(init_vars.mdict_odict)
        t2 = time.perf_counter()
        print_log_info('initializing mdict_list', 0, t1, t2)
        write_cache()
        write_dir_change()
        print_log_info('creating cache file', 0, t2, time.perf_counter())
    else:
        get_sound_list()
        load_cache()
        init_zim_list()
        print_log_info('reading from cache file', 0, t1, time.perf_counter())

    print_log_info(['dictionary counts', len(init_vars.mdict_odict)])
    print_log_info('initializing', 0, t1, time.perf_counter())
    return init_vars
