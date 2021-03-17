import os
import json
import collections

# 窗口位置
xpos = 0
ypos = 40
typos = ypos + 40

tkwidth = 500
tkheigtht = 800

'''
auto_zooming:页面缩放比例，默认0.0，只支持windows。
-1.0,75%;0.0,100%;1.0,125%;2.0,150%.

xpos,ypos:窗口位置
typos:第二个窗口的位置

tkwidth,tkheight:窗口宽高
'''

default_url_dict = collections.OrderedDict()
default_url_dict.update({
    '查询': 'http://127.0.0.1:8000/mdict/?query=%WORD%',
    '全文查询': 'http://127.0.0.1:8000/mdict/es/?query=%WORD%'
})

cef_settings = {
    'auto_zooming': '0.0',
    'xpos': xpos,
    'ypos': ypos,
    'typos': typos,
    'tkwidth': tkwidth,
    'tkheight': tkheigtht
}

default_config = {
    'url': default_url_dict,
    'cef': cef_settings
}

root_dir = os.path.dirname(__file__)
ini_path = os.path.join(root_dir, 'huaci.ini')

huaci_config = default_config

if os.path.exists(ini_path):
    with open(ini_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict):
            if 'url' in data.keys():
                huaci_config['url'].update(data['url'])
            if 'cef' in data.keys():
                huaci_config['cef'].update(data['cef'])
else:
    with open(ini_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4, ensure_ascii=False)
    os.chmod(ini_path, 0o777)

print('settings:', huaci_config)


def get_huaci_config():
    return huaci_config
