import os
import sys
import time

import psutil
from multiprocessing.pool import ThreadPool

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django

django.setup()

from mynav.models import Website
from mynav.icon_utils import get_icons_set, process_url


def download_all_icons():
    t1 = time.perf_counter()
    icons_set = get_icons_set()
    sites = Website.objects.all()
    not_exists_list = []
    for site in sites:
        if site.pk not in icons_set:
            # process_url(site.site_url, site.pk)
            not_exists_list.append((site.site_url, site.pk))
        else:
            print(site.site_name, site.site_url, 'has already exists.')
    max_cpu_num = psutil.cpu_count(True)
    if len(not_exists_list) > max_cpu_num:
        cpu_num = max_cpu_num
    else:
        cpu_num = len(not_exists_list)
    thread_pool = ThreadPool(cpu_num)
    thread_pool.starmap(process_url, not_exists_list)
    thread_pool.close()
    t2 = time.perf_counter()
    print('icons download has finished.', t2 - t1)


download_all_icons()
