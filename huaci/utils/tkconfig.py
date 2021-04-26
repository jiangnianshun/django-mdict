import os
import sys
import tkinter as tk
from tkinter import ttk

GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
# WS_EX_TOOLWINDOW=0x00000080

sys.path.append(os.path.abspath(__file__))

try:
    from .tkbase import *
except Exception:
    from tkbase import *


class ConfigWindow:
    def __init__(self, main):
        self.root = tk.Toplevel()
        self.root.title('设置')
        self.root.attributes('-topmost', True)
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        self.root.withdraw()
        self.main = main
        self.huaci = self.main.huaci

        set_icon(self.root)

        self.root.resizable(0, 0)  # 禁止缩放
        self.root.attributes("-toolwindow", True)  # toolwindow模式，只有关闭按钮，不显示图标，最小化和最大化按钮

        Widget1(self.root, self.huaci)

    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()


# 划词设置窗口
class Widget1:
    def __init__(self, root, huaci):
        self.lang = {'chi_sim': '中文简体', 'chi_tra': '中文繁体', 'jpn': '日文'}
        self.huaci = huaci
        self.url_dict = huaci.url_dict

        self.root = root
        self.radio_v = tk.StringVar(value='copy')
        tr1 = ttk.Radiobutton(self.root, text='复制查词', value='copy', variable=self.radio_v, command=self.run)
        tr1.invoke()
        tr1.pack(fill='both', expand=True)
        ttk.Radiobutton(self.root, text='OCR查词', value='ocr', variable=self.radio_v, command=self.run) \
            .pack(fill='both', expand=True)
        self.check_dict = {}
        for la in self.lang.keys():
            self.check_dict.update({la: tk.IntVar()})
            cb = ttk.Checkbutton(self.root, text=self.lang[la], variable=self.check_dict[la], command=self.set_lang)
            cb.invoke()
            cb.pack(fill='both', expand=True)

        url_keys = self.url_dict.keys()
        self.radio_v2 = tk.StringVar(value='django-mdict')
        for i in range(len(self.url_dict)):
            url_name = list(url_keys)[i]
            tr = tk.Radiobutton(self.root, text=url_name, value=url_name, variable=self.radio_v2, indicatoron=False,
                                command=self.set_root_url)
            # ttk的Radiobutton不支持indicatoron
            if i == 0:
                tr.invoke()
            tr.pack(fill='both', expand=True)

    def set_root_url(self):
        self.huaci.root_url = self.url_dict[self.radio_v2.get()]
        print('root url:', self.huaci.root_url)

    def set_lang(self):
        lang_str = ''
        for la in self.lang.keys():
            if la in self.check_dict.keys() and self.check_dict[la].get() == 1:
                lang_str = lang_str + '+' + la
        lc = lang_str[1:]
        if lc == '':
            lc = 'eng'
        print('已设置OCR语言为', lc)
        self.huaci.lang_con = lc

    def run(self):
        if self.radio_v.get() == 'copy':
            hm = 'copy'
            print('###复制查词模式###')
            print('选择文字后按ctrl+c+c复制查词')
        elif self.radio_v.get() == 'ocr':
            hm = 'ocr'
            print('###截图OCR查词模式###')
            print('按ctrl+c+c后点击截图查词')
        else:
            hm = 'copy'
            print('###复制查词模式###')
            print('选择文字后按ctrl+c+c复制查词')

        self.huaci.run_huaci(hm)
