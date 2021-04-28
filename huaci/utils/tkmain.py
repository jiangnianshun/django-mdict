import win32api
import win32con
import win32gui
from cefpython3 import cefpython as cef
import ctypes
from ctypes import windll

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk

import sys
import pystray
from pystray import MenuItem as item

try:
    from .tkconfig import ConfigWindow
    from .tkhuaci import *
    from .tkbase import *
    from .tkini import get_huaci_config
except Exception:
    from tkconfig import ConfigWindow
    from tkhuaci import *
    from tkbase import *
    from tkini import get_huaci_config

# Fix for PyCharm hints warnings
WindowUtils = cef.WindowUtils()

# Constants
# Tk 8.5 doesn't support png images
IMAGE_EXT = ".png" if tk.TkVersion > 8.5 else ".gif"

GWL_EXSTYLE = -20
WS_EX_APPWINDOW = 0x00040000
# WS_EX_TOOLWINDOW=0x00000080

sys.path.append(os.path.abspath(__file__))

count = 0

myappid = 'django-mdict'  # arbitrary string
windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

huaci_config = get_huaci_config()
cef_config = huaci_config['cef']


class MainWindow:
    def __init__(self):
        assert cef.__version__ >= "55.3", "CEF Python v55.3+ required to run this"
        sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
        # Tk must be initialized before CEF otherwise fatal error (Issue #306)

        self.root = tk.Tk()

        self.root.attributes('-topmost', True)
        # 永久窗口置顶，而lift()是暂时置顶。
        self.create_mask()
        self.huaci = Huaci(self.root)
        self.huaci.run_huaci('copy')
        self.init_param()

        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)

        tkwidth = cef_config['tkwidth']
        tkheight = cef_config['tkheight']
        xpos = cef_config['xpos']
        ypos = cef_config['ypos']

        self.app = MainFrame(self)
        pos = str(tkwidth) + "x" + str(tkheight) + "+" + str(xpos) + "+" + str(ypos)
        self.root.geometry(pos)
        # 宽度x高度+左端距离+上端距离

        settings = {'cache_path': 'huaci.cache'}

        if 'auto_zooming' in cef_config.keys():
            settings.update({'auto_zooming': cef_config['auto_zooming']})

        cef.Initialize(settings=settings)
        self.create_systray()
        self.root.withdraw()
        self.app.mainloop()

        cef.Shutdown()

    def init_param(self):
        self.query = ''
        self.param = ''
        self.url = self.huaci.root_url
        flag = self.url.find('?')
        if flag > -1:
            self.param = self.url[flag:]
            self.url = self.url[:flag]

    def quit_window(self, icon, item):
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
        # 设置任务栏的图标为窗口的图标
        self.root.wm_withdraw()
        self.root.after(10, lambda: self.root.wm_deiconify())
        set_icon(self.root)

    def show_main(self, query):
        self.icon.stop()
        self.root.after(0, self.root.deiconify)
        self.root.after(10, self.set_appwindow)
        set_icon(self.root)
        self.query = query

    def show_window(self, icon, item):
        icon.stop()
        self.root.after(0, self.root.deiconify)
        self.root.after(10, self.set_appwindow)
        set_icon(self.root)

    def create_systray(self):
        ypos = cef_config['ypos']
        cef_config['typos'] = ypos + 40
        # 显示系统托盘
        image = get_icon()
        # 这里如果用相对路径default.ico，那么用bat调用时报错。
        self.menu = pystray.Menu(item('打开', self.show_window, default=True),
                                 item('退出', self.quit_window))
        # 这里menu应该用pystray.Menu()，如果直接使用tuple，那么左键单击报错，其他功能正常。
        # 鼠标左键点击托盘图标运行default=True的Menuitem，如果default均为False，则无动作。
        self.icon = pystray.Icon("djangomdict", icon=image, title='django-mdict', menu=self.menu)
        if self.huaci.master is None:
            self.huaci.set_master(self)
        self.icon.run()

    def hide_window(self):
        # 隐藏窗口
        self.root.withdraw()
        self.create_systray()

    def create_mask(self):
        self.mask = tk.Toplevel()
        self.mask.attributes('-topmost', True)
        self.mask.attributes('-fullscreen', True)
        self.mask.attributes("-alpha", 0.2)
        self.mask.protocol('WM_DELETE_WINDOW', self.mask.withdraw)
        self.create_canvas()
        self.mask.withdraw()

    def show_mask(self):
        self.icon.stop()
        # 需要先停止托盘
        self.mask.after(0, self.mask.deiconify)

    def hide_mask(self):
        self.mask.withdraw()

    def create_canvas(self):
        self.canvas = tk.Canvas(self.mask, bg='black')
        self.canvas.pack(anchor='nw')
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def create_rectangle(self, x1, y1, x2, y2):
        self.canvas.create_rectangle(x1, y1, x2, y2, fill='white', outline='white')

    def clear_rectangle(self):
        if self.canvas is not None:
            self.canvas.delete("all")


class MainFrame(tk.Frame):
    def __init__(self, main):
        self.browser_frame = None
        self.navigation_bar = None
        self.main = main
        self.root = main.root

        # Root
        self.root.geometry("900x640")
        tk.Grid.rowconfigure(self.root, 0, weight=1)
        tk.Grid.columnconfigure(self.root, 0, weight=1)

        # MainFrame
        tk.Frame.__init__(self, self.root)
        self.master.title("词典")
        self.master.bind("<Configure>", self.on_root_configure)
        self.bind("<Configure>", self.on_configure)

        # NavigationBar
        self.navigation_bar = NavigationBar(self)
        self.navigation_bar.grid(row=0, column=0,
                                 sticky=(tk.N + tk.S + tk.E + tk.W))
        tk.Grid.rowconfigure(self, 0, weight=0)
        tk.Grid.columnconfigure(self, 0, weight=0)

        # BrowserFrame
        self.browser_frame = BrowserFrame(self, self.navigation_bar, self.main)
        self.browser_frame.grid(row=1, column=0,
                                sticky=(tk.N + tk.S + tk.E + tk.W))
        tk.Grid.rowconfigure(self, 1, weight=1)
        tk.Grid.columnconfigure(self, 0, weight=1)

        # Pack MainFrame
        self.pack(fill=tk.BOTH, expand=tk.YES)

    def on_root_configure(self, _):
        if self.browser_frame:
            self.browser_frame.on_root_configure()

    def on_configure(self, event):
        if self.browser_frame:
            width = event.width
            height = event.height
            if self.navigation_bar:
                height = height - self.navigation_bar.winfo_height()
            self.browser_frame.on_mainframe_configure(width, height)

    def get_browser(self):
        if self.browser_frame:
            return self.browser_frame.browser
        return None

    def get_browser_frame(self):
        if self.browser_frame:
            return self.browser_frame
        return None


class BrowserFrame(tk.Frame):
    def __init__(self, mainframe, navigation_bar=None, main=None):
        self.navigation_bar = navigation_bar
        self.closing = False
        self.browser = None
        self.main = main

        tk.Frame.__init__(self, mainframe)
        self.mainframe = mainframe
        self.bind("<Configure>", self.on_configure)
        """For focus problems see Issue #255 and Issue #535. """
        self.focus_set()

    def create_browser(self):
        global count
        window_info = cef.WindowInfo()

        rect = [0, 0, self.winfo_width(), self.winfo_height()]
        window_info.SetAsChild(self.get_window_handle(), rect)
        if '%WORD%' in self.main.param:
            url = self.main.url + self.main.param.replace('%WORD%', self.main.query)
        else:
            url = self.main.url + '?query=' + self.main.query

        return cef.CreateBrowserSync(window_info, url=url)

    def embed_browser(self):
        if self.browser is None:
            self.browser = self.create_browser()
        assert self.browser
        self.browser.SetClientHandler(LifespanHandler())
        self.message_loop_work()

    def get_window_handle(self):
        if self.winfo_id() > 0:
            return self.winfo_id()
        else:
            raise Exception("Couldn't obtain window handle")

    def message_loop_work(self):
        cef.MessageLoopWork()
        self.after(10, self.message_loop_work)

    def on_configure(self, _):
        if not self.browser:
            self.embed_browser()

    def on_root_configure(self):
        # Root <Configure> event will be called when top window is moved
        if self.browser:
            self.browser.NotifyMoveOrResizeStarted()

    def on_mainframe_configure(self, width, height):
        if self.browser:
            ctypes.windll.user32.SetWindowPos(
                self.browser.GetWindowHandle(), 0,
                0, 0, width, height, 0x0002)
            self.browser.NotifyMoveOrResizeStarted()


