import re
import threading
import time
import collections

import pyscreenshot
import pytesseract
# import cv2
# import numpy as np
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Button, Listener as MouseListener

import pyperclip

try:
    from .tkini import get_huaci_config
    from .tkbase import data_path
except Exception:
    from tkini import get_huaci_config
    from tkbase import data_path

# tesseract-OCR训练数据
# https://tesseract-ocr.github.io/tessdoc/Data-Files.html


reg = r'[ _=,.;:!?@%&#~`()\[\]<>{}/\\\$\+\-\*\^\'"\t\n\r，。：；“”（）【】《》？!、·0123456789]'
regp = re.compile(reg)


class Huaci:
    def __init__(self, master):
        self.start_flag = 0
        self.flag = 0
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

        self.master = master

        self.master = None

        self.t1 = 0
        self.t2 = 0

        self.url_dict = collections.OrderedDict()
        self.url_dict['查询'] = 'http://127.0.0.1:8000/mdict/?query=%WORD%'
        self.url_dict['全文查询'] = 'http://127.0.0.1:8000/mdict/es/?query=%WORD%'

        self.p = None

        self.url_dict = get_huaci_config()['url']

        self.root_url = list(self.url_dict.values())[0]  # 这里换有序词典
        self.old_root_url = self.root_url
        print('root url:', self.root_url)

        self.lang_con = 'eng'
        self.huaci_mode = 'copy'

        self.timestamp = 0
        self.timestamp2 = 0

        self.thread_mouse = None

        self.thread_keyboard = None

        self.max_text_length = 40

    def translate_picture(self, img):
        tess_cmd = '--psm 6 --oem 1 -c lstm_choice_iterations=0 -c page_separator=""'
        if data_path != '':
            tess_cmd += ' --tessdata-dir ' + data_path

        # img = np.asarray(img)
        # shape = img.shape
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # if shape[0] < 40 or shape[1] < 40:
        #     # 图片放大
        #     img = cv2.resize(np.asarray(img), None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)

        # kernel = np.ones((1, 1), np.uint8)
        # img = cv2.dilate(img, kernel, iterations=1)
        # img = cv2.erode(img, kernel, iterations=1)
        # img = cv2.adaptiveThreshold(cv2.medianBlur(img, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #                             cv2.THRESH_BINARY, 31, 3)

        # text = pytesseract.image_to_string(img, lang=self.lang_con, config=tess_cmd)
        data = pytesseract.image_to_data(img, lang=self.lang_con, config=tess_cmd)
        data_list = [line.split('\t') for line in data.split('\n')]
        text = ''
        for data in data_list[1:]:
            # 去重重复
            if len(data) == 12 and data[5] == '1' and data[-1] != '':
                text += data[-1][0]

        # psm设置布局，小段文本6或7比较好，6可用于横向和竖向文字，7只能用于横向文字，文字方向转90度的用5。
        # tesseract会在末尾加form feed分页符，unicode码000c。
        # -c page_separator=""设置分页符为空
        text = regp.sub('', text)
        # if len(text) == 0 or len(text) > self.max_text_length:
        #     print('text length exceed limit of length', len(text))
        #     return

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

        if self.start_flag == 1 and self.huaci_mode == 'ocr':

            if button == Button.left and pressed:

                self.flag += 1

                if self.flag % 2 == 1:
                    self.t1 = time.perf_counter()
                    self.start_x = x
                    self.start_y = y
                else:
                    self.t2 = time.perf_counter()
                    self.end_x = x
                    self.end_y = y

                    if self.end_x == self.start_x or self.end_y == self.start_y:
                        self.flag -= 1
                        # print('duplicated click')
                        return

                    if 0 < self.t2 - self.t1 <= 5:
                        if self.start_x < self.end_x and self.start_y < self.end_y:
                            im = pyscreenshot.grab(bbox=(self.start_x, self.start_y, self.end_x, self.end_y))
                            self.master.clear_rectangle()
                            self.master.hide_mask()
                            self.translate_picture(im)
                        elif self.start_x < self.end_x and self.start_y > self.end_y:
                            im = pyscreenshot.grab(bbox=(self.start_x, self.end_y, self.end_x, self.start_y))
                            self.master.clear_rectangle()
                            self.master.hide_mask()
                            self.translate_picture(im)

                        elif self.start_x > self.end_x and self.start_y < self.end_y:
                            im = pyscreenshot.grab(bbox=(self.end_x, self.start_y, self.start_x, self.end_y))
                            self.master.clear_rectangle()
                            self.master.hide_mask()
                            self.translate_picture(im)

                        elif self.start_x > self.end_x and self.start_y > self.end_y:
                            im = pyscreenshot.grab(bbox=(self.end_x, self.end_y, self.start_x, self.start_y))
                            self.master.clear_rectangle()
                            self.master.hide_mask()
                            self.translate_picture(im)
                    else:
                        self.init_vars()
                        # print('exceed limit of time', self.t2 - self.t1)
        else:
            self.init_vars()

    def on_scroll(self, x, y, dx, dy):
        self.init_vars()

    def set_mask(self, x, y):
        if self.start_flag == 1 and self.huaci_mode == 'ocr':
            self.master.show_mask()
            self.master.clear_rectangle()
            if self.flag % 2 == 1:
                tx1 = self.start_x
                tx2 = x
                ty1 = self.start_y
                ty2 = y
                if x < self.start_x:
                    tx1 = x
                    tx2 = self.start_x
                if y < self.start_y:
                    ty1 = y
                    ty2 = self.start_y
                self.master.create_rectangle(tx1, ty1, tx2, ty2)

    def on_move(self, x, y):
        self.set_mask(x, y)

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
                            # self.set_mask(0, 0)
                            pass
                        return
        except AttributeError as e:
            # 非字母的键没有char这个属性sq
            self.clear_timestamp()

    def thread_mouse_fun(self):
        with MouseListener(on_click=self.on_click, on_scroll=self.on_scroll, on_move=self.on_move) as mouse_listener:
            mouse_listener.join()

    def mouse_monitor(self):
        self.thread_mouse = threading.Thread(target=self.thread_mouse_fun)
        self.thread_mouse.daemon = True
        self.thread_mouse.start()

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

        browser = self.master.app.get_browser()

        self.master.show_main(query)

        if browser is not None:
            if self.root_url != self.old_root_url:
                self.master.init_param()
                url = self.root_url.replace('%WORD%', query)
                browser.LoadUrl(url)
                self.old_root_url = self.root_url
            else:
                browser.ExecuteFunction('call_query', query)

        self.master.root.title(query)

    def run_huaci(self, hm):
        self.huaci_mode = hm
        if self.thread_keyboard is None:
            self.thread_keyboard = threading.Thread(target=self.thread_keyboard_fun)
            self.thread_keyboard.daemon = True
            self.thread_keyboard.start()
        if self.thread_mouse is None:
            self.mouse_monitor()
