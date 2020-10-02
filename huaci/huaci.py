import pytesseract
import pyscreenshot as ImageGrab
from pynput import mouse, keyboard
from pynput.mouse import Button
import threading
import time, os, sys
from multiprocessing import Process

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


def translate_picture(img):
    text = pytesseract.image_to_string(img, lang='chi_sim')
    text = text.replace(' ', '').replace("\n", " ").strip()
    if len(text) == 0:
        print('text length is zero')
        return
    if len(text) > 30:
        print('text length exceed limit of length', len(text))
        return

    search_mdict(text)


def on_click(x, y, button, pressed):  # button：鼠标键，pressed：是按下还是抬起
    global start_flag
    global flag
    global start_x
    global start_y
    global end_x
    global end_y
    global t1, t2

    if start_flag is 1:

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
                    init_vars()
                    print('exceed limit of height', abs(end_y - start_y))
                    return
                if abs(end_x - start_x) > 500:
                    init_vars()
                    print('exceed limit of width', abs(end_x - start_x))
                    return

                if end_x == start_x or end_y == start_y:
                    flag -= 1
                    print('duplicated click')
                    return

                if 0 < t2 - t1 <= 3000:
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


def on_press(key):
    global start_flag
    try:
        if key.char == "q":
            start_flag = 0
            init_vars()
            exit_mouse_monitor()
        elif key.char == "s":
            start_flag = 1
            mouse_monitor()
    except AttributeError as e:
        # 非字母的键没有char这个属性sq
        # print('error',e)
        pass


mouse_listener = mouse.Listener(on_click=on_click)


def thread_mouse_fun():
    with mouse.Listener(on_click=on_click, on_scroll=on_scroll) as mouse_listener:
        mouse_listener.join()


thread_mouse = None


def mouse_monitor():
    global thread_mouse
    thread_mouse = threading.Thread(target=thread_mouse_fun)
    thread_mouse.start()
    print('thread_mouse has started')


def exit_mouse_monitor():
    global thread_mousesq
    if thread_mouse is not None:
        # 停止线程
        print('thread_mouse has stopped')


def thread_keyboard_fun():
    with keyboard.Listener(on_press=on_press) as keyboard_listener:
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


def search_mdict(query):
    global start_flag, p, pool, root_url
    start_flag = 0
    init_vars()

    if p != None:
        p.terminate()
    p = Process(target=search, args=(query, root_url))
    p.daemon = True
    p.start()


def run_huaci():
    thread_keyboard = threading.Thread(target=thread_keyboard_fun)
    thread_keyboard.start()


if __name__ == "__main__":
    print('按s键开启划词，按q键关闭划词。')
    run_huaci()
