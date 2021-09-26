import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django

django.setup()

from base.base_func import ROOT_DIR

time_str = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))

export_root_path = os.path.join(ROOT_DIR, 'export')
export_data_root_path = os.path.join(export_root_path, 'data')
export_uploads_path = os.path.join(export_data_root_path, 'media', 'uploads')

if not os.path.exists(export_root_path):
    os.mkdir(export_root_path)


def except_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print('error:', e)
        return None

    return wrapper


def export_database(mdl, jtype):
    item_list = mdl.objects.all()
    export_list = []
    for item in item_list:
        item_data = None
        if jtype == 'mymdictentry':
            mdict_entry = item.mdict_entry
            mdict_item_list = []
            for mdict_item in item.mymdictitem_set.all():
                item_entry = mdict_item.item_entry
                if mdict_item.item_type is None:
                    item_type = None
                else:
                    item_type = mdict_item.item_type.mdict_type
                item_content = mdict_item.item_content
                item_obj = {'item_entry': item_entry, 'item_type': item_type, 'item_content': item_content}
                mdict_item_list.append(item_obj)
            item_data = {'mdict_entry': mdict_entry, 'mdict_item_list': mdict_item_list}
        elif jtype == 'mdictdic':
            mdict_name = item.mdict_name
            mdict_file = item.mdict_file
            mdict_enable = item.mdict_enable
            mdict_priority = item.mdict_priority
            mdict_es_enable = item.mdict_es_enable
            mdict_md5 = item.mdict_md5
            group_name_list = []
            for mdict_group in item.mdictdicgroup_set.all():
                group_name_list.append(mdict_group.dic_group_name)
            item_data = {'mdict_name': mdict_name, 'mdict_file': mdict_file, 'mdict_enable': mdict_enable,
                         'mdict_priority': mdict_priority, 'mdict_es_enable': mdict_es_enable, 'mdict_md5': mdict_md5,
                         'group_name_list': group_name_list}
        elif jtype == 'mdictonline':
            mdict_name = item.mdict_name
            mdict_url = item.mdict_url
            mdict_enable = item.mdict_enable
            mdict_priority = item.mdict_priority
            mdict_isiframe = item.mdict_isiframe
            item_data = {'mdict_name': mdict_name, 'mdict_url': mdict_url, 'mdict_enable': mdict_enable,
                         'mdict_priority': mdict_priority, 'mdict_isiframe': mdict_isiframe}
        elif jtype == 'website':
            site_name = item.site_name
            site_url = item.site_url
            site_brief = item.site_brief
            site_priority = item.site_priority
            site_group = item.site_group
            if item.site_group is not None:
                group_name = item.site_group.group_name
                group_priority = item.site_group.group_priority
                site_group = {'group_name': group_name, 'group_priority': group_priority}
            item_data = {'site_name': site_name, 'site_url': site_url, 'site_brief': site_brief,
                         'site_priority': site_priority, 'site_group': site_group}
        if item_data is not None:
            export_list.append(item_data)
    return {jtype: export_list}


def write_json(export_data, jtype):
    export_file = "export_" + time_str + '_' + jtype + '.json'
    export_json_path = os.path.join(ROOT_DIR, 'export', export_file)
    with open(export_json_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(export_data, indent=4, ensure_ascii=False))


# @except_decorator
def export_mymdictentry():
    from mdict.models import MyMdictEntry
    export_data = export_database(MyMdictEntry, 'mymdictentry')
    write_json(export_data, 'mymdictentry')
    print('mymdictentry export has finished.')


# @except_decorator
def export_mdictdic():
    from mdict.models import MdictDic
    export_data = export_database(MdictDic, 'mdictdic')
    write_json(export_data, 'mdictdic')
    print('mdictdic export has finished.')


# @except_decorator
def export_mdictonline():
    from mdict.models import MdictOnline
    export_data = export_database(MdictOnline, 'mdictonline')
    write_json(export_data, 'mdictonline')
    print('mdictonline export has finished.')


# @except_decorator
def export_website():
    from mynav.models import Website
    export_data = export_database(Website, 'website')
    write_json(export_data, 'website')
    print('website export has finished.')

def exprot_all():
    export_mymdictentry()
    export_mdictdic()
    export_mdictonline()
    export_website()


exprot_all()
