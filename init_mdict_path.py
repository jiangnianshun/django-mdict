import json
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--mdict', default="", help='input mdict path')
parser.add_argument('-a', '--audio', default="", help='input audio path')

args = parser.parse_args()

mdict_path = args.mdict
audio_path = args.audio

tk_exist = False
try:
    import tkinter as tk
    from tkinter.filedialog import askdirectory

    tk_exist = True
except:
    print('tkinter not installed')

json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mdict_path.json')
config = {'mdict_path': [], 'audio_path': []}

if tk_exist:
    root = tk.Tk()
    root.withdraw()  # 隐藏主界面

    _path = askdirectory()
    # 如果用户点击取消和关闭选择框，返回值都是空字符串。
    if _path != '':
        config.update({'mdict_path': [_path]})
        print('mdict_path', _path)
    else:
        print('mdict_path is empty.')
    _path = askdirectory()
    if _path != '':
        config.update({'audio_path': [_path]})
        print('audio_path', _path)
    else:
        print('audio_path is empty.')
else:
    if mdict_path != '':
        config.update({'mdict_path': [mdict_path]})
        print('mdict_path', mdict_path)
    else:
        print('mdict_path is empty. require -m parameter, use -h to show help.')

    if audio_path != '':
        config.update({'audio_path': [audio_path]})
        print('audio_path', audio_path)
    else:
        print('audio_path is empty.')


def write_json_file(con, file, mode='w'):
    with open(file, mode, encoding='utf-8') as f:
        json.dump(con, f, indent=4)
    os.chmod(file, 0o777)


def process_list(path_list):
    for i in range(len(path_list) - 1, -1, -1):
        if path_list[i] == "":
            del path_list[i]
        elif not isinstance(path_list[i], str):
            del path_list[i]
        elif len(path_list[i]) > 1 and path_list[i][0] == '~':
            path_list[i] = os.path.join(os.path.expanduser('~'), path_list[i][2:])
    return path_list


if os.path.exists(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        temp = f.read()
    try:
        data = json.loads(temp)
        mdict_path_list = process_list(config['mdict_path'])
        audio_path_list = process_list(config['audio_path'])

        mdict_path_list.extend(process_list(data['mdict_path']))
        audio_path_list.extend(process_list(data['audio_path']))

        for i in range(len(mdict_path_list) - 1, -1, -1):
            if i > 0 and mdict_path_list[i] in mdict_path_list[:i]:
                del mdict_path_list[i]

        for i in range(len(audio_path_list) - 1, -1, -1):
            if i > 0 and audio_path_list[i] in audio_path_list[:i]:
                del audio_path_list[i]

        new_data = {'mdict_path': mdict_path_list, 'audio_path': audio_path_list}
        write_json_file(new_data, json_file)
    except:
        write_json_file(config, json_file)
else:
    write_json_file(config, json_file)
