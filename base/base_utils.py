import inspect
import json
import mimetypes
import os
import re
import sqlite3

from django.http.request import QueryDict
from base.base_constant import regp

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_log_header(mod_name, debug_level, start=-1, end=-1):
    dl = ''
    if debug_level == 2:
        dl = 'ERROR'
    elif debug_level == 1:
        dl = 'WARNING'

    if debug_level == 0:
        header = '[' + mod_name.upper() + ']'
    else:
        header = '[' + mod_name.upper() + ' ' + dl + ']'

    if end > 0 and start > 0:
        return header + ' ' + get_running_time(start, end)
    else:
        return header


def print_log_info(log_content='', debug_level=0, start=-1, end=-1):
    prev_frame = inspect.getframeinfo(inspect.currentframe().f_back)
    # currentframe()是当前函数，f_back是上一帧，即调用函数
    # prev_frame,0是文件路径，1是行数，2是函数名（如果不在函数里，显示<module>），3显示调用本函数的那一行代码，4索引
    prev_file = os.path.basename(prev_frame[0]).split('.')[0]
    prev_func = prev_frame[2]
    if prev_func == '<module>':
        mod_name = prev_file
    else:
        mod_name = prev_file + '.' + prev_func

    log_text = ''
    if isinstance(log_content, str):
        log_text = log_content
    elif isinstance(log_content, list):
        for content in log_content:
            log_text = log_text + ' ' + str(content)
        log_text = log_text[1:]

    print(get_log_header(mod_name, debug_level, start, end) + ' ' + log_text)


def check_readlib():
    try:
        from mdict.readlib.lib.pureSalsa20 import Salsa20
    except ImportError as e:
        print_log_info('loading mdict.readlib.lib.pureSalsa20 failed!', 1)

    try:
        from mdict.readlib.lib.ripemd128 import ripemd128
    except ImportError as e:
        print_log_info('loading mdict.readlib.lib.ripemd128 failed!', 1)

    try:
        from mdict.readlib.lib.readmdict import MDX, MDD
    except ImportError as e:
        print_log_info('loading mdict.readlib.lib.readmdict failed!', 1)

    try:
        from mdict.readlib.lib.readzim import ZIMFile
    except ImportError as e:
        print_log_info('loading mdict.readlib.lib.readzim failed!', 1)


def get_running_time(start, end):
    return '[' + str(round(abs(end - start), 4)) + 's' + ']'


def is_en_func(s):
    # 是否纯英文字母(全角和半角)
    s = regp.sub('', s)
    if s == '':
        return False
    zhmodel = re.compile(r'^[a-zA-Zａ-ｚＡ-Ｚ]+$')
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
    """英文字母全角转半角"""
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
    querydict = QueryDict(request.body.decode("utf-8", errors='replace'), encoding="utf-8")
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


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


kana = {
    'あ': 'ア', 'い': 'イ', 'う': 'ウ', 'え': 'エ', 'お': 'オ',
    'か': 'カ', 'き': 'キ', 'く': 'ク', 'け': 'ケ', 'こ': 'コ',
    'さ': 'サ', 'し': 'シ', 'す': 'ス', 'せ': 'セ', 'そ': 'ソ',
    'た': 'タ', 'ち': 'チ', 'つ': 'ツ', 'て': 'テ', 'と': 'ト',
    'な': 'ナ', 'に': 'ニ', 'ぬ': 'ヌ', 'ね': 'ネ', 'の': 'ノ',
    'は': 'ハ', 'ひ': 'ヒ', 'ふ': 'フ', 'へ': 'ヘ', 'ほ': 'ホ',
    'ま': 'マ', 'み': 'ミ', 'む': 'ム', 'め': 'メ', 'も': 'モ',
    'や': 'ヤ', 'ゆ': 'ユ', 'よ': 'ヨ',
    'ら': 'ラ', 'り': 'リ', 'る': 'ル', 'れ': 'レ', 'ろ': 'ロ',
    'わ': 'ワ', 'を': 'ヲ', 'ん': 'ン',
    'が': 'ガ', 'ぎ': 'ギ', 'ぐ': 'グ', 'げ': 'ゲ', 'ご': 'ゴ',
    'ざ': 'ザ', 'じ': 'ジ', 'ず': 'ズ', 'ぜ': 'ゼ', 'ぞ': 'ゾ',
    'だ': 'ダ', 'ぢ': 'ヂ', 'づ': 'ヅ', 'で': 'デ', 'ど': 'ド',
    'ば': 'バ', 'び': 'ビ', 'ぶ': 'ブ', 'べ': 'ベ', 'ぼ': 'ボ',
    'ぱ': 'パ', 'ぴ': 'ピ', 'ぷ': 'プ', 'ぺ': 'ペ', 'ぽ': 'ポ',
    'ぁ': 'ァ', 'ぃ': 'ィ', 'ぅ': 'ゥ', 'ぇ': 'ェ', 'ぉ': 'ォ',
    'っ': 'ッ', 'ゃ': 'ャ', 'ゅ': 'ュ', 'ょ': 'ョ',
}

