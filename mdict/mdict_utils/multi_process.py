import multiprocessing

from base.base_utils import print_log_info
from base.base_config import get_cpu_num, set_cpu_num
from mdict.mdict_utils.data_utils import get_or_create_dic
from mdict.mdict_utils.loop_decorator import loop_mdict_list, innerObject
from mdict.mdict_utils.multi_base import multi_search_mdx


# def multiprocess_search_sug(n, sug_list, group):
#     return multi_search_mdx(n, sug_list, group, is_mdx=False)


def multiprocess_search_mdx(n, query_list, group, is_mdx=True):
    return multi_search_mdx(n, query_list, group, is_mdx=is_mdx)


def create_process_pool(dic_num=-1):
    if dic_num > 0:
        set_cpu_num(dic_num)
    cnum = get_cpu_num()
    print_log_info(['creating multiprocessing pool. ( ', cnum, ')'])
    return multiprocessing.Pool(processes=cnum)


def pre_pool_search(prpool):
    # 预热，避免第一次查询等待。
    try:
        cnum = get_cpu_num()
        q_list = ((i, ['bananapie'], 0, True) for i in range(cnum))
        prpool.starmap(multiprocess_search_mdx, q_list)
    except Exception as e:
        # 当db.sqlite3不存在时，会导致django无法运行。
        print(e)


def terminate_pool(pool):
    print_log_info('terminating multiprocessing pool.')
    if pool is not None:
        pool.terminate()


# def check_pool_recreate(pool):
#     # 重建进程池
#     if init_vars.need_recreate:
#         terminate_pool(pool)
#         pool = create_process_pool()
#         print_log_info('recreating multiprocessing pool success.')
#         init_vars.need_recreate = False
#     return pool


@loop_mdict_list()
class loop_create_model_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        get_or_create_dic(dict_file)


def loop_create_model():
    global pool
    terminate_pool(pool)
    loop_create_model_object({})
    pool = create_process_pool()

# pool = create_process_pool()
