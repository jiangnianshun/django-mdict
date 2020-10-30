import math
import os
import platform
import sys
from ctypes import windll

import win32api
import win32con
import win32gui
from cefpython3 import cefpython as cef

WindowUtils = cef.WindowUtils()

i = 0


class LifespanHandler():
    def OnBeforePopup(self, **kwargs):
        global i
        url = kwargs['target_url']
        window_info = create_window_info('win' + str(i))
        i += 1
        browser = cef.CreateBrowserSync(window_info=window_info, url=url,
                                        window_title="词典")

        browser.SetClientHandler(LifespanHandler())
        return True


def search(query, root_url):
    global i

    print('query:', query)

    url = root_url
    if url.find('?') > -1:
        url += '&query=' + query
    else:
        url += '?query=' + query

    # check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()

    window_info = create_window_info('win' + str(i))
    i += 1

    browser = cef.CreateBrowserSync(window_info=window_info, url=url,
                                    window_title="词典")

    browser.SetClientHandler(LifespanHandler())
    # browser.LoadUrl('http://www.baidu.com')
    cef.MessageLoop()
    cef.Shutdown()  # 清除所有资源


def check_versions():
    ver = cef.GetVersion()
    print("[huaci.pyw] CEF Python {ver}".format(ver=ver["version"]))
    print("[huaci.pyw] Chromium {ver}".format(ver=ver["chrome_version"]))
    print("[huaci.pyw] CEF {ver}".format(ver=ver["cef_version"]))
    print("[huaci.pyw] Python {ver} {arch}".format(
        ver=platform.python_version(),
        arch=platform.architecture()[0]))
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"


def create_window_info(class_name):
    window_proc = {
        win32con.WM_CLOSE: close_window,
        # win32con.WM_DESTROY: exit_app,#生成多个窗口，关闭一个会关闭所有窗口
        win32con.WM_SIZE: WindowUtils.OnSize,
        win32con.WM_SETFOCUS: WindowUtils.OnSetFocus,
        win32con.WM_ERASEBKGND: WindowUtils.OnEraseBackground,
    }
    # 每个窗口的class_name不能相同
    window_handle = create_window(title='词典',
                                  class_name=class_name,
                                  width=500,
                                  height=800,
                                  window_proc=window_proc,
                                  icon="default.ico")
    window_info = cef.WindowInfo()
    window_info.SetAsChild(window_handle)

    return window_info


def create_window(title, class_name, width, height, window_proc, icon):
    # Register window class
    wndclass = win32gui.WNDCLASS()
    wndclass.hInstance = win32api.GetModuleHandle(None)
    wndclass.lpszClassName = class_name
    wndclass.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
    wndclass.hbrBackground = win32con.COLOR_WINDOW
    wndclass.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
    wndclass.lpfnWndProc = window_proc
    atom_class = win32gui.RegisterClass(wndclass)
    assert (atom_class != 0)

    myappid = 'djangomdict.version'  # arbitrary string
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # 设置任务栏的图标为窗口的图标

    # Center window on screen.
    screenx = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screeny = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    xpos = int(math.floor((screenx * 0.2 - width) / 2))
    ypos = int(math.floor((screeny - height) / 2))
    if xpos < 0:
        xpos = 0
    if ypos < 0:
        ypos = 0

    # Create window
    window_style = (win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN
                    | win32con.WS_VISIBLE)
    window_handle = win32gui.CreateWindow(class_name, title, window_style,
                                          xpos, ypos, width, height,
                                          0, 0, wndclass.hInstance, None)

    assert (window_handle != 0)
    win32gui.SetWindowPos(window_handle, win32con.HWND_TOPMOST, xpos, ypos, width, height, win32con.SWP_SHOWWINDOW)
    # win32con.HWND_TOPMOST窗口置顶

    # Window icon
    icon = os.path.abspath(icon)
    if not os.path.isfile(icon):
        icon = None
    if icon:
        # Load small and big icon.
        # WNDCLASSEX (along with hIconSm) is not supported by pywin32,
        # we need to use WM_SETICON message after window creation.
        # Ref:
        # 1. http://stackoverflow.com/questions/2234988
        # 2. http://blog.barthe.ph/2009/07/17/wmseticon/
        bigx = win32api.GetSystemMetrics(win32con.SM_CXICON)
        bigy = win32api.GetSystemMetrics(win32con.SM_CYICON)
        big_icon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON,
                                      bigx, bigy,
                                      win32con.LR_LOADFROMFILE)
        smallx = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        smally = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        small_icon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON,
                                        smallx, smally,
                                        win32con.LR_LOADFROMFILE)
        win32api.SendMessage(window_handle, win32con.WM_SETICON,
                             win32con.ICON_BIG, big_icon)
        win32api.SendMessage(window_handle, win32con.WM_SETICON,
                             win32con.ICON_SMALL, small_icon)
    return window_handle


def close_window(window_handle, message, wparam, lparam):
    browser = cef.GetBrowserByWindowHandle(window_handle)
    browser.CloseBrowser(True)
    # OFF: win32gui.DestroyWindow(window_handle)
    return win32gui.DefWindowProc(window_handle, message, wparam, lparam)


def exit_app(*_):
    win32gui.PostQuitMessage(0)
    return 0


if __name__ == '__main__':
    search('龙', 'http://127.0.0.1:8000/mdict')
