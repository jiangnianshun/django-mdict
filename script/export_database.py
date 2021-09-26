import json
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django

django.setup()

from base.base_func import ROOT_DIR
from mdict.models import MyMdictEntry

time_str = time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))

export_file = 'export_db' + time_str + '.json'
export_root_path = os.path.join(ROOT_DIR, 'export')
export_json_path = os.path.join(ROOT_DIR, 'export', export_file)

export_data_root_path = os.path.join(export_root_path, 'data')
export_uploads_path = os.path.join(export_data_root_path, 'media', 'uploads')

if not os.path.exists(export_root_path):
    os.mkdir(export_root_path)


def export_mymdictentry():
    entry_list = MyMdictEntry.objects.all()
    export_entry_list = []
    for entry in entry_list:
        mdict_entry = entry.mdict_entry
        mdict_item_list = []
        for mdict_item in entry.mymdictitem_set.all():
            item_entry = mdict_item.item_entry
            if mdict_item.item_type is None:
                item_type = None
            else:
                item_type = mdict_item.item_type.mdict_type
            item_content = mdict_item.item_content
            item_obj = {'item_entry': item_entry, 'item_type': item_type, 'item_content': item_content}
            mdict_item_list.append(item_obj)
        entry_obj = {'mdict_entry': mdict_entry, 'mdict_item_list': mdict_item_list}
        export_entry_list.append(entry_obj)
    export_data = {'builtindic': export_entry_list}

    with open(export_json_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(export_data, indent=4, ensure_ascii=False))


export_mymdictentry()
