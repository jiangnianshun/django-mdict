import collections
import functools
import time
from abc import abstractmethod

from mdict.models import MdictDic
from .data_utils import get_or_create_dic
from .init_utils import init_vars

values_list = init_vars.mdict_odict.values()


def loop_mdict_list(return_type=0, timer=False, digit=5):
    """
    a decorator to reduce redundant loop code
    @param return_type: 0:return list, 1:return dict, 2:return ordered dict
    @param timer: display loop running time
    @param digit: set number of decimal places
    @return:
    """

    def decorator(obj):
        @functools.wraps(obj)
        def wrapper(*args, **kwargs):
            o = obj(*args, **kwargs)
            t1 = time.perf_counter()
            if o.target_pk > -1:
                dic = MdictDic.objects.get(pk=o.target_pk)
                item = init_vars.mdict_odict[dic.mdict_file]

                mdx = item.mdx
                mdd_list = item.mdd_list
                g_id = item.g_id
                icon = item.icon

                o.inner_search(mdx, mdd_list, g_id, icon, dic.mdict_file, dic)

            else:
                for item in values_list:
                    mdx = item.mdx
                    mdd_list = item.mdd_list
                    g_id = item.g_id
                    icon = item.icon

                    dict_file = mdx.get_fname()
                    dic = get_or_create_dic(dict_file)

                    o.inner_search(mdx, mdd_list, g_id, icon, dict_file, dic)
                    if o.break_tag:
                        break
            t2 = time.perf_counter()
            if timer:
                print(obj.__name__, 'running time:', round(t2 - t1, digit))
            if return_type == 0:
                return o.inner_list
            elif return_type == 1:
                return o.inner_dict
            elif return_type == 2:
                return o.inner_odict

        return wrapper

    return decorator


class inner_object():
    def __init__(self, params={}):
        """

        @param params: put all variables in the params that you need in loop
        """
        if 'inner_odict' not in params.keys():
            self.inner_odict = collections.OrderedDict()
        if 'inner_dict' not in params.keys():
            self.inner_dict = {}
        if 'inner_list' not in params.keys():
            self.inner_list = []
        self.target_pk = -1
        self.__dict__.update(params)
        # 将字典键转为类的成员变量的变量名，字典值转为对应成员变量的值
        self.break_tag = False

    @abstractmethod
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        """
        inherit inner_object()，then add decorator loop_mdict_list，finally overwrite function inner_search().
        @param mdx: MDX file object
        @param mdd_list: MDD file object list
        @param g_id: dictionary group id
        @param icon: dictionary icon type, it is jpb, png or none.
        @param dict_file: dictionary file name, not contain extension
        @param dic: dictionary object in database
        @return: search results, it's a list or a dict, using the decorator variable return_is_dict to control it.
        """
