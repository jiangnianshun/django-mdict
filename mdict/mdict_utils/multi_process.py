import multiprocessing

from base.base_func import print_log_info
from .data_utils import get_or_create_dic
from .loop_decorator import loop_mdict_list, innerObject
from .init_utils import init_vars
from .mdict_config import get_cpu_num
from .multi_base import multi_search_mdx


def multiprocess_search_sug(n, sug_list, group):
    return multi_search_mdx(n, sug_list, group, is_mdx=False)


def multiprocess_search_mdx(n, query_list, group):
    return multi_search_mdx(n, query_list, group)


def create_process_pool():
    cnum = get_cpu_num()
    print_log_info(['creating multiprocessing pool. process number is ', cnum, '.'])
    return multiprocessing.Pool(processes=cnum)


def terminate_pool(pool):
    print_log_info('terminating multiprocessing pool.')
    if pool is not None:
        pool.terminate()


def check_pool_recreate(pool):
    # 重建进程池
    if init_vars.need_recreate:
        terminate_pool(pool)
        pool = create_process_pool()
        print_log_info('recreating multiprocessing pool success.')
        init_vars.need_recreate = False
    return pool


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
