import os
import sys
import threading
import time
from multiprocessing import Process

import psutil
import pyscreenshot as ImageGrab
import pytesseract
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Button, Listener as MouseListener

sys.path.append(os.path.abspath(__file__))
from search import search

import win32event
import win32api
from winerror import ERROR_ALREADY_EXISTS

mutex = win32event.CreateMutex(None, False, 'name')
last_error = win32api.GetLastError()

import pystray
from pystray import MenuItem as item
import pyperclip
import tkinter as tk
from tkinter import ttk
from PIL import Image
from ctypes import windll

GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
# WS_EX_TOOLWINDOW=0x00000080

huaci_mode = 'copy'

# tesseract-OCR训练数据
# https://tesseract-ocr.github.io/tessdoc/Data-Files.html

start_flag = 0
flag = 0
start_x = 0
start_y = 0
end_x = 0
end_y = 0

t1 = 0
t2 = 0

p = None
root_url = "http://127.0.0.1:8000/mdict/"
root_dir = os.path.dirname(__file__)
ini_path = os.path.join(root_dir, 'huaci.ini')

if os.path.exists(ini_path):
    with open(ini_path, 'r', encoding='utf-8') as f:
        root_url = f.read().strip()


def translate_picture(img):
    text = pytesseract.image_to_string(img, lang='chi_sim')
    text = text.replace('\n', '').replace('\t', '').strip()
    if len(text) == 0:
        print('text length is zero')
        return
    if len(text) > 30:
        print('text length exceed limit of length', len(text))
        return

    search_mdict(text)


def translate_clipboard():
    try:
        # result = root.selection_get(selection="CLIPBOARD").strip()
        # tkinter的剪切板读取必须在mainloop中，当root widthdraw后，就不能用了。
        result = pyperclip.paste()
        if 0 < len(result) <= 30:
            search_mdict(result)
    except Exception as e:
        print(e)


def on_click(x, y, button, pressed):  # button：鼠标键，pressed：是按下还是抬起
    global start_flag
    global flag
    global start_x
    global start_y
    global end_x
    global end_y
    global t1, t2

    if start_flag == 1:

        if button == Button.left and pressed:

            flag += 1

            if flag % 2 is 1:
                t1 = time.perf_counter()
                start_x = x
                start_y = y
                print("start_x,start_y:", start_x, start_y)
            else:
                t2 = time.perf_counter()
                end_x = x
                end_y = y
                print("end_x,end_y:", end_x, end_y)
                if abs(end_y - start_y) > 100:
                    # init_vars()
                    start_x = end_x
                    start_y = end_y
                    end_x = 0
                    end_y = 0
                    print('exceed limit of height', abs(end_y - start_y))
                    return
                if abs(end_x - start_x) > 500:
                    # init_vars()
                    start_x = end_x
                    start_y = end_y
                    end_x = 0
                    end_y = 0
                    print('exceed limit of width', abs(end_x - start_x))
                    return

                if end_x == start_x or end_y == start_y:
                    flag -= 1
                    print('duplicated click')
                    return

                if 0 < t2 - t1 <= 5:
                    if start_x < end_x and start_y < end_y:
                        im = ImageGrab.grab(bbox=(start_x, start_y, end_x, end_y))
                        translate_picture(im)
                    elif start_x < end_x and start_y > end_y:
                        im = ImageGrab.grab(bbox=(start_x, end_y, end_x, start_y))
                        translate_picture(im)

                    elif start_x > end_x and start_y < end_y:
                        im = ImageGrab.grab(bbox=(end_x, start_y, start_x, end_y))
                        translate_picture(im)

                    elif start_x > end_x and start_y > end_y:
                        im = ImageGrab.grab(bbox=(end_x, end_y, start_x, start_y))
                        translate_picture(im)
                else:
                    init_vars()
                    print('exceed limit of time', t2 - t1)
    else:
        init_vars()


def on_scroll(x, y, dx, dy):
    init_vars()


timestamp = 0
timestamp2 = 0


def clear_timestamp():
    global timestamp, timestamp2
    timestamp = 0
    timestamp2 = 0


