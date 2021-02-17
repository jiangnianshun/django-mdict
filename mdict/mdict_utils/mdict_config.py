import configparser
import os
import psutil

from base.base_func import is_number
from mysite.settings import BASE_DIR

cpu_num = psutil.cpu_count(False)


# cpu的物理核心数


def set_cpunum(t_list_len):
    global cpu_num
    cnum = round(t_list_len / 10)

    if cnum < cpu_num:
        cpu_num = cnum

    if cnum < 1:
        cpu_num = 1


def get_cpunum():
    global cpu_num
    return cpu_num


user_config_path = os.path.join(BASE_DIR, 'config.ini')

default_config = {
    'COMMON': {
        'cache_num': 30,  # 查询提示缓存的个数
        'search_cache_num': 20,  # 查询（分页）缓存的个数
        'builtin_dic_enable': True,  # 启用内置词典
        'es_host': 'http://127.0.0.1:9200/'
    },
    'SEARCH': {
        'merge_entry_max_length': 1000,
        'st_enable': True,  # 繁简和简繁转化
        'chaizi_enable': True,  # 拆字反查
        'fh_char_enable': True,  # 全角转换
        'kana_enable': True,  # 假名转换
        'force_refresh': False,  # 强制刷新
        'select_btn_enable': True,  # 是否启用选择文字弹出框
        'suggestion_num': 30,  # 查询提示显示的数目
        'link_new_label': False,
        'force_font': False,  # 强制使用全宋体
        'card_show': False,  # 允许一次展开多个词典
        'default_group': 0,
    }
}

config = configparser.ConfigParser(interpolation=None)
# ConfigParser()对字符串含有%会抛出异常，要设置interpolation=None。

config_permission = True


def get_config():
    global config, config_permission

    if not config_permission:
        return config

    if os.path.exists(user_config_path):
        config.read(user_config_path, encoding='utf-8')
    else:
        try:
            with open(user_config_path, 'w', encoding='utf-8') as f:
                config.write(f)
            os.chmod(user_config_path, 0o777)
        except PermissionError as e:
            print(e)
            config_permission = False
    return config


def get_config_con(con_name):
    con = get_config()
    for section in con.sections():
        if con_name in con[section].keys():
            value = con[section][con_name]
            if isinstance(value, str):
                if is_number(value.split('.')[0]):
                    return int(value)
                else:
                    return value

    # config.ini中没有时查询默认值
    for section in default_config:
        if con_name in default_config[section].keys():
            return default_config[section][con_name]

    # 设置仍不存在
    print(con_name)
    raise Exception('config not exists!')


def get_config_sec(sec):
    con = get_config()
    if sec in con.sections():
        return con[sec]
    else:
        raise Exception('config section ont existed!')


def create_config():
    global config_permission
    for section in default_config:
        config[section] = default_config[section]
    try:
        with open(user_config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        os.chmod(user_config_path, 0o777)
    except PermissionError as e:
        print(e)
        config_permission = False


def add_or_edit_config_section(sec_name, sec):
    global config_permission
    con = get_config()
    con[sec_name.upper()] = sec
    try:
        with open(user_config_path, 'w', encoding='utf-8') as f:
            con.write(f)
        os.chmod(user_config_path, 0o777)
    except PermissionError as e:
        print(e)
        config_permission = False


def set_config(sec, save_config):
    global config, config_permission
    con = get_config()
    for con_name, con_value in save_config.items():
        con[sec][con_name] = str(con_value)
    config = con
    try:
        with open(user_config_path, 'w', encoding='utf-8') as f:
            con.write(f)
        os.chmod(user_config_path, 0o777)
    except PermissionError as e:
        print(e)
        config_permission = False


if not os.path.exists(user_config_path):
    create_config()

config.read(user_config_path, encoding='utf-8')
