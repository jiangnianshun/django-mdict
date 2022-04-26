import os
import html
from django.core.exceptions import AppRegistryNotReady
from mdict.mdict_utils.init_utils import init_vars
from mdict.mdict_utils.dic_object import dicObject
from base.base_utils import exec_sqlite3, ROOT_DIR, print_log_info
from base.base_sys import check_module_import

try:
    from mdict.models import MdictDic, MdictDicGroup
except AppRegistryNotReady as e:
    pass
except Exception as e:
    pass

sql3_path = os.path.join(ROOT_DIR, 'db.sqlite3')


def get_columns():
    # 字段mdict_file顺序不能保证固定
    exec_cmd = "PRAGMA table_info(mdict_mdictdic)"
    column_list = exec_sqlite3(sql3_path, exec_cmd)
    tmp_dict = {}
    for column in column_list:
        tmp_dict.update({column[1]: column[0]})
    resort_dic = False
    if tmp_dict['id'] != 0 or tmp_dict['mdict_name'] != 1 or tmp_dict['mdict_file'] != 2 or \
            tmp_dict['mdict_enable'] != 3 or tmp_dict['mdict_priority'] != 4 or tmp_dict['mdict_es_enable'] != 5 or \
            tmp_dict['mdict_md5'] != 6:
        resort_dic = True
    return tmp_dict, resort_dic


column_names, column_resort = get_columns()
mdict_file_flag = column_names['mdict_file']


def resort_dics(dics):
    if len(dics) > 0:
        if column_resort:
            tmp_dics = []
            for dic in dics:
                item = (dic[column_names['id']], dic[column_names['mdict_name']], dic[column_names['mdict_file']],
                        dic[column_names['mdict_enable']], dic[column_names['mdict_priority']],
                        dic[column_names['mdict_es_enable']], dic[column_names['mdict_md5']])
                tmp_dics.append(item)
            return tmp_dics

    return dics


def convert_dics(dics):
    dics_dict = {}

    for tdic in dics:
        if tdic[mdict_file_flag] not in dics_dict.keys():
            dics_dict.update({tdic[mdict_file_flag]: tdic})
    return dics_dict


def get_all_dics():
    if check_module_import('mdict.models'):
        return MdictDic.objects.all()
    else:

        all_dics = exec_sqlite3(sql3_path, 'select * from mdict_mdictdic')
        all_dics = resort_dics(all_dics)
        dics_dict = convert_dics(all_dics)

        return dics_dict


def get_or_create_dic(dict_file, dict_name=''):
    if check_module_import('mdict.models'):
        dics = MdictDic.objects.filter(mdict_file=dict_file)
        if len(dics) == 0:
            dic = MdictDic.objects.create(mdict_name=dict_file, mdict_file=dict_file)
        else:
            dic = dics[0]
        return dic
    else:
        if dict_name == '':
            dict_name = dict_file
        exec_cmd = "insert into mdict_mdictdic (mdict_name,mdict_file,mdict_enable,mdict_priority) values (?,?,1,1)"
        exec_param = (dict_name, dict_file)
        exec_sqlite3(sql3_path, exec_cmd, exec_param)
        dics = exec_sqlite3(sql3_path, "select * from mdict_mdictdic where mdict_file=?", (dict_file,))
        if len(dics) > 0:
            dics = resort_dics(dics)
            return dicObject(*dics[0])
        else:
            return None


def check_dic_in_group(group_pk, dic_pk):
    if check_module_import('mdict.models'):
        group = MdictDicGroup.objects.filter(pk=group_pk)
        if group.count() > 0:
            dic_count = group[0].mdict_group.filter(pk=dic_pk).count()
            if dic_count > 0:
                return True
            else:
                return False
        else:
            return False
    else:
        dic_in_group = exec_sqlite3(sql3_path,
                                    'select * from mdict_mdictdicgroup_mdict_group where mdictdicgroup_id={} AND mdictdic_id={}'
                                    .format(group_pk, dic_pk))
        if len(dic_in_group) > 0:
            return True
        else:
            return False


def init_database():
    try:
        print_log_info('initializing database')
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
    except Exception as e:
        print('initializing database failed', e)
