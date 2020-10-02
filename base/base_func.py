import mimetypes
import os, re, inspect, json
from enum import IntEnum
from mysite.settings import BASE_DIR
from django.http.request import QueryDict

font_path = os.path.join(BASE_DIR, 'media', 'font')


def get_log_header(mod_name, debug_level, start=-1, end=-1):
    if debug_level == DebugLevel.error:
        dl = 'ERROR'
    elif debug_level == DebugLevel.warning:
        dl = 'WARNING'

    if debug_level == DebugLevel.debug:
        header = '[' + mod_name.upper() + ']'
    else:
        header = '[' + mod_name.upper() + ' ' + dl + ']'

    if end > 0 and start > 0:
        return header + ' ' + get_running_time(start, end)
    else:
        return header


class DebugLevel(IntEnum):
    debug = 0
    warning = 1
    error = 2


def print_log_info(log_content='', debug_level=DebugLevel.debug, start=-1, end=-1):
    prev_frame = inspect.getframeinfo(inspect.currentframe().f_back)
    # currentframe()是当前函数，f_back是上一帧，即调用函数
    # prev_frame,0是文件路径，1是行数，2是函数名（如果不在函数里，显示<module>），3显示调用本函数的那一行代码，4索引
    prev_file = os.path.basename(prev_frame[0]).split('.')[0]
    prev_func = prev_frame[2]
    if prev_func == '<module>':
        mod_name = prev_file
    else:
        mod_name = prev_file + '.' + prev_func

    print(get_log_header(mod_name, debug_level, start, end), log_content)


def get_running_time(start, end):
    return '[' + str(round(abs(end - start), 4)) + 's' + ']'


def is_en_func(s):  # 是否纯英文
    zhmodel = re.compile(r'^[ \'a-zA-Z\-]+$')
    match = zhmodel.search(s)
    if match:
        return True
    else:
        return False


def conatain_upper_characters(s):
    zhmodel = re.compile(r'[A-Z]')
    match = zhmodel.search(s)
    if match:
        return True
    else:
        return False


def strQ2B(ustring):
    """把字符串全角转半角"""
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        # ord返回字符的十六进制数
        if inside_code == 0x3000:
            inside_code = 0x0020
        else:
            inside_code -= 0xfee0
        if inside_code < 0x0020 or inside_code > 0x7e:  # 转完之后不是半角字符返回原来的字符
            rstring += uchar
        else:
            rstring += chr(inside_code)
            # 将十六进制数转换回字符
    return rstring


def request_body_serialze(request):
    # 对request.body做QuertDict编码转换处理
    # 如果不做数据处理：格式b'id=49&name=%E4%B8%AD&name_cn=&comment='
    # 页面中提交的中文“中”，变成%E4%B8%AD
    querydict = QueryDict(request.body.decode("utf-8"), encoding="utf-8")
    response_dict = {}
    try:
        for key, val in querydict.items():
            response_dict[key] = json.loads(val)
    except:
        pass
    return response_dict


def guess_mime(f_name):
    mime_type = mimetypes.guess_type(f_name)[0]
    if mime_type is None:
        if f_name.endswith('.spx'):
            mime_type = 'audio/x-speex'
    return mime_type