from multiprocessing.pool import ThreadPool
from base.base_func import print_log_info
from .data_utils import get_or_create_dic
from .decorator import loop_mdict_list, inner_object
from .init_utils import init_vars
from .mdict_config import get_config_con
from .multibase import multi_search_mdx


def multithread_search_sug(n, query, group):
    return multi_search_mdx(n, query, group, is_mdx=False)


def multithread_search_mdx(n, query, group):
    return multi_search_mdx(n, query, group)


cpunums = get_config_con('process_num')


def create_threadpool():
    print_log_info('creating multithreading pool. thread number is ' + str(cpunums) + '.')
    return ThreadPool(cpunums)


def terminate_threadpool(threadpool):
    print_log_info('terminating multithreading pool.')
    threadpool.terminate()


def check_threadpool_recreate(threadpool):
    # 重建进程池
    if init_vars.need_recreate:
        terminate_threadpool(threadpool)
        threadpool = create_threadpool()
        print_log_info('recreating multithreading pool success.')
        init_vars.need_recreate = False
    return threadpool


@loop_mdict_list()
class loop_create_model_object(inner_object):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        get_or_create_dic(dict_file)


def loop_create_thread_model():
    global thpool
    terminate_threadpool(thpool)
    loop_create_model_object({})
    thpool = create_threadpool()


thpool = create_threadpool()
