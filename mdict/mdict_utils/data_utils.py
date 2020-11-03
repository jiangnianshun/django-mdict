from base.base_func import print_log_info
from django.core.exceptions import AppRegistryNotReady

try:
    from mdict.models import MdictDic
except AppRegistryNotReady as e:
    print(e)


def get_all_dic():
    return MdictDic.objects.all()


def get_or_create_dic(dict_file):
    try:
        dic = MdictDic.objects.get(mdict_file=dict_file)
    except MdictDic.DoesNotExist as e:
        print(e)
        print_log_info('find new mdict, add MdicDic to database.' + dict_file, 2)
        dic = MdictDic.objects.create(mdict_name=dict_file, mdict_file=dict_file)
    except Exception as e:
        print(e)
        dic = None
    #     多线程同时添加很多词典，操作sqlite3时会出错，后面再处理

    return dic
