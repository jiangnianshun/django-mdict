import os
import sys
import time
import pickle
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from base.base_func import ROOT_DIR
from base.sys_utils import check_system
from mdict.mdict_utils.mdict_func import set_mdict_path
from mdict.mdict_utils.init_utils import rewrite_cache

if check_system() == 0:
    cache_name = '.Linux.dat'
elif check_system() == 1:
    cache_name = '.Windows.dat'
else:
    cache_name = ''

cache_path = os.path.join(ROOT_DIR, '.cache', cache_name)
dir_status = False


class DirWatch:
    def __init__(self, target_dir=''):
        self.observer = Observer()
        self.target_dir = target_dir

    def run(self):
        global dir_status
        event_handler = Handler()
        self.observer.schedule(event_handler, self.target_dir, recursive=True)
        self.observer.start()

        try:
            while True:
                mdict_root_path, audio_path, mdict_path_list, audio_path_list = set_mdict_path()
                if mdict_root_path != self.target_dir:
                    print('mdict root path changed!')
                    rewrite_cache(mdict_root_path)
                    self.target_dir = mdict_root_path
                    dir_status = False
                elif dir_status is True:
                    print('watch dog changed!')
                    rewrite_cache(mdict_root_path)
                    self.target_dir = mdict_root_path
                    dir_status = False
                time.sleep(10)
        except:
            self.observer.stop()
            print("Wd Observer Stopped")
        self.observer.join()

    def stop(self):
        self.observer.stop()

    def set(self, target_dir):
        self.target_dir = target_dir


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        global dir_status
        if not event.is_directory and event.event_type != 'deleted':
            if event.src_path.lower().endswith('.mdx'):
                # print(event.event_type, event.src_path)
                dir_status = True


if __name__ == '__main__':
    if cache_name != '' and os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)

        if os.path.exists(data['root_dir']):
            watch = DirWatch(data['root_dir'])
            watch.run()
        else:
            print('mdict root path not exists!')
    else:
        print('cache data file not exists!')
