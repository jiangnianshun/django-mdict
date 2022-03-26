from multiprocessing.pool import ThreadPool
from base.base_utils import print_log_info
from base.base_config import get_cpu_num
from mdict.mdict_utils.data_utils import get_or_create_dic
from mdict.mdict_utils.loop_decorator import loop_mdict_list, innerObject
from mdict.mdict_utils.init_utils import init_vars
from mdict.mdict_utils.multi_base import multi_search_mdx


def multithread_search_sug(n, query_list, group):
    return multi_search_mdx(n, query_list, group, is_mdx=False)


def multithread_search_mdx(n, query, group):
    return multi_search_mdx(n, query, group)


def create_thread_pool():
    cnum = get_cpu_num()
    print_log_info(['creating multithreading pool. thread number is ', cnum, '.'])
    return ThreadPool(cnum)


def terminate_threadpool(threadpool):
    print_log_info('terminating multithreading pool.')
    threadpool.terminate()


def check_threadpool_recreate(threadpool):
    # 重建进程池
    if init_vars.need_recreate:
        terminate_threadpool(threadpool)
        threadpool = create_thread_pool()
        print_log_info('recreating multithreading pool success.')
        init_vars.need_recreate = False
    return threadpool


@loop_mdict_list()
class loop_create_model_object(innerObject):
    def inner_search(self, mdx, mdd_list, g_id, icon, dict_file, dic):
        get_or_create_dic(dict_file)


def loop_create_thread_model():
    global thpool
    terminate_threadpool(thpool)
    loop_create_model_object({})
    thpool = create_thread_pool()


# thpool = create_thread_pool()