def on_press(key):
    global start_flag, timestamp, timestamp2, huaci_mode
    try:
        if key == Key.ctrl or key == Key.ctrl_l or key == Key.ctrl_r:
            clear_timestamp()
            timestamp = time.perf_counter()
            return
        elif key.char == '\x03':
            if timestamp2 == 0:
                clear_timestamp()
                timestamp2 = time.perf_counter()
                return
        else:
            if timestamp > 0:
                if key.char == 'c':
                    newtime = time.perf_counter()
                    if newtime - timestamp < 0.5:
                        clear_timestamp()
                        timestamp2 = newtime
                        return
        if timestamp2 > 0:
            if key.char == 'c' or key.char == '\x03':
                newtime = time.perf_counter()
                if newtime - timestamp2 < 0.5:
                    clear_timestamp()
                    start_flag = 1
                    if huaci_mode == 'copy':
                        translate_clipboard()
                    elif huaci_mode == 'ocr':
                        mouse_monitor()
                    return
    except AttributeError as e:
        # 非字母的键没有char这个属性sq
        clear_timestamp()


def thread_mouse_fun():
    with MouseListener(on_click=on_click, on_scroll=on_scroll) as mouse_listener:
        mouse_listener.join()


thread_mouse = None


def mouse_monitor():
    global thread_mouse
    thread_mouse = threading.Thread(target=thread_mouse_fun)
    thread_mouse.start()
    print('thread_mouse has started')


def thread_keyboard_fun():
    with KeyboardListener(on_press=on_press) as keyboard_listener:
        keyboard_listener.join()


def init_vars():
    global flag, t1, t2, start_x, start_y, end_x, end_y

    flag = 0
    t1 = 0
    t2 = 0
    start_x = 0
    start_y = 0
    end_x = 0
    end_y = 0


def killtree(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()

        parent.kill()
    except psutil.NoSuchProcess as e:
        print(e)


def search_mdict(query):
    global start_flag, p, root_url

    start_flag = 0
    init_vars()

    if p is not None:
        print('closing process ', p.pid)
        killtree(p.pid)
        # p.terminate()
        # p.join()
        # p.close()
    p = Process(target=search, args=(query, root_url))
    p.daemon = True
    p.start()


thread_keyboard = None


def run_huaci():
    global thread_keyboard
    if thread_keyboard is None:
        thread_keyboard = threading.Thread(target=thread_keyboard_fun)
        thread_keyboard.start()


def run():
    global huaci_mode
    if radio_v.get() == 'copy':
        huaci_mode = 'copy'
        print('复制查词模式')
        print('选择文字后按ctrl+c+c复制查词')
    elif radio_v.get() == 'ocr':
        huaci_mode = 'ocr'
        print('截图OCR查词模式')
        print('按ctrl+c+c后点击截图查词')
    run_huaci()


def set_appwindow(root):
    # 用pythonw运行后，不显示cmd窗口，因此没有任务栏图标，这里加上任务栏图标
    hwnd = windll.user32.GetParent(root.winfo_id())
    style = windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    # style = style & ~WS_EX_TOOLWINDOW
    style = style | WS_EX_APPWINDOW
    res = windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
    # re-assert the new window style
    myappid = 'djangomdict.version'  # arbitrary string
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    #设置任务栏的图标为窗口的图标
    root.wm_withdraw()
    root.after(10, lambda: root.wm_deiconify())


def quit_window(icon, item):
    icon.stop()
    root.destroy()


def show_window(icon, item):
    icon.stop()
    root.after(0, root.deiconify)
    root.after(10, lambda: set_appwindow(root))


def withdraw_window():
    # 关闭设置界面后
    root.withdraw()
    create_systray()


def create_systray():
    # 显示系统托盘
    image = Image.open("default.ico")
    menu = (item('设置', show_window), item('退出', quit_window))
    icon = pystray.Icon("djangomdict", icon=image, title='django-mdict', menu=menu)
    icon.run()


if __name__ == "__main__":
    if last_error == ERROR_ALREADY_EXISTS:
        # 只运行一个实例
        print('App instance already running')
    else:
        root = tk.Tk()
        root.withdraw()
        root.title('')

        huaci_path=os.path.dirname(os.path.abspath(__file__))
        ico_path=os.path.join(huaci_path,'default.ico')
        if os.path.exists(ico_path):
            root.iconbitmap(ico_path)

        root.resizable(0, 0)  # 禁止缩放
        root.attributes("-toolwindow", True)  # toolwindow模式，只有关闭按钮，不显示图标，最小化和最大化按钮
        root.protocol('WM_DELETE_WINDOW', withdraw_window)

        radio_v = tk.StringVar()
        tr1 = ttk.Radiobutton(root, text='复制查词', value='copy', variable=radio_v, command=run)
        tr1.invoke()
        tr1.pack(fill='both', expand=True)
        ttk.Radiobutton(root, text='OCR查词', value='ocr', variable=radio_v, command=run).pack(fill='both', expand=True)

        create_systray()

        root.mainloop()

# if __name__ == "__main__":
#     print('url:', root_url)
#     print('按ctrl+c+c开始划词。')
#     run_huaci()