kana_half = {
    'ｱ': 'ア', 'ｲ': 'イ', 'ｳ': 'ウ', 'ｴ': 'エ', 'ｵ': 'オ',
    'ｶ': 'カ', 'ｷ': 'キ', 'ｸ': 'ク', 'ｹ': 'ケ', 'ｺ': 'コ',
    'ｻ': 'サ', 'ｼ': 'シ', 'ｽ': 'ス', 'ｾ': 'セ', 'ｿ': 'ソ',
    'ﾀ': 'タ', 'ﾁ': 'チ', 'ﾂ': 'ツ', 'ﾃ': 'テ', 'ﾄ': 'ト',
    'ﾅ': 'ナ', 'ﾆ': 'ニ', 'ﾇ': 'ヌ', 'ﾈ': 'ネ', 'ﾉ': 'ノ',
    'ﾊ': 'ハ', 'ﾋ': 'ヒ', 'ﾌ': 'フ', 'ﾍ': 'ヘ', 'ﾎ': 'ホ',
    'ﾏ': 'マ', 'ﾐ': 'ミ', 'ﾑ': 'ム', 'ﾒ': 'メ', 'ﾓ': 'モ',
    'ﾔ': 'ヤ', 'ﾕ': 'ユ', 'ﾖ': 'ヨ',
    'ﾗ': 'ラ', 'ﾘ': 'リ', 'ﾙ': 'ル', 'ﾚ': 'レ', 'ﾛ': 'ロ',
    'ﾜ': 'ワ', 'ｦ': 'ヲ', 'ﾝ': 'ン',
    'ｶﾞ': 'ガ', 'ｷﾞ': 'ギ', 'ｸﾞ': 'グ', 'ｹﾞ': 'ゲ', 'ｺﾞ': 'ゴ',
    'ｻﾞ': 'ザ', 'ｼﾞ': 'ジ', 'ｽﾞ': 'ズ', 'ｾﾞ': 'ゼ', 'ｿﾞ': 'ゾ',
    'ﾀﾞ': 'ダ', 'ﾁﾞ': 'ヂ', 'ﾂﾞ': 'ヅ', 'ﾃﾞ': 'デ', 'ﾄﾞ': 'ド',
    'ﾊﾟ': 'パ', 'ﾋﾟ': 'ピ', 'ﾌﾟ': 'プ', 'ﾍﾟ': 'ペ', 'ﾎﾟ': 'ポ',
    'ﾊﾞ': 'パ', 'ﾋﾞ': 'ビ', 'ﾌﾞ': 'ブ', 'ﾍﾞ': 'ベ', 'ﾎﾞ': 'ボ',
    'ｧ': 'ァ', 'ｨ': 'ィ', 'ｩ': 'ゥ', 'ｪ': 'ェ', 'ｫ': 'ォ',
    'ｯ': 'ッ', 'ｬ': 'ャ', 'ｭ': 'ュ', 'ｮ': 'ョ',
}

invert_kana = {value: key for key, value in kana.items()}
kana_keys = kana.keys()
invert_kana_keys = invert_kana.keys()
kana_half_keys = kana_half.keys()


def h2k(words):
    # 平假名转片假名
    trans_words = ''
    for w in words:
        if w in kana_keys:
            trans_words += kana[w]
        else:
            trans_words += w
    return trans_words


def k2h(words):
    # 片假名转平假名
    trans_words = ''
    for w in words:
        if w in invert_kana_keys:
            trans_words += invert_kana[w]
        else:
            trans_words += w
    return trans_words


def kh2f(words):
    # 半角片假名转全角片假名
    trans_words = ''
    for w in words:
        if w in kana_half_keys:
            trans_words += kana_half[w]
        else:
            trans_words += w
    return trans_words


def exec_sqlite3(db_path, exec_cmd, exec_param=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row
    try:
        if exec_param is None:
            cursor.execute(exec_cmd)
        else:
            cursor.execute(exec_cmd, exec_param)
        rows = cursor.fetchall()
        conn.commit()
        conn.close()
        return rows
    except sqlite3.IntegrityError as e:
        print(e)
        conn.close()
        return []
    except sqlite3.OperationalError as e:
        print(e)
        conn.close()
        return []


def item_order(obj, mdl, type):
    attr1 = type + '_priority'
    attr2 = type + '_name'
    priority = eval('obj.' + attr1)
    if priority < 1:
        priority = 1

    item_list = mdl.objects.all().exclude(pk=obj.pk).order_by(attr1, attr2)

    item_list_len = len(item_list)

    if priority > item_list_len:
        priority = item_list_len

    for i in range(item_list_len):
        if i + 1 < priority:
            if i + 1 != eval('item_list[i].' + attr1):
                eval('item_list.filter(pk=item_list[i].pk).update(' + attr1 + '=i + 1)')
        elif i + 1 >= priority:
            if i + 2 != eval('item_list[i].' + attr1):
                eval('item_list.filter(pk=item_list[i].pk).update(' + attr1 + '=i + 2)')
