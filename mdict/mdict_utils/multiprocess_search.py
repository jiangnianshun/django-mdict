import multiprocessing

from base.base_func import print_log_info
from .data_utils import get_or_create_dic
from .decorator import loop_mdict_list, inner_object
from .init_utils import init_vars
from .mdict_config import get_config_con
from .multibase import multi_search_mdx


def multiprocess_search_sug(n, required, group):
    return multi_search_mdx(n, required, group, is_mdx=False)


def multiprocess_search_mdx(n, required, group):
    return multi_search_mdx(n, required, group)


cpunums = get_config_con('process_num')


def create_pool():
    print_log_info('creating multiprocessing pool. process number is ' + str(cpunums) + '.')
    return multiprocessing.Pool(processes=cpunums)


def terminate_pool(pool):
    print_log_info('terminating multiprocessing pool.')
    if pool is not None:
        pool.terminate()


def check_pool_recreate(pool):
    # 重建进程池
    if init_vars.need_recreate:
        terminate_pool(pool)
        pool = create_pool()
        print_log_info('recreating multiprocessing pool success.')
        init_vars.need_recreate = False
    return pool


@loop_mdict_list()
class loop_create_model_object(inner_object):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        get_or_create_dic(dict_file)


def loop_create_model():
    global pool
    terminate_pool(pool)
    loop_create_model_object({})
    pool = create_pool()


pool = create_pool()
