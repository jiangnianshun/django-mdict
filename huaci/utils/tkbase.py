import os
from PIL import Image

root_path = os.path.dirname(os.path.abspath(__file__))
ico_path = os.path.join(root_path, 'resources', 'default.ico')
data_path = os.path.join(root_path, 'tessdata')
data_path = data_path.replace('\\','/')

if not os.path.exists(data_path):
    data_path = ''


def set_icon(root):
    if os.path.exists(ico_path):
        root.iconbitmap(ico_path)


def get_icon():
    return Image.open(ico_path)
