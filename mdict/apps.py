import os
import subprocess
from django.apps import AppConfig

from base.base_utils import print_log_info, check_readlib, exec_sqlite3
from base.base_sys import check_system, print_sys_info, check_apache
from mdict.mdict_utils.init_utils import init_mdict_list

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
script_path = os.path.join(root_dir, 'script')
sql3_path = os.path.join(root_dir, 'db.sqlite3')


def init_ws_server():
    # windows系统启动独立的进程创建多进程池
    cmd = ['python', 'ws_server.py']
    command = ' '.join(cmd)
    print_log_info(['running websockets...'])
    try:
        subprocess.Popen(command, shell=False, cwd=script_path)
    except Exception as e:
        print('[APPS.INIT_WS_SERVER] ws_server start failed...', e)


def init_wd_server():
    # 每隔20秒检测文件夹变动，若有变动则刷新缓存
    if check_system() == 0:
        cmd = ['python3', 'wd_server.py']
        command = ' '.join(cmd)
        shell = True
    else:
        cmd = ['python', 'wd_server.py']
        command = ' '.join(cmd)
        shell = False
    print_log_info(['running watch dog...'])
    try:
        subprocess.Popen(command, shell=shell, cwd=script_path)
    except Exception as e:
        print('[APPS.INIT_WD_SERVER] wd_server start failed...', e)


# 启动mdict时进行初始化
class MdictConfig(AppConfig):
    name = 'mdict'

    def ready(self):
        init_mdict_list()

        # 函数在apps.py中会运行2次，通过--noreload关闭。
        run_once = os.environ.get('CMDLINERUNNER_RUN_ONCE')
        if run_once is None:
            os.environ['CMDLINERUNNER_RUN_ONCE'] = 'True'
            print_sys_info()
            check_readlib()
            if check_system() == 1:
                try:
                    # 数据表不存在时，不创建进程池。
                    all_dics = exec_sqlite3(sql3_path, 'select * from mdict_mdictdic')
                    init_ws_server()
                except Exception as e:
                    print(e)
            if not check_apache():
                init_wd_server()
