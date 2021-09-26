import json
import sys
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mdict', default="", help='mdict path')

args = parser.parse_args()

json_path = args.mdict

tk_exist = False
try:
    import tkinter as tk
    from tkinter.filedialog import askopenfilename

    tk_exist = True
except:
    print('tkinter not installed')

if tk_exist:
    root = tk.Tk()
    root.withdraw()  # 隐藏主界面

    json_path = askopenfilename()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django

django.setup()

from mdict.models import MyMdictEntry, MyMdictItem, MyMdictEntryType

with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)


def import_mymdictentry():
    mymdict_entry_list = json_data['builtindic']
    for mymdict_entry in mymdict_entry_list:
        mdict_entry = mymdict_entry['mdict_entry']
        mdict_item_list = mymdict_entry['mdict_item_list']
        mymdict_entry_obj = MyMdictEntry.objects.create(mdict_entry=mdict_entry)
        for mdict_item in mdict_item_list:
            item_entry = mdict_item['item_entry']
            item_content = mdict_item['item_content']
            item_type = mdict_item['item_type']
            tmp = MyMdictEntryType.objects.filter(mdict_type=item_type)
            if len(tmp) > 0:
                item_type_obj = tmp[0]
            elif item_type is None:
                item_type_obj = None
            else:
                item_type_obj = MyMdictEntryType.objects.create(mdict_type=item_type)
            MyMdictItem.objects.create(item_mdict=mymdict_entry_obj, item_entry=item_entry, item_content=item_content,
                                       item_type=item_type_obj)


import_mymdictentry()
