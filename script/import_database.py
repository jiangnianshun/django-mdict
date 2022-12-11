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

from mdict.models import MyMdictEntry, MyMdictItem, MyMdictEntryType, MdictDic, MdictDicGroup, MdictOnline
from mynav.models import Website, Webgroup


def read_json():
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    return json_data


def import_database(item_list, jtype):
    for item in item_list:
        if jtype == 'mymdictentry':
            mdict_entry = item['mdict_entry']
            mdict_item_list = item['mdict_item_list']
            tmp_set = MyMdictEntry.objects.filter(mdict_entry=mdict_entry)
            if len(tmp_set) == 0:
                mymdict_entry_obj = MyMdictEntry.objects.create(mdict_entry=mdict_entry)
                for mdict_item in mdict_item_list:
                    item_entry = mdict_item['item_entry']
                    item_content = mdict_item['item_content']
                    item_type = mdict_item['item_type']
                    item_type_set = MyMdictEntryType.objects.filter(mdict_type=item_type)
                    if len(item_type_set) > 0:
                        item_type_obj = item_type_set[0]
                    elif item_type is None:
                        item_type_obj = None
                    else:
                        item_type_obj = MyMdictEntryType.objects.create(mdict_type=item_type)
                    MyMdictItem.objects.create(item_mdict=mymdict_entry_obj, item_entry=item_entry,
                                               item_content=item_content,
                                               item_type=item_type_obj)
            else:
                print(mdict_entry, 'has exists.')
        elif jtype == 'mdictdic':
            mdict_name = item['mdict_name']
            mdict_file = item['mdict_file']
            mdict_enable = item['mdict_enable']
            mdict_priority = item['mdict_priority']
            mdict_es_enable = item['mdict_es_enable']
            mdict_md5 = item['mdict_md5']
            group_name_list = item['group_name_list']
            tmp_set = MdictDic.objects.filter(mdict_file=mdict_file)
            if len(tmp_set) > 0:
                dic_obj = tmp_set[0]
            else:
                dic_obj = MdictDic.objects.create(mdict_name=mdict_name, mdict_file=mdict_file,
                                                  mdict_enable=mdict_enable,
                                                  mdict_priority=mdict_priority, mdict_es_enable=mdict_es_enable,
                                                  mdict_md5=mdict_md5)
            for group_name in group_name_list:
                group_set = MdictDicGroup.objects.filter(dic_group_name=group_name)
                if len(group_set) > 0:
                    group_obj = group_set[0]
                else:
                    group_obj = MdictDicGroup.objects.create(dic_group_name=group_name)
                group_obj.mdict_group.add(dic_obj)
        elif jtype == 'mdictonline':
            mdict_name = item['mdict_name']
            mdict_url = item['mdict_url']
            mdict_enable = item['mdict_enable']
            mdict_priority = item['mdict_priority']
            mdict_isiframe = item['mdict_isiframe']
            tmp_set = MdictOnline.objects.filter(mdict_name=mdict_name)
            if len(tmp_set) == 0:
                MdictOnline.objects.create(mdict_name=mdict_name, mdict_url=mdict_url, mdict_enable=mdict_enable,
                                           mdict_priority=mdict_priority, mdict_isiframe=mdict_isiframe)
            else:
                print(mdict_name, 'has exists.')
        elif jtype == 'website':
            site_name = item['site_name']
            site_url = item['site_url']
            site_brief = item['site_brief']
            site_priority = item['site_priority']
            site_group = item['site_group']
            if site_group is None:
                site_group_obj = None
            else:
                group_name = item['site_group']['group_name']
                group_priority = item['site_group']['group_priority']
                group_set = Webgroup.objects.filter(group_name=group_name)
                if len(group_set) > 0:
                    site_group_obj = group_set[0]
                else:
                    site_group_obj = Webgroup.objects.create(group_name=group_name, group_priority=group_priority)
            tmp_set = Website.objects.filter(site_url=site_url)
            if len(tmp_set) == 0:
                Website.objects.create(site_name=site_name, site_url=site_url, site_brief=site_brief,
                                       site_priority=site_priority, site_group=site_group_obj)
            else:
                print(site_url, 'has exists.')


def import_all():
    json_data = read_json()
    json_data_keys = json_data.keys()
    print('import starting...')
    if 'mymdictentry' in json_data_keys:
        import_database(json_data['mymdictentry'], 'mymdictentry')
        print('mymdictentry import has been finished.')
    if 'mdictdic' in json_data_keys:
        import_database(json_data['mdictdic'], 'mdictdic')
        print('mdictdic import has been finished.')
    if 'mdictonline' in json_data_keys:
        import_database(json_data['mdictonline'], 'mdictonline')
        print('mdictonline import has been finished.')
    if 'website' in json_data_keys:
        import_database(json_data['website'], 'website')
        print('website import has been finished.')


if __name__ == '__main__':
    import_all()
