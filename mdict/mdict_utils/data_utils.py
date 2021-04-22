import os
import html
from django.core.exceptions import AppRegistryNotReady
from django.db.utils import OperationalError as DjangoError
from sqlite3 import OperationalError as Sqlite3Error
from mdict.mdict_utils.init_utils import init_vars
from base.base_func import read_from_sqlite, ROOT_DIR

is_django = False

try:
    from mdict.models import MdictDic
    is_django = True
except AppRegistryNotReady as e:
    pass
except Exception as e:
    pass

sql3_path = os.path.join(ROOT_DIR, 'db.sqlite3')

def get_all_dic():
    if is_django:
        return MdictDic.objects.all()
    else:
        dics_dict = {}
        all_dics = read_from_sqlite(sql3_path, 'select * from mdict_mdictdic')
        for tdic in all_dics:
            if tdic[2] not in dics_dict.keys():
                dics_dict.update({tdic[2]: tdic})
        return dics_dict


def get_or_create_dic(dict_file):
    if is_django:
        dics = MdictDic.objects.filter(mdict_file=dict_file)
        if len(dics) == 0:
            dic = MdictDic.objects.create(mdict_name=dict_file, mdict_file=dict_file)
        else:
            dic = dics[0]
    else:
        dic = None

    return dic


def init_database():
    try:
        print('init database')
        update_list = []
        all_dics = MdictDic.objects.all()
        for k, v in init_vars.mdict_odict.items():
            dics = all_dics.filter(mdict_file=k)
            if len(dics) == 0:
                header = v.mdx.header
                mdict_name = k
                if 'Title' in header:
                    mdict_name = html.unescape(header['Title'].strip())
                    if not mdict_name or mdict_name == 'Title (No HTML code allowed)':
                        mdict_name = k
                print(k, mdict_name)
                obj = MdictDic(mdict_name=mdict_name, mdict_file=k)
                update_list.append(obj)
        if update_list:
            MdictDic.objects.bulk_create(update_list, batch_size=100)
            print('add new dictionary', len(update_list))
    except Sqlite3Error as e:
        print(e)
    except DjangoError as e:
        print(e)
