import os
import subprocess
from django.apps import AppConfig

from base.base_func import print_log_info, check_readlib
from base.sys_utils import check_system, print_sys_info
from mdict.mdict_utils.init_utils import init_mdict_list

script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'script')


def init_ws_server():
    cmd = ['python', 'ws_server.py']
    command = ' '.join(cmd)
    print_log_info(['running ws server...'])
    try:
        subprocess.Popen(command, shell=False, cwd=script_path)
    except Exception as e:
        print(e)


def init_wd_server():
    if check_system() == 0:
        cmd = ['python3', 'wd_server.py']
        command = ' '.join(cmd)
        shell = True
    else:
        cmd = ['python', 'wd_server.py']
        command = ' '.join(cmd)
        shell = False
    print_log_info(['running watch dog server...'])
    try:
        subprocess.Popen(command, shell=shell, cwd=script_path)
    except Exception as e:
        print(e)


# 启动mdict时进行初始化
class MdictConfig(AppConfig):
    name = 'mdict'

    def ready(self):
        init_mdict_list()

        # 函数在apps.py中会运行2次，在init_utils.py中运行次数更多。
        run_once = os.environ.get('CMDLINERUNNER_RUN_ONCE')
        if run_once is None:
            os.environ['CMDLINERUNNER_RUN_ONCE'] = 'True'
            print_sys_info()
            check_readlib()
            if check_system() == 1:
                init_ws_server()
            init_wd_server()
