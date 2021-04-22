import os
import subprocess
from django.apps import AppConfig

from mdict.mdict_utils.init_utils import init_mdict_list
from base.sys_utils import check_system

script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'script')


def init_ws_server():
    cmd = ['python', 'ws_server.py']
    command = ' '.join(cmd)
    print('running ws server:', command)
    try:
        subprocess.Popen(command, shell=True, cwd=script_path)
    except Exception as e:
        print(e)


# 启动mdict时进行初始化
class MdictConfig(AppConfig):
    name = 'mdict'

    def ready(self):
        init_mdict_list(False)
        if check_system() == 1:
            init_ws_server()
