import pickle, time, collections
from base.base_func import print_log_info, guess_mime
from base.sys_utils import get_sys_name
from .mdict_config import *

print_log_info('system is ' + get_sys_name() + '.')

try:
    from mdict.readmdict.lib.readmdict_search import MDX, MDD

    print_log_info('loading readmdict_search lib.')
except ImportError as e:
    print(e)
    print_log_info(
        'loading readmdict_search lib failed! compile pyx files in mynav/mdict/readmdict/pyx/ with cython, this will speed up search.',
        1)
    from mdict.readmdict.source.readmdict_search import MDX, MDD

from .mdict_func import mdict_root_path, audio_path

pickle_file_path = BASE_DIR + os.sep + '.' + get_sys_name() + '.cache'


# 这里使用init_vars包裹mdit_list是因为，当其他模块引入mdict_list后，再修改mdict_list，其他模块引入的mdict_list没有改变，因此需要用类包裹。
class initVars:
    mdict_odict = collections.OrderedDict()
    need_recreate = False


init_vars = initVars()

sound_list = []


class MdictItem:
    def __init__(self, mdx, mdd_list, g_id, icon, file_size):
        self.mdx = mdx
        self.mdd_list = mdd_list
        self.g_id = g_id
        self.icon = icon
        self.file_size = file_size


img_type = ['jpg', 'jpeg', 'png', 'webp', 'gif']


def get_mdict_list():
    g_id = 0

    m_list = collections.OrderedDict()

    # 词典结尾是mdx或MDX
    # ntfs下文件名不区分大小写，但ext4下区分大小写

    # os.walk和os.scandir()
    for root, dirs, files in os.walk(mdict_root_path):
        for file in files:
            if file.lower().endswith('.mdx'):
                f_name = file[:file.rfind('.')]

                mdx_path = os.path.join(root, file)
                mdx_file_size = int(os.path.getsize(mdx_path) / 1000000)  # 转换成MB

                mdd_list = []
                for f in files:
                    if f.lower().endswith('.mdd') and f.startswith(f_name):
                        mdd_path = os.path.join(root, f)
                        mdd_list.append(MDD(mdd_path))

                if mdx_path.find('.part') != -1:
                    for item in m_list.values():
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
                            icon = f.split('.')[-1]
                            break

                m_list.update({f_name: MdictItem(MDX(mdx_path), tuple(mdd_list), g_id, icon, mdx_file_size)})

                g_id += 1

    return m_list


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
            pickle_list = get_mdict_list()
            write_pickle_file(path)
    return pickle_list


def write_pickle_file(path):
    with open(path, 'wb') as f:
        pickle.dump(init_vars.mdict_odict, f)


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
        init_vars.mdict_odict = get_mdict_list()
        if len(init_vars.mdict_odict) > 0:
            write_cache()

    init_vars.mdict_odict = sort_mdict_list(init_vars.mdict_odict)  # 生成indicator


def write_cache():
    write_pickle_file(pickle_file_path)


indicator = []


def sort_mdict_list(t_list):
    sorted(t_list.items(), key=lambda k: k[1].file_size)

    cpunums = get_config_con('process_num')
    for i in range(cpunums):
        indicator.append(list())

    n = 0
    for i in range(len(t_list) - 1, -1, -1):
        indicator[n].append(i)  # 改进成每列的file_size的和大概相等
        n += 1
        if n >= cpunums:
            n = 0

    return t_list


def init_mdict_list(rewrite_cache):
    global config
    t1 = time.perf_counter()

    if rewrite_cache:
        init_vars.need_recreate = True

    if not rewrite_cache and os.path.exists(pickle_file_path) and os.path.getsize(pickle_file_path) > 0:
        get_sound_list()
        load_cache()
        print_log_info('reading from cache file', 0, t1, time.perf_counter()),
    else:
        sound_list.clear()
        get_sound_list()

        init_vars.mdict_odict.clear()
        init_vars.mdict_odict = get_mdict_list()
        init_vars.mdict_odict = sort_mdict_list(init_vars.mdict_odict)
        t2 = time.perf_counter()
        print_log_info('initializing mdict_list', 0, t1, t2)
        write_cache()
        print_log_info('creating cache file', 0, t2, time.perf_counter())
        t3 = time.perf_counter()

    print_log_info('total time', 0, t1, time.perf_counter())
