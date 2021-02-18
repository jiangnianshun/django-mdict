import os
import re
import json
import threading
import time
import collections

import pyscreenshot
import pytesseract
import cv2
import numpy as np
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Button, Listener as MouseListener

import pyperclip

# tesseract-OCR训练数据
# https://tesseract-ocr.github.io/tessdoc/Data-Files.html


reg = r'[ _=,.;:!?@%&#~`()\[\]<>{}/\\\$\+\-\*\^\'"\t\n\r，。：；“”（）【】《》？!、·0123456789]'
regp = re.compile(reg)


class Huaci:
    def __init__(self):
        self.start_flag = 0
        self.flag = 0
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

        self.master = None

        self.t1 = 0
        self.t2 = 0

        self.url_dict = collections.OrderedDict()
        self.url_dict['查询'] = 'http://127.0.0.1:8000/mdict/?query=%WORD%'
        self.url_dict['全文查询'] = 'http://127.0.0.1:8000/mdict/es/?query=%WORD%'

        self.p = None

        self.root_dir = os.path.dirname(__file__)
        self.ini_path = os.path.join(self.root_dir, 'huaci.ini')

        if os.path.exists(self.ini_path):
            with open(self.ini_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.url_dict.update(data)
        else:
            with open(self.ini_path, 'w', encoding='utf-8') as f:
                json.dump(self.url_dict, f, indent=4, ensure_ascii=False)
            os.chmod(self.ini_path, 0o777)

        self.root_url = list(self.url_dict.values())[0]  # 这里换有序词典
        print('root url', self.root_url)

        self.lang_con = 'eng'
        self.huaci_mode = 'copy'

        self.timestamp = 0
        self.timestamp2 = 0

        self.thread_mouse = None

        self.thread_keyboard = None

        self.max_text_length = 40

    def translate_picture(self, img):
        # 图片二值化
        gray = cv2.cvtColor(np.asarray(img), cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        invert = 255 - thresh

        text = pytesseract.image_to_string(invert, lang=self.lang_con, config='--psm 6 -c page_separator=""')
        # psm设置布局，小段文本6或7比较好，6可用于横向和竖向文字，7只能用于横向文字，文字方向转90度的用5。
        # tesseract会在末尾加form feed分页符，unicode码000c。
        # -c page_separator=""设置分页符为空
        text = regp.sub('', text)
        if len(text) == 0 or len(text) > self.max_text_length:
            print('text length exceed limit of length', len(text))
            return

        self.search_mdict(text)

    def translate_clipboard(self):
        try:
            # result = root.selection_get(selection="CLIPBOARD").strip()
            # tkinter的剪切板读取必须在mainloop中，当root widthdraw后，就不能用了。
            result = pyperclip.paste().strip()
            if 0 < len(result) <= self.max_text_length:
                self.search_mdict(result)
        except Exception as e:
            print(e)

    def on_click(self, x, y, button, pressed):  # button：鼠标键，pressed：是按下还是抬起
        if self.start_flag == 1:

            if button == Button.left and pressed:

                self.flag += 1

                if self.flag % 2 is 1:
                    self.t1 = time.perf_counter()
                    self.start_x = x
                    self.start_y = y
                else:
                    self.t2 = time.perf_counter()
                    self.end_x = x
                    self.end_y = y

                    if self.end_x == self.start_x or self.end_y == self.start_y:
                        self.flag -= 1
                        print('duplicated click')
                        return

                    if 0 < self.t2 - self.t1 <= 5:
                        if self.start_x < self.end_x and self.start_y < self.end_y:
                            im = pyscreenshot.grab(bbox=(self.start_x, self.start_y, self.end_x, self.end_y))
                            self.translate_picture(im)
                        elif self.start_x < self.end_x and self.start_y > self.end_y:
                            im = pyscreenshot.grab(bbox=(self.start_x, self.end_y, self.end_x, self.start_y))
                            self.translate_picture(im)

                        elif self.start_x > self.end_x and self.start_y < self.end_y:
                            im = pyscreenshot.grab(bbox=(self.end_x, self.start_y, self.start_x, self.end_y))
                            self.translate_picture(im)

                        elif self.start_x > self.end_x and self.start_y > self.end_y:
                            im = pyscreenshot.grab(bbox=(self.end_x, self.end_y, self.start_x, self.start_y))
                            self.translate_picture(im)
                    else:
                        self.init_vars()
                        print('exceed limit of time', self.t2 - self.t1)
        else:
            self.init_vars()

    def on_scroll(self, x, y, dx, dy):
        self.init_vars()

    def clear_timestamp(self):
        self.timestamp = 0
        self.timestamp2 = 0

    def on_press(self, key):
        try:
            if key == Key.ctrl or key == Key.ctrl_l or key == Key.ctrl_r:
                self.clear_timestamp()
                self.timestamp = time.perf_counter()
                return
            elif key.char == '\x03':
                if self.timestamp2 == 0:
                    self.clear_timestamp()
                    self.timestamp2 = time.perf_counter()
                    return
            else:
                if self.timestamp > 0:
                    if key.char == 'c':
                        newtime = time.perf_counter()
                        if newtime - self.timestamp < 0.5:
                            self.clear_timestamp()
                            self.timestamp2 = newtime
                            return
            if self.timestamp2 > 0:
                if key.char == 'c' or key.char == '\x03':
                    newtime = time.perf_counter()
                    if newtime - self.timestamp2 < 0.5:
                        self.clear_timestamp()
                        self.start_flag = 1
                        if self.huaci_mode == 'copy':
                            self.translate_clipboard()
                        elif self.huaci_mode == 'ocr':
                            self.mouse_monitor()
                        return
        except AttributeError as e:
            # 非字母的键没有char这个属性sq
            self.clear_timestamp()

    def thread_mouse_fun(self):
        with MouseListener(on_click=self.on_click, on_scroll=self.on_scroll) as mouse_listener:
            mouse_listener.join()

    def mouse_monitor(self):
        self.thread_mouse = threading.Thread(target=self.thread_mouse_fun)
        self.thread_mouse.daemon = True
        self.thread_mouse.start()
        print('thread_mouse has started')

    def thread_keyboard_fun(self):
        with KeyboardListener(on_press=self.on_press) as keyboard_listener:
            keyboard_listener.join()

    def init_vars(self):
        self.flag = 0
        self.t1 = 0
        self.t2 = 0
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

    def set_master(self, master):
        self.master = master

    def search_mdict(self, query):
        self.start_flag = 0
        self.init_vars()

        url = self.root_url.replace('%WORD%', query)

        browser = self.master.get_browser()

        self.master.main.show_main(url)

        if browser is not None:
            browser.LoadUrl(url)

        self.master.master.title(query)

    def run_huaci(self, hm):
        self.huaci_mode = hm
        if self.thread_keyboard is None:
            self.thread_keyboard = threading.Thread(target=self.thread_keyboard_fun)
            self.thread_keyboard.daemon = True
            self.thread_keyboard.start()
