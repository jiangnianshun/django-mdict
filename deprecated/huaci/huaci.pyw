import os
import sys
import win32event
from winerror import ERROR_ALREADY_EXISTS

sys.path.append(os.path.abspath(__file__))
try:
    from huaci.utils.tkmain import *
except Exception:
    from utils.tkmain import *

if __name__ == "__main__":
    mutex = win32event.CreateMutex(None, False, 'django-mdict')
    last_error = win32api.GetLastError()
    # mutex必须在main中，否则会执行两次，import时执行一次，import结束后执行一次，这样就无法启动。

    if last_error == ERROR_ALREADY_EXISTS:
        # 只运行一个实例
        print('App instance already running')
    else:
        MainWindow()
