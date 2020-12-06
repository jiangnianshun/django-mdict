import configparser
import os

from mysite.settings import BASE_DIR

user_config_path = os.path.join(BASE_DIR, 'config.ini')

default_config = {
    'COMMON': {
        'process_num': -1,  # 默认进程数
        'cache_num': 30,  # 查询提示缓存的个数
        'search_cache_num': 20,  # 查询（分页）缓存的个数
        'builtin_dic_enable': True,  # 启用内置词典
    },
    'SEARCH': {
        'spell_check': 2,
        'lemmatize': 2,
        'merge_entry_enable': True,
        'merge_entry_num': 5,  # 全局设置，同一个词典一个词条的条数多于等于5个时，将合并为1个。
        'merge_entry_max_length': 500,
        'st_enable': True,  # 繁简和简繁转化
        'chaizi_enable': True,  # 拆字反查
        'fh_char_enable': True,  # 全角转换
        'force_refresh': False,  # 强制刷新
        'select_btn_enable': True,  # 是否启用选择文字弹出框
        'suggestion_num': 15,  # 查询提示显示的数目
        'link_new_label': False,
        'force_font': False,  # 强制使用全宋体
        'card_show': False,  # 允许一次展开多个词典
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
        config.read(user_config_path)
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
                if value.isdigit():
                    return int(value)
                else:
                    return value
            else:
                for sec in default_config.keys():
                    if con_name in default_config[sec].keys():
                        return default_config[sec][con_name]
    # config不存在时的处理，应该返回默认值，后面再处理
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
