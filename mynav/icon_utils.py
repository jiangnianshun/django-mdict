import os
import re
import io
import gzip
import requests
from requests.exceptions import ConnectionError, ReadTimeout, TooManyRedirects
from multiprocessing import Process

from base.base_utils import ROOT_DIR

icon_root_path = os.path.join(ROOT_DIR, 'media', 'icon')

max_time = (3, 10)

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/94.0.4606.71 Safari/537.36 '}


def get_icon_root_path():
    if not os.path.exists(icon_root_path):
        os.mkdir(icon_root_path)
    return icon_root_path


def add_url_protocol(url, prefix='https'):
    if not url.startswith('http'):
        if url.startswith('//'):
            url = f'{prefix}:{url}'
        else:
            url = f'{prefix}://{url}'
    return url


def get_icon_url(url):
    if url.endswith('/'):
        url = f'{url}favicon.ico'
    else:
        url = f'{url}/favicon.ico'
    return url


def unzip(content):
    buf = io.BytesIO(content)
    gf = gzip.GzipFile(fileobj=buf)
    content = gf.read()
    return content


def get_url_host(url):
    mark1 = url.find('//')
    if mark1 > -1:
        tmp_url = url[mark1 + 2:]
        mark2 = tmp_url.find('/')
        return url[:mark1 + 2] + tmp_url[:mark2]
    else:
        mark2 = url.find('/')
        return url[:mark2]


def get_icon_link(html, url):
    reg = r'<link rel="shortcut icon"[\s\S]*?/>'
    # .*是除换行符外的任意字符，[\s\S]*是包括换行符的任意字符。
    link_list = re.compile(reg).findall(html)
    link = ""
    if len(link_list) > 0:
        link = link_list[0]
        mark = link.find('href="')
        link = link[mark + 6:]
        mark = link.find('"')
        link = link[:mark]
    if link.startswith('/'):
        if url[-1] == '/':
            link = url + link[1:]
        else:
            link = get_url_host(url) + link
    return link


def get_page(url, stream=True):
    text = ''
    content = b''
    try:
        req = requests.get(url, headers=header, stream=stream, timeout=max_time)
        text = req.text
        if req.status_code == 200:
            if req.encoding == 'gzip':
                content = unzip(req.content)
            else:
                content = req.content
            print(url, 'success download.')
        else:
            print(url, 'status_code:', req.status_code)
        req.close()
    except ConnectionError as e:
        # ConnectionError包含ConnectTimeout
        print(url, e)
    except ReadTimeout as e:
        print(url, e)
    except TooManyRedirects as e:
        print(url, e)
    except ValueError as e:
        print(url, e)
    return text, content


def download_icon(url):
    if url.endswith('.ico'):
        icon_url = url
    else:
        icon_url = get_icon_url(url)
    text, content = get_page(icon_url)
    return content


def get_url_html(url):
    text, content = get_page(url, stream=False)
    return text


def process_url(url, id):
    root_url = get_url_host(url)
    new_url = add_url_protocol(root_url, 'https')
    icon_data = download_icon(new_url)
    if len(icon_data) == 0:
        if not url.startswith('http'):
            new_url = add_url_protocol(root_url, 'http')
            icon_data = download_icon(new_url)
    if len(icon_data) == 0:
        text, content = get_page(url)
        if len(text) > 0:
            link = get_icon_link(text, root_url)
            icon_data = download_icon(link)
    if len(icon_data) > 0:
        icon_name = str(id) + '.ico'
        icon_path = os.path.join(icon_root_path, icon_name)
        with open(icon_path, 'wb') as f:
            f.write(icon_data)


def get_icons_set():
    icons_set = set()
    icon_path = get_icon_root_path()
    for file in os.listdir(icon_path):
        if file.endswith('.ico') and file.split('.')[0].isdigit():
            icons_set.add(int(file.split('.')[0]))
    return icons_set


def get_icon(url, id):
    p = Process(target=process_url, args=(url, id))
    p.start()
