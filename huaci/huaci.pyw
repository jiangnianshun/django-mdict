import os
import psutil
import sys
import threading
import time
from multiprocessing import Process

import pyscreenshot as ImageGrab
import pytesseract
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Button, Listener as MouseListener

sys.path.append(os.path.abspath(__file__))
from search import search

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
    result = root.selection_get(selection="CLIPBOARD").strip()
    if 0 < len(result) <= 30:
        search_mdict(result)


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
    global start_flag, timestamp, timestamp2
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
                    if huaci_mode == 1:
                        translate_clipboard()
                    elif huaci_mode == 2:
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

thread_keyboard=None

def run_huaci():
    global thread_keyboard
    if thread_keyboard is None:
        thread_keyboard = threading.Thread(target=thread_keyboard_fun)
        thread_keyboard.start()


import tkinter as tk

huaci_mode = 1


def run():
    global huaci_mode
    print('url:', root_url)
    if v.get() == 1:
        huaci_mode = 1
        print('复制查词模式')
        print('选择文字后按ctrl+c+c复制查词')
    elif v.get() == 2:
        huaci_mode = 2
        print('截图OCR查词模式')
        print('按ctrl+c+c后点击截图查词')
    run_huaci()


if __name__ == "__main__":
    root = tk.Tk()
    root.title('')
    root.attributes("-toolwindow", True)  # toolwindow模式，只有关闭按钮，没有图标，最小化和最大化按钮
    root.resizable(0, 0)  # 禁止缩放
    v = tk.IntVar()
    tk.Radiobutton(root, text='复制查词', value=1, variable=v).pack(fill='both', expand=True)
    tk.Radiobutton(root, text='OCR查词', value=2, variable=v).pack(fill='both', expand=True)
    tk.Button(root, text='运行', command=run).pack(fill='both', expand=True)
    root.mainloop()

# if __name__ == "__main__":
#     print('url:', root_url)
#     print('按ctrl+c+c开始划词。')
#     run_huaci()
