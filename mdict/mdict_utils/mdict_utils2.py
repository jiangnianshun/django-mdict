import collections
import os
import threading
import time

from base.base_config import set_cpu_num, get_cpu_num
from base.base_utils import print_log_info, guess_mime
from mdict.mdict_utils.mdict_utils import check_xapian
from mdict.readlib.src.readmdict import MDD, MDX
from mdict.readlib.src.readzim import ZIMFile


def get_mdict_dict(tmdict_root_path):
    g_id = 0

    m_dict = collections.OrderedDict()
    idx_list = []
    zim_list = []
    # 词典结尾是mdx或MDX
    # ntfs下文件名不区分大小写，但ext4下区分大小写

    for root, dirs, files in os.walk(tmdict_root_path):
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
                            print_log_info([mdd_path, 'mdd loading failed', e])

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
                    print_log_info([mdx_path, 'mdx loading failed', e])

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


class MdictItem:
    def __init__(self, mdx, mdd_list, g_id, icon, num):
        self.mdx = mdx
        self.mdd_list = mdd_list
        self.g_id = g_id
        self.icon = icon
        self.num = num