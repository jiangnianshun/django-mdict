import os
import sys
import pystray
from pystray import MenuItem as item
import tkinter as tk
from tkinter import ttk
from PIL import Image
from ctypes import windll

GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
# WS_EX_TOOLWINDOW=0x00000080

sys.path.append(os.path.abspath(__file__))
try:
    from huaci.utils import *
except Exception:
    from utils import *


class TkWindow():
    def __init__(self):
        check_version()

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title('')

        self.huaci = Huaci()

        huaci_path = os.path.dirname(os.path.abspath(__file__))
        ico_path = os.path.join(huaci_path, 'default.ico')
        if os.path.exists(ico_path):
            self.root.iconbitmap(ico_path)

        self.root.resizable(0, 0)  # 禁止缩放
        self.root.attributes("-toolwindow", True)  # toolwindow模式，只有关闭按钮，不显示图标，最小化和最大化按钮
        self.root.protocol('WM_DELETE_WINDOW', self.withdraw_window)

        Widget1(self.root, self.huaci)

        self.create_systray()

        self.root.mainloop()

    def quit_window(self, icon, item):
        if self.huaci.p is not None:
            print('closing process ', self.huaci.p.pid)
            self.huaci.killtree(self.huaci.p.pid)
        icon.stop()
        self.root.destroy()

    def set_appwindow(self):
        # 用pythonw运行后，不显示cmd窗口，因此没有任务栏图标，这里加上任务栏图标
        hwnd = windll.user32.GetParent(self.root.winfo_id())
        style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        # style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        res = windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        # re-assert the new window style
        myappid = 'djangomdict.version'  # arbitrary string
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        # 设置任务栏的图标为窗口的图标
        self.root.wm_withdraw()
        self.root.after(10, lambda: self.root.wm_deiconify())

    def show_window(self, icon, item):
        icon.stop()
        self.root.after(0, self.root.deiconify)
        self.root.after(10, self.set_appwindow)

    def create_systray(self):
        # 显示系统托盘
        image = Image.open("default.ico")
        menu = pystray.Menu(item('设置', self.show_window, default=True), item('退出', self.quit_window))
        # 这里menu应该用pystray.Menu()，如果直接使用tuple，那么左键单击报错，其他功能正常。
        # 鼠标左键点击托盘图标运行default=True的Menuitem，如果default均为False，则无动作。
        icon = pystray.Icon("djangomdict", icon=image, title='django-mdict', menu=menu)
        icon.run()

    def withdraw_window(self):
        # 关闭设置界面后
        self.root.withdraw()
        self.create_systray()


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


def check_version():
    print('tesseract version:', pytesseract.get_tesseract_version())
