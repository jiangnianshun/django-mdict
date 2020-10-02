import configparser
import os

from mysite.settings import BASE_DIR
from base.sys_utils import check_system

# 分两个config，因为windows下创建的config，在wsl下报permissionerror。
if check_system() == 0:
    user_config_path = os.path.join(BASE_DIR, 'config_lin.ini')
else:
    user_config_path = os.path.join(BASE_DIR, 'config_win.ini')

default_config = {
    'COMMON': {
        'process_num': 4,  # 默认进程数
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
        'suggestion_number': 15,  # 查询提示显示的数目
        'link_new_label': False,
        'force_font': False,  # 强制使用全宋体
        'card_show': False,  # 允许一次展开多个词典
    }
}

config = configparser.ConfigParser(interpolation=None)


# ConfigParser()对字符串含有%会抛出异常，要设置interpolation=None。

def get_config():
    global config
    if os.path.exists(user_config_path):
        config.read(user_config_path)
    else:
        with open(user_config_path, 'w', encoding='utf-8') as f:
            config.write(f)
    return config


def get_config_con(con_name):
    con = get_config()
    for section in con.sections():
        if con_name in con[section].keys():
            value = con[section][con_name]
            if value.isdigit():
                return int(value)
            else:
                return value
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
    for section in default_config:
        config[section] = default_config[section]
    with open(user_config_path, 'w', encoding='utf-8') as f:
        config.write(f)


def add_or_edit_config_section(sec_name, sec):
    con = get_config()
    con[sec_name.upper()] = sec
    with open(user_config_path, 'w', encoding='utf-8') as f:
        con.write(f)


def set_config(save_config):
    con = get_config()
    for con_name, con_value in save_config.items():
        con['SEARCH'][con_name] = str(con_value)
    with open(user_config_path, 'w', encoding='utf-8') as f:
        con.write(f)


if not os.path.exists(user_config_path):
    create_config()

config.read(user_config_path, encoding='utf-8')
