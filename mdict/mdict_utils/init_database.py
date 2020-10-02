# -*- coding: utf-8 -*-
from mdict.mdict_utils.init_utils import init_vars
from mdict.mdict_utils.data_utils import get_or_create_dic

def init_database():
    print('init database')
    for k, v in init_vars.mdict_odict.items():
        get_or_create_dic(k)