def create_window_info(class_name):
    window_proc = {
        win32con.WM_CLOSE: close_window,
        # win32con.WM_DESTROY: exit_app,#生成多个窗口，关闭一个会关闭所有窗口
        win32con.WM_SIZE: WindowUtils.OnSize,
        win32con.WM_SETFOCUS: WindowUtils.OnSetFocus,
        win32con.WM_ERASEBKGND: WindowUtils.OnEraseBackground,
    }
    # 每个窗口的class_name不能相同

    tkwidth = cef_config['tkwidth']
    tkheight = cef_config['tkheight']

    window_handle = create_window(title='词典',
                                  class_name=class_name,
                                  width=tkwidth,
                                  height=tkheight,
                                  window_proc=window_proc)

    window_info = cef.WindowInfo()
    window_info.SetAsChild(window_handle)

    return window_info


def create_window(title, class_name, width, height, window_proc):
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

    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # 设置任务栏的图标为窗口的图标

    xpos = cef_config['xpos']
    typos = cef_config['typos']

    # Create window
    window_style = (win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN
                    | win32con.WS_VISIBLE)
    window_handle = win32gui.CreateWindow(class_name, title, window_style,
                                          xpos, typos, width, height,
                                          0, 0, wndclass.hInstance, None)

    assert (window_handle != 0)
    win32gui.SetWindowPos(window_handle, win32con.HWND_TOPMOST, xpos, typos, width, height, win32con.SWP_SHOWWINDOW)
    # win32con.HWND_TOPMOST窗口置顶
    cef_config['typos'] += 40

    # Window icon
    icon = ico_path
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


class LifespanHandler():
    def OnBeforePopup(self, **kwargs):
        global count
        url = kwargs['target_url']
        window_info = create_window_info('win' + str(count))
        count += 1
        browser = cef.CreateBrowserSync(window_info=window_info, url=url,
                                        window_title="词典")
        browser.SetClientHandler(LifespanHandler())
        return True


class NavigationBar(tk.Frame):

    def __init__(self, master):
        self.back_state = tk.NONE
        self.forward_state = tk.NONE
        self.back_image = None
        self.forward_image = None
        self.reload_image = None
        self.main = master.main
        self.setting = ConfigWindow(self.main)

        tk.Frame.__init__(self, master)
        resources = os.path.join(os.path.dirname(__file__), "resources")

        # Back button
        back_png = os.path.join(resources, "back" + IMAGE_EXT)
        if os.path.exists(back_png):
            self.back_image = tk.PhotoImage(file=back_png)
        self.back_button = tk.Button(self, image=self.back_image,
                                     command=self.go_back)
        self.back_button.grid(row=0, column=0)

        # Forward button
        forward_png = os.path.join(resources, "forward" + IMAGE_EXT)
        if os.path.exists(forward_png):
            self.forward_image = tk.PhotoImage(file=forward_png)
        self.forward_button = tk.Button(self, image=self.forward_image,
                                        command=self.go_forward)
        self.forward_button.grid(row=0, column=1)

        # Reload button
        reload_png = os.path.join(resources, "reload" + IMAGE_EXT)
        if os.path.exists(reload_png):
            self.reload_image = tk.PhotoImage(file=reload_png)
        self.reload_button = tk.Button(self, image=self.reload_image,
                                       command=self.reload)
        self.reload_button.grid(row=0, column=2)

        # settings button
        setting_png = os.path.join(resources, "setting" + IMAGE_EXT)
        if os.path.exists(setting_png):
            self.setting_image = tk.PhotoImage(file=setting_png)
        self.setting_button = tk.Button(self, image=self.setting_image,
                                        command=self.show_setting)
        self.setting_button.grid(row=0, column=4)

    def go_back(self):
        if self.master.get_browser():
            self.master.get_browser().GoBack()

    def go_forward(self):
        if self.master.get_browser():
            self.master.get_browser().GoForward()

    def reload(self):
        if self.master.get_browser():
            self.master.get_browser().Reload()

    def show_setting(self):
        self.setting.show_window()
