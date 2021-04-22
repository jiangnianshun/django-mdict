import re
import sys
import platform

reg1 = r'^[a-zA-Z]:[/\\]'
reg2 = r'[/|\\]'
regp = re.compile(reg2)


def split_os_path(path):
    absolute = ''
    if check_system() == 0:
        if path[0] == '/' or path[0] == '\\':
            absolute = '/'
            path = path[1:]
    else:
        result = re.match(reg1, path)
        if result is not None:
            absolute = result.group()
            path = path[len(absolute):]
            absolute = absolute.replace('/', '').replace('\\', '')
    path_list = list(filter(None, regp.split(path)))

    path_dict = {'absolute': absolute, 'path': path_list}
    return path_dict


def find_os_path(a, b):
    # 获取to_find_path_list在target_path_list中的位置，不存在返回(-1,-1)，若重复，则返回最右面那个
    start = -1
    end = -1
    flag = 0
    if len(b) > len(a):
        return -1, -1
    b0_list = [i for i, x in enumerate(a) if x == b[0]]
    if len(b0_list) == 0:
        return -1, -1
    flag = False
    for i in reversed(b0_list):
        flag = False
        for j in range(len(b)):
            if not b[j] == a[i + j]:
                flag = True
                break
        if flag:
            continue
        return i, i + len(b)
    return -1, -1


default_system = ''


def get_sys_name(set_system=''):
    global default_system
    if set_system != '':
        default_system = set_system
    if default_system != '':
        return default_system
    return platform.system()


def check_system():
    sys_name = get_sys_name()
    if sys_name == 'Linux':  # 下一步区分linux和wsl
        return 0
    elif sys_name == 'Windows':
        return 1
    else:
        print('unknown system')
        return 1


def check_module_import(mod_name):
    if mod_name in sys.modules:
        return True
    else:
        return False
