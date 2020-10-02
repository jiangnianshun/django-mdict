# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 12:11:06 2019

@author: jns
"""
import os
import stat


def rename_file(path, r_path):
    try:
        os.rename(path, r_path)
    except PermissionError as e:
        print('权限错误，修改只读属性。')
        print(e)
        os.chmod(path, stat.S_IWRITE)
        os.rename(path, r_path)
    except Exception as e:
        print('未处理的错误')
        print(e)


def delete_file(path):
    try:
        os.remove(path)
    except PermissionError as e:
        print(e)
        if os.path.isdir(path):
            if len(os.listdir(path)) > 0:
                print('文件夹非空，无法删除')
            else:
                print('删除文件夹')
                os.rmdir(path)
        else:
            print('修改只读属性。')
            os.chmod(path, stat.S_IWRITE)
            os.remove(path)
    except Exception as e:
        print('未处理的错误')
        print(e)


def process_num(t):
    str1 = ''
    if t < 10:
        str1 = '00' + str(t)
    elif 10 <= t < 100:
        str1 = '0' + str(t)
    else:
        str1 = str(t)
    return str1


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False
