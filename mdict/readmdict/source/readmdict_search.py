#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# readmdict.py
# Octopus MDict Dictionary File (.mdx) and Resource File (.mdd) Analyser
#
# Copyright (C) 2012, 2013, 2015 Xiaoqiang Wang <xiaoqiangwang AT gmail DOT com>
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# You can get a copy of GNU General Public License along this program
# But you can always get it from http://www.gnu.org/licenses/gpl.txt
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

import math
import operator
import re
import sys
# zlib compression is used for engine version >=2.0
import zlib
from io import BytesIO
from struct import pack, unpack

try:
    from mdict.readmdict.lib.pureSalsa20 import Salsa20
except ImportError as e:
    print(e)
    print(
        'loading pureSalsa20 lib failed! run build script to compile, this will speed up search.')
    from mdict.readmdict.source.pureSalsa20 import Salsa20

try:
    from mdict.readmdict.lib.ripemd128 import ripemd128
except ImportError as e:
    print(e)
    print(
        'loading ripemd128 lib failed! run build script to compile, this will speed up search.')
    from mdict.readmdict.source.ripemd128 import ripemd128

# from ripemd128 import ripemd128
# from pureSalsa20 import Salsa20

# LZO compression is used for engine version < 2.0
try:
    import lzo
except ImportError:
    lzo = None
    print("LZO compression support is not available")

'''
key_block_info,key_block,record_block的开头4个字节是压缩类型
b'\x00\x00\x00\x00'无压缩
b'\x01\x00\x00\x00'lzo压缩
b'\x02\x00\x00\x00'zlib压缩

self._encrypt是加密类型
0 无加密
1 Salsa20加密，需要提供self._passcode
2 ripemd128加密
'''

# 2x3 compatible
if sys.hexversion >= 0x03000000:
    unicode = str


def _unescape_entities(text):
    """
    unescape offending tags < > " &
    """
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&amp;', '&')
    return text


def _fast_decrypt(data, key):
    b = bytearray(data)
    key = bytearray(key)
    previous = 0x36
    for i in range(len(b)):
        t = (b[i] >> 4 | b[i] << 4) & 0xff
        t = t ^ previous ^ (i & 0xff) ^ key[i % len(key)]
        previous = b[i]
        b[i] = t
    return bytes(b)


def _mdx_decrypt(comp_block):
    key = ripemd128(comp_block[4:8] + pack(b'<L', 0x3695))
    return comp_block[0:8] + _fast_decrypt(comp_block[8:], key)


def _salsa_decrypt(ciphertext, encrypt_key):
    s20 = Salsa20(key=encrypt_key, IV=b"\x00" * 8, rounds=8)
    return s20.encryptBytes(ciphertext)


def _decrypt_regcode_by_deviceid(reg_code, deviceid):
    deviceid_digest = ripemd128(deviceid)
    s20 = Salsa20(key=deviceid_digest, IV=b"\x00" * 8, rounds=8)
    encrypt_key = s20.encryptBytes(reg_code)
    return encrypt_key


def _decrypt_regcode_by_email(reg_code, email):
    email_digest = ripemd128(email.decode().encode('utf-16-le'))
    s20 = Salsa20(key=email_digest, IV=b"\x00" * 8, rounds=8)
    encrypt_key = s20.encryptBytes(reg_code)
    return encrypt_key


reg = r'[ _=,.;:!?@%&#~`()\[\]<>{}/\\\$\+\-\*\^\'"\t|]'
regp = re.compile(reg)


# 搜韵诗词词条：八归·辛巳，CC-CEDICT词条威廉·莎士比亚，stripkey时不包含·


class MDict(object):

    def __init__(self, fpath, encoding='', passcode=None):
        self._fpath = fpath
        self._encoding = encoding.upper()
        self._passcode = passcode
        self._sug_flag = -1

        f = open(self._fpath, 'rb')
        self.header = self._read_header(f)
        self.strip_key()
        f.seek(self._key_block_offset)
        try:
            self._key_list = tuple(self._read_keys(f))
        except Exception:
            print("Try Brutal Force on Encrypted Key Blocks")
            # _read_keys_brutal从没用到过，不知道是否能用
            self._key_list = tuple(self._read_keys_brutal(f))
        f.seek(self._record_block_offset)
        self._record_list = tuple(self._read_records(f))
        f.close()

    def get_len(self):
        return self._num_entries

    def get_fpath(self):
        return self._fpath

    def get_encoding(self):
        return self._encoding

    def get_fname(self):
        slash = self._fpath.rfind('/')
        if self._fpath.rfind('\\') > slash:
            slash = self._fpath.rfind('\\')
        return self._fpath[slash + 1:self._fpath.rfind('.')]

    def _read_number(self, f):
        return unpack(self._number_format, f.read(self._number_width))[0]

    @staticmethod
    def _parse_header(header):
        """
        extract attributes from <Dict attr="value" ... >
        """
        taglist = re.findall(r'(\w+)="(.*?)"', header, re.DOTALL)
        tagdict = {}
        for key, value in taglist:
            tagdict[key] = _unescape_entities(value)
        return tagdict

    def compare_keys(self, key1, key2):
        """
        排序要求：
        header中KeyCaseSensitive表明排序时是否大小写不敏感,为No时要转化为小写字母比较。
        header中StripKey只对mdx有效，为No，则不分词，字母、空格、符号都参与排序，为Yes，则分词，仅字母参与排序，去掉空格、符号。
        MDX的编码有utf-8,utf-16,gb18030(包括gbk，gb2313,gb18030),BIG5按照utf-8，utf-16按照utf-16be排序，其他按照各自编码排序。
        MDD的编码为utf-16le,尽管utf-16默认也是utf-16le，但是会加前缀\xff\xfe，因此如果将传入的str转化为bytes再比较就会出错，如果都是在str下进行比较就没有影响。
        @param key1: the key user input
        @param key2: the key from the file
        @return:
        """
        # mdx和mdd中的key都是bytes，查询key是str，因此str转bytes要在lower()之后进行。
        if type(key1) == bytes:
            key1 = key1.decode(self._encoding, errors='replace')
        if type(key2) == bytes:
            key2 = key2.decode(self._encoding, errors='replace')
            # Dictionary of Engineering的最后一个词条是b'\xc5ngstr\xf6m compensation pyrheliometer'，其中\xc5和\xf6解码报错，因此用replace。
        key1 = self.process_str_keys(key1)
        key2 = self.process_str_keys(key2)

        if self.__class__.__name__ == 'MDX':
            if self._encoding == 'UTF-16':
                if operator.__lt__(key1.encode('utf-16be'), key2.encode('utf-16be')):
                    return -1
                elif operator.__eq__(key1.encode('utf-16be'), key2.encode('utf-16be')):
                    return 0
                elif operator.__gt__(key1.encode('utf-16be'), key2.encode('utf-16be')):
                    return 1
            if self._encoding == 'BIG-5':
                if operator.__lt__(key1.encode('utf-8'), key2.encode('utf-8')):
                    return -1
                elif operator.__eq__(key1.encode('utf-8'), key2.encode('utf-8')):
                    return 0
                elif operator.__gt__(key1.encode('utf-8'), key2.encode('utf-8')):
                    return 1
            else:
                if operator.__lt__(key1.encode(self._encoding, errors='replace'),
                                   key2.encode(self._encoding, errors='replace')):
                    return -1
                elif operator.__eq__(key1.encode(self._encoding, errors='replace'),
                                     key2.encode(self._encoding, errors='replace')):
                    return 0
                elif operator.__gt__(key1.encode(self._encoding, errors='replace'),
                                     key2.encode(self._encoding, errors='replace')):
                    return 1
        else:
            if operator.__lt__(key1.encode('utf-8'), key2.encode('utf-8')):
                return -1
            elif operator.__eq__(key1.encode('utf-8'), key2.encode('utf-8')):
                return 0
            elif operator.__gt__(key1.encode('utf-8'), key2.encode('utf-8')):
                return 1

    def lower_str_keys(self, key):
        """
        lower processing
        @param key: the key to be processed
        @return:
        """
        if 'KeyCaseSensitive' in self.header and self.header['KeyCaseSensitive'] == 'Yes':
            return key
        else:
            return key.lower()

    def strip_key(self):
        # 0:False,1:True,2:None
        if 'StripKey' in self.header.keys():
            if self.header['StripKey'] == 'Yes':
                self._strip_key = 1
            elif self.header['StripKey'] == 'No':
                self._strip_key = 0
            else:
                self._strip_key = 2
        else:
            self._strip_key = 2

        if self.__class__.__name__ == 'MDD':
            self._strip_key = 0

    def process_str_keys(self, key):
        if type(key) == bytes:
            key = key.decode(self._encoding, errors='replace')
        key = self.lower_str_keys(key)

        if self._strip_key == 1:
            # key = re.sub(reg, '', key)
            key = regp.sub('', key)
        # 这里要strip()，否则，[汉-汉] 家庭实用菜谱的mdd有问题。
        return key.strip()

    def _read_keys(self, f):
        # the following numbers could be encrypted
        if self._version >= 2.0:
            num_bytes = 8 * 5
        else:
            num_bytes = 4 * 4
        block = f.read(num_bytes)

        if self._encrypt & 1:
            if self._passcode is None:
                raise RuntimeError('user identification is needed to read encrypted file')
            regcode, userid = self._passcode
            if isinstance(userid, unicode):
                userid = userid.encode('utf8')
            if self.header['RegisterBy'] == 'EMail':
                encrypted_key = _decrypt_regcode_by_email(regcode, userid)
            else:
                encrypted_key = _decrypt_regcode_by_deviceid(regcode, userid)
            block = _salsa_decrypt(block, encrypted_key)

        # decode this block
        sf = BytesIO(block)
        # number of key blocks
        self._num_key_blocks = self._read_number(sf)  # p1位置
        # number of entries
        self._num_entries = self._read_number(sf)
        # number of bytes of key block info after decompression
        if self._version >= 2.0:
            # key_block_info_decomp_size = self._read_number(sf)
            self._read_number(sf)
        # number of bytes of key block info
        self.key_block_info_size = self._read_number(sf)
        # number of bytes of key block
        key_block_size = self._read_number(sf)

        # 4 bytes: adler checksum of previous 5 numbers
        if self._version >= 2.0:
            adler32 = unpack('>I', f.read(4))[0]
            assert adler32 == (zlib.adler32(block) & 0xffffffff)

        # read key block info, which indicates key block's compressed and decompressed size
        key_block_info = f.read(self.key_block_info_size)
        self._record_block_offset = f.tell() + key_block_size
        return self._decode_key_block_info(key_block_info)

    def _read_records(self, f):
        num_record_blocks = self._read_number(f)
        num_entries = self._read_number(f)
        assert (num_entries == self._num_entries)
        self.record_block_info_size = self._read_number(f)
        # record_block_size = self._read_number(f)
        self._read_number(f)

        # record block info section
        record_block_info_list = []
        size_counter = 0
        compressed_size = 0
        decompressed_size = 0
        for i in range(num_record_blocks):
            compressed_size += self._read_number(f)
            decompressed_size += self._read_number(f)
            record_block_info_list += [(compressed_size, decompressed_size)]
            size_counter += self._number_width * 2

        return record_block_info_list

    def _decode_key_block_info(self, key_block_info_compressed):
        key_block_compressed_size = 0
        key_block_decompressed_size = 0
        key_block_info = b''
        if self._version >= 2:
            # zlib compression
            #            assert(key_block_info_compressed[:4] == b'\x02\x00\x00\x00')
            # decrypt if needed
            compress = key_block_info_compressed[0:4]
            if compress == b'\x00\x00\x00\x00':
                if self._encrypt & 0x02:
                    key_block_info_compressed = _mdx_decrypt(key_block_info_compressed)
                key_block_info = key_block_info_compressed[8:]
            elif compress == b'\x02\x00\x00\x00':
                if self._encrypt & 0x02:
                    key_block_info_compressed = _mdx_decrypt(key_block_info_compressed)
                # decompress
                key_block_info = zlib.decompress(key_block_info_compressed[8:])
                # adler checksum
                adler32 = unpack('>I', key_block_info_compressed[4:8])[0]
                assert (adler32 == zlib.adler32(key_block_info) & 0xffffffff)
        else:
            # no compression
            key_block_info = key_block_info_compressed
        # decode
        key_block_info_list = []
        num_entries = 0
        i = 0
        if self._version >= 2:
            byte_format = '>H'
            # H是2个字节，B是1个字节
            byte_width = 2
            text_term = 1
        else:
            byte_format = '>B'
            byte_width = 1
            text_term = 0

        while i < len(key_block_info):
            # number of entries in current key block
            num_entries += unpack(self._number_format, key_block_info[i:i + self._number_width])[0]
            i += self._number_width
            # text head size

            text_head_size = unpack(byte_format, key_block_info[i:i + byte_width])[0]
            if self._encoding != 'UTF-16':
                text_head_text = key_block_info[i + byte_width:i + byte_width + text_head_size]
            else:
                text_head_text = key_block_info[i + byte_width:i + byte_width + text_head_size * 2]
            i += byte_width

            if self._encoding != 'UTF-16':
                i += text_head_size + text_term
            else:
                i += (text_head_size + text_term) * 2

            # text tail size

            text_tail_size = unpack(byte_format, key_block_info[i:i + byte_width])[0]
            if self._encoding != 'UTF-16':
                text_tail_text = key_block_info[i + byte_width:i + byte_width + text_tail_size]
            else:
                text_tail_text = key_block_info[i + byte_width:i + byte_width + text_tail_size * 2]
            # utf-16需要16位二进制数，也就是4位16进制数来表示一个字符，比如b'\\\x00u\x00',b'\\\x00'是反斜杠\，b'u\x00'是u。text_head_size和text_tail_size是字符长度，在utf-16下应该读取2倍字节的长度，结束后有\x00\x00表示结束。

            i += byte_width
            # text tail
            if self._encoding != 'UTF-16':
                i += text_tail_size + text_term
            else:
                i += (text_tail_size + text_term) * 2
            # key block compressed size
            key_block_compressed_size_t = unpack(self._number_format, key_block_info[i:i + self._number_width])[0]
            i += self._number_width
            # key block decompressed size
            key_block_decompressed_size_t = unpack(self._number_format, key_block_info[i:i + self._number_width])[0]
            i += self._number_width
            key_block_compressed_size += key_block_compressed_size_t
            key_block_decompressed_size += key_block_decompressed_size_t
            key_block_info_list += [
                (text_head_text, text_tail_text, key_block_compressed_size, key_block_decompressed_size)]
        #           #text_head_text是该key_block的第一个词条，？？？？？text_tail_text可能是该key_block的最后一个词条，也可能是下一个key_block的text_head_text。
        # text_tail_text在mdd中不可靠，比如牛8简mdd最后一个块的最后一个项是b'\\us_pron.png',但是对应的text_tail_text是b'us_pron.png'，少了个反斜杠。
        # key_block_compressed_size是包含这个key_block的累计压缩大小，key_block_decompressed_size是包含这个key_block的累计解压大小。
        return key_block_info_list

    def reduce_key_info(self, s, e, key):
        if e <= s:
            return -1, -1, -1, -1, -1, -1, -1
        half = int((e + s) / 2)
        key_block_info_list = self._key_list
        if self.compare_keys(key, key_block_info_list[half][0]) >= 0 \
                >= self.compare_keys(key, key_block_info_list[half][1]):
            if half - 1 >= 0:
                if half + 1 <= e:
                    return key_block_info_list[half][2], key_block_info_list[half][3], \
                           key_block_info_list[half - 1][2], key_block_info_list[half - 1][3], \
                           key_block_info_list[half + 1][2], key_block_info_list[half + 1][3], half
                else:
                    return key_block_info_list[half][2], key_block_info_list[half][3], \
                           key_block_info_list[half - 1][2], key_block_info_list[half - 1][3], -1, -1, half
            else:
                return key_block_info_list[half][2], key_block_info_list[half][3], 0, 0
        elif self.compare_keys(key, key_block_info_list[half][0]) < 0:
            return self.reduce_key_info(s, half, key)
        else:
            return self.reduce_key_info(half + 1, e, key)

    def reduce_key_block(self, key_list, s, e, key):
        if e <= s:
            return []
        half = int((e + s) / 2)

        if self.compare_keys(key, key_list[half][1]) == 0:
            return self.process_symbol_search(key, key_list, half, 0)
        elif self.compare_keys(key, key_list[half][1]) < 0:
            return self.reduce_key_block(key_list, s, half, key)
        else:
            return self.reduce_key_block(key_list, half + 1, e, key)

    def reduce_key_block_sug(self, key_list, s, e, key, num):
        if e <= s:
            self._sug_flag = e
            return ['']
        half = int((e + s) / 2)

        key_list_len = len(key_list)

        if self.compare_keys(key, key_list[half][1]) == 0:
            k = self.process_str_keys(key_list[half][1])

            m_a = [k]

            lim = num
            if key_list_len - 1 - half < 6:
                lim = key_list_len - 1 - half
            i = j = 1
            self._sug_flag = half + 1

            while half + j < e and j <= lim and not self.compare_keys(key, key_list[half + j][1]) == 0:
                k = self.process_str_keys(key_list[half + j][1])
                self._sug_flag = half + j + 1
                if k not in m_a:
                    m_a.append(k)
                    i += 1
                j += 1
            return m_a

        elif self.compare_keys(key, key_list[half][1]) < 0:
            return self.reduce_key_block_sug(key_list, s, half, key, num)
        elif self.compare_keys(key, key_list[half][1]) > 0:
            return self.reduce_key_block_sug(key_list, half + 1, e, key, num)

    @staticmethod
    def get_key_block(f, compressed_size, decompressed_size, compressed_size_b, decompressed_size_b):
        if compressed_size_b == -1:
            print('当前块为第一个块')
            return b''
        key_block_compressed = f.read(compressed_size - compressed_size_b)
        end = compressed_size
        key_block_type = key_block_compressed[0:4]
        key_block = b''

        if key_block_type == b'\x00\x00\x00\x00':
            key_block = key_block_compressed[8:end]
        elif key_block_type == b'\x01\x00\x00\x00':
            if lzo is None:
                # key_block = b''
                print("LZO compression is not supported")
                return key_block

            # decompress key block
            header = b'\xf0' + pack('>I', decompressed_size - decompressed_size_b)
            key_block = lzo.decompress(header + key_block_compressed[8:end])
        elif key_block_type == b'\x02\x00\x00\x00':
            # decompress key block
            key_block = zlib.decompress(key_block_compressed[8:end])
        else:
            print('key block type error!', key_block_type)

        return key_block

    def get_block_size(self, key):
        # compressed_size = -1  # 累计压缩大小
        # decompressed_size = -1  # 累计解压大小
        # compressed_size_b = -1  # 之前块的累计压缩大小
        # decompressed_size_b = -1  # 之前块的累计解压大小
        compressed_size_a = -1  # 之后块的累计压缩大小
        decompressed_size_a = -1  # 之后块的累计解压大小

        key = self.process_str_keys(key)

        key_block_info_list = self._key_list
        length = len(key_block_info_list)

        # <0时应当返回第一个词条
        # if self.compare_keys(key, key_block_info_list[0][0]) < 0:
        #     return -1, -1, -1, -1, -1, -1
        if self.compare_keys(key, key_block_info_list[0][0]) < 0 or \
                self.compare_keys(key, key_block_info_list[length - 1][1]) > 0:
            return -1, -1, -1, -1, -1, -1

        if length == 1:  # collins词典mdd的第一个key_block长度1，只有css文件。
            compressed_size = key_block_info_list[length - 1][2]
            decompressed_size = key_block_info_list[length - 1][3]
            compressed_size_b = 0
            decompressed_size_b = 0
            r_p1 = 0
        elif self.compare_keys(key, key_block_info_list[0][1]) <= 0:
            compressed_size = key_block_info_list[0][2]
            decompressed_size = key_block_info_list[0][3]
            compressed_size_b = 0
            decompressed_size_b = 0
            r_p1 = 0
            if length >= 2:
                compressed_size_a = key_block_info_list[1][2]
                decompressed_size_a = key_block_info_list[1][3]
        elif self.compare_keys(key, key_block_info_list[length - 1][0]) >= 0:
            compressed_size = key_block_info_list[length - 1][2]
            decompressed_size = key_block_info_list[length - 1][3]
            compressed_size_b = key_block_info_list[length - 2][2]
            decompressed_size_b = key_block_info_list[length - 2][3]
            r_p1 = length - 1
        else:
            compressed_size, decompressed_size, compressed_size_b, decompressed_size_b, compressed_size_a, \
            decompressed_size_a, r_p1 = self.reduce_key_info(0, length - 1, key)
        self.t_p1 = r_p1
        return compressed_size, decompressed_size, compressed_size_b, decompressed_size_b, compressed_size_a, \
               decompressed_size_a

    def get_key_block_size_list(self, p):
        # compressed_size = -1  # 累计压缩大小
        # decompressed_size = -1  # 累计解压大小
        # compressed_size_b = -1  # 之前块的累计压缩大小
        # decompressed_size_b = -1  # 之前块的累计解压大小
        compressed_size_a = -1  # 之后块的累计压缩大小
        decompressed_size_a = -1  # 之后块的累计解压大小
        compressed_size_b2 = -1  # 之前第2块的累计压缩大小
        decompressed_size_b2 = -1  # 之前第2块的累计解压大小

        key_block_info_list = self._key_list
        length = len(key_block_info_list)
        if p == -1:
            p = length - 1
        if not p < length:
            return -1, -1, -1, -1, -1, -1, -1, -1
        if p - 1 >= 0:
            compressed_size_b = key_block_info_list[p - 1][2]
            decompressed_size_b = key_block_info_list[p - 1][3]
        else:
            compressed_size_b = 0
            decompressed_size_b = 0

        if p - 2 >= 0:
            compressed_size_b2 = key_block_info_list[p - 2][2]
            decompressed_size_b2 = key_block_info_list[p - 2][3]
        else:
            if compressed_size_b != 0:
                compressed_size_b2 = 0
                decompressed_size_b2 = 0

        if p + 1 < length - 1:
            compressed_size_a = key_block_info_list[p + 1][2]
            decompressed_size_a = key_block_info_list[p + 1][3]

        compressed_size = key_block_info_list[p][2]
        decompressed_size = key_block_info_list[p][3]

        return compressed_size, decompressed_size, compressed_size_b, decompressed_size_b, compressed_size_a, \
               decompressed_size_a, compressed_size_b2, decompressed_size_b2

    def process_symbol_search(self, key, key_list, position, direction):
        result_list = []
        key_list_length = len(key_list)
        p_key = self.process_str_keys(key)

        # 先向前查找，再向后查找，这样整个列表的my_end就是第1个和最后1个元素的my_end

        # 处理纯符号的查询，当stripkey为yes时，纯字符比如+=会被替换为空，导致查询错误，因此当替换后为空时，不替换进行查找。
        # if self.process_str_keys(key_list[my_position][1]) == '':
        # 改成当含部分符号时，进行详细匹配，如果key包含在结果中就加入，当查询无字符时，则按照默认的stripkey来查询。
        # 比如查c，会显示c,c++,c#，但是查c#，则只会显示c#。
        # 后续这里改成两个自定义参数，一是纯符号分词准确查找，二是包含符号分词准确查找
        if self.__class__.__name__ == 'MDX':
            # 在MDX里需要对纯字符进行重新匹配
            if p_key == '':
                # 如果key是纯符号，要求key完全匹配，查到一个结果就返回。
                if direction <= 0:
                    p_now = position
                    while p_now >= 0 and self.process_str_keys(key_list[p_now][1]) == '':
                        if key == key_list[p_now][1].decode(self._encoding, errors='replace'):
                            my_start = key_list[p_now][0]
                            if p_now + 1 < key_list_length:
                                my_end = key_list[p_now + 1][0]
                            else:
                                my_end = -1

                            entry = key_list[p_now][1].decode(self._encoding, errors='replace')
                            result_list.append((my_start, my_end, self.t_p1, p_now, entry))
                            return result_list
                        p_now -= 1

                if direction >= 0:
                    if direction == 0:
                        p_now = position + 1
                    else:
                        p_now = position

                    while p_now < key_list_length and self.process_str_keys(key_list[p_now][1]) == '':
                        if key == key_list[p_now][1].decode(self._encoding, errors='replace'):
                            my_start = key_list[p_now][0]
                            if p_now + 1 < key_list_length:
                                my_end = key_list[p_now + 1][0]
                            else:
                                my_end = -1
                            entry = key_list[p_now][1].decode(self._encoding, errors='replace')
                            result_list.append((my_start, my_end, self.t_p1, p_now, entry))
                            return result_list
                        p_now += 1
                return result_list  # 没有查到返回空

            elif p_key != self.lower_str_keys(key).replace(' ', '') and len(p_key) <= 2:
                # 仅当纯字母只有1个或2个是才会包含查找
                # key处理后不为空，且不等于lower后并替换空格的key，说明key包含符号，此时要包含查找
                # 这里会导致一查c#时不会出现c++，但也会导致查it's不会包含its（比方，等换个词），即在筛选的过程中，有部分符合规定的词被筛选掉了，做成可选功能
                if direction <= 0:
                    p_now = position
                    while p_now >= 0 and p_key == self.process_str_keys(key_list[p_now][1]):
                        if self.lower_str_keys(key).replace(' ', '') in self.lower_str_keys(
                                key_list[p_now][1].decode(self._encoding, errors='replace')).replace(' ', ''):
                            my_start = key_list[p_now][0]
                            if p_now + 1 < key_list_length:
                                my_end = key_list[p_now + 1][0]
                            else:
                                my_end = -1

                            entry = key_list[p_now][1].decode(self._encoding, errors='replace')
                            result_list.append((my_start, my_end, self.t_p1, p_now, entry))

                        p_now -= 1

                if direction >= 0:
                    if direction == 0:
                        p_now = position + 1
                    else:
                        p_now = position

                    while p_now < key_list_length and p_key == self.process_str_keys(key_list[p_now][1]):
                        if self.lower_str_keys(key).replace(' ', '') in self.lower_str_keys(
                                key_list[p_now][1].decode(self._encoding, errors='replace')).replace(' ', ''):
                            my_start = key_list[p_now][0]
                            if p_now + 1 < key_list_length:
                                my_end = key_list[p_now + 1][0]
                            else:
                                my_end = -1
                            entry = key_list[p_now][1].decode(self._encoding, errors='replace')
                            result_list.append((my_start, my_end, self.t_p1, p_now, entry))

                        p_now += 1

                return result_list

        # MDD查询和不包含符号的MDX查询用下面的逻辑
        if direction <= 0:  # 向前查找
            p_now = position

            while p_now >= 0 and self.compare_keys(key, key_list[p_now][1]) == 0:
                my_start = key_list[p_now][0]
                if p_now + 1 < key_list_length:
                    my_end = key_list[p_now + 1][0]
                else:
                    my_end = -1
                entry = key_list[p_now][1].decode(self._encoding, errors='replace')
                result_list.append((my_start, my_end, self.t_p1, p_now, entry))
                p_now -= 1

        if direction >= 0:  # 向后查找
            if direction == 0:
                p_now = position + 1
            else:
                p_now = position

            while p_now < key_list_length and self.compare_keys(key, key_list[p_now][1]) == 0:
                my_start = key_list[p_now][0]
                if p_now + 1 < key_list_length:
                    my_end = key_list[p_now + 1][0]
                else:
                    my_end = -1
                entry = key_list[p_now][1].decode(self._encoding, errors='replace')

                result_list.append((my_start, my_end, self.t_p1, p_now, entry))
                p_now += 1

        return result_list

    def search_key_block_position(self, key, key_list):
        key_list_length = len(key_list)
        result_list = []

        if self.compare_keys(key, key_list[0][1]) < 0 or self.compare_keys(key, key_list[key_list_length - 1][1]) > 0:
            return []

        elif self.compare_keys(key, key_list[0][1]) == 0:
            result_list = self.process_symbol_search(key, key_list, 0, 1)

        elif self.compare_keys(key, key_list[key_list_length - 1][1]) == 0:
            result_list = self.process_symbol_search(key, key_list, key_list_length - 1, -1)
        else:
            result_list = self.reduce_key_block(key_list, 0, key_list_length - 1, key)
        return result_list

    def search_key_block_sug(self, key, key_list, num):
        # notice that adler32 returns signed value
        #        assert(adler32 == zlib.adler32(key_block) & 0xffffffff)
        key = self.process_str_keys(key)

        my_sug = []
        # 0表示没有重复的词条，my_extra小于my_start说明前一个是重复词条，my_extra大于my_end说明后一个是重复词条
        key_list_length = len(key_list)
        # key_list是一个key_block中的所有key的元组(key_id,key_text)组成的列表。
        # 这里<=0，因此<0时，应当提供第一词条
        if self.compare_keys(key, key_list[0][1]) <= 0:
            my_sug.append(key_list[0][1].decode(self._encoding, errors='replace'))
            if key_list_length > 1:
                i = 1
                j = 1
                lim = num
                if key_list_length < 6:
                    lim = key_list_length - 1
                while j <= lim and j <= 8:
                    if not self.compare_keys(key, key_list[j][1]) == 0:
                        k = key_list[j][1].decode(self._encoding, errors='replace')
                        if k not in my_sug:
                            my_sug.append(k)
                            i += 1
                    j += 1

        elif self.compare_keys(key, key_list[key_list_length - 1][1]) == 0:
            my_sug.append(key_list[key_list_length - 1][1].decode(self._encoding, errors='replace'))
        else:
            my_sug.extend(self.reduce_key_block_sug(key_list, 0, key_list_length - 1, key, num))

        return my_sug

    def search_key_block_list(self, key_list, p, num, back):
        my_list = []
        length = len(key_list)
        start = 0
        end = length - 1

        if p == -1:
            p = end

        if p - num > 0:
            start = p - num + 1
        if p + num < end:
            end = p + num

        if start == end:
            r_p2 = start
            my_list.append([key_list[start][1].decode(self._encoding, errors='replace'), start, start])
        elif back:
            r_p2 = end
            for i in range(p, end + 1):
                s = key_list[i][0]
                if i + 1 < length:
                    e = key_list[i + 1][0]
                else:
                    e = -1
                my_list.append([key_list[i][1].decode(self._encoding, errors='replace'), s, e])
        else:
            r_p2 = start
            for i in range(start, p + 1):
                s = key_list[i][0]
                if i + 1 < length:
                    e = key_list[i + 1][0]
                else:
                    e = -1
                my_list.append([key_list[i][1].decode(self._encoding, errors='replace'), s, e])
        return my_list, r_p2

    def _decode_key_block_search(self, key, f):
        # num_bytes = 0
        if self._version >= 2.0:
            num_bytes = 8 * 5
        else:
            num_bytes = 4 * 4

        p = self._key_block_offset + num_bytes + self.key_block_info_size
        if self._version >= 2.0:
            p += 4

        # 获取key_t所在块和之前及之后块的累积压缩和解压缩大小
        compressed_size, decompressed_size, compressed_size_b, decompressed_size_b, compressed_size_a, \
        decompressed_size_a = self.get_block_size(key)

        if compressed_size == -1:
            # 未查询到
            return []
        p += compressed_size_b
        f.seek(p)

        key_block = self.get_key_block(f, compressed_size, decompressed_size, compressed_size_b,
                                       decompressed_size_b)
        if key_block == b'':
            return []

        key_list = self._split_key_block(key_block)
        # key_list是一个key_block中的所有key的元组(key_id,key_text)组成的列表。

        result_list = self.search_key_block_position(key, key_list)

        # 由于存在一个key_block对应多个record_block的情况，因此当my_end==-1时，提取下一个块第一个词条的位置赋值给my_end。

        if len(result_list) > 0:
            if result_list[0][1] == -1 or result_list[len(result_list) - 1][1] == -1:
                if compressed_size_a != -1:
                    key_block = self.get_key_block(f, compressed_size_a, decompressed_size_a, compressed_size,
                                                   decompressed_size)
                    my_end = unpack(self._number_format, key_block[0:self._number_width])[0]
                    if result_list[0][1] == -1:
                        item = list(result_list[0])
                        item[1] = my_end
                        result_list[0] = tuple(item)
                    elif result_list[len(result_list) - 1][1] == -1:
                        item = list(result_list[len(result_list) - 1])
                        item[1] = my_end
                        result_list[len(result_list) - 1] = tuple(item)

        return result_list

    def _decode_key_block_sug(self, key, f, num):
        # num_bytes = 0
        if self._version >= 2.0:
            num_bytes = 8 * 5
        else:
            num_bytes = 4 * 4

        p = self._key_block_offset + num_bytes + self.key_block_info_size
        if self._version >= 2.0:
            p += 4

        compressed_size, decompressed_size, compressed_size_b, decompressed_size_b, compressed_size_a, \
        decompressed_size_a = self.get_block_size(key)

        if compressed_size == -1:
            return ['']
        p += compressed_size_b
        f.seek(p)
        key_block = self.get_key_block(f, compressed_size, decompressed_size, compressed_size_b,
                                       decompressed_size_b)
        if key_block == b'':
            return []

        key_list = self._split_key_block(key_block)

        my_sug = self.search_key_block_sug(key, key_list, num)

        key_list_length = len(key_list)

        # sug_flag标记的是key_list中没有找到key时的位置，从该位置向后查询近似的词。
        sug_flag = self._sug_flag
        if sug_flag != -1 and len(my_sug) < num:
            k = key_list[sug_flag][1].decode(self._encoding, errors='replace')
            if self.process_str_keys(key) != '':
                if self.process_str_keys(k).find(self.process_str_keys(key)) == 0:
                    m_a = [k]
                    lim = num - len(my_sug)
                    if key_list_length - 1 - sug_flag < 6:
                        lim = key_list_length - 1 - sug_flag
                    i = j = 1

                    while sug_flag + j < key_list_length and j <= lim and not \
                            self.compare_keys(key, key_list[sug_flag + j][1]) == 0:

                        k = key_list[sug_flag + j][1].decode(self._encoding, errors='replace')
                        if k not in m_a:
                            m_a.append(k)
                            i += 1
                        j += 1
                    my_sug.extend(m_a)
            else:
                if k.find(key) == 0:
                    m_a = [k]
                    lim = num - len(my_sug)
                    if key_list_length - 1 - sug_flag < 6:
                        lim = key_list_length - 1 - sug_flag
                    i = j = 1

                    while sug_flag + j < key_list_length and j <= lim and not key_list[sug_flag + j][1].decode(
                            self._encoding, errors='replace').find(key) == 0:

                        k = key_list[sug_flag + j][1].decode(self._encoding, errors='replace')
                        if k not in m_a:
                            m_a.append(k)
                            i += 1
                        j += 1
                    my_sug.extend(m_a)
        return my_sug

    def _decode_key_block_list(self, f, p1, p2, num, direction):
        # num_bytes = 0
        if self._version >= 2.0:
            num_bytes = 8 * 5
        else:
            num_bytes = 4 * 4

        p = self._key_block_offset + num_bytes + self.key_block_info_size
        if self._version >= 2.0:
            p += 4

        compressed_size, decompressed_size, compressed_size_b, decompressed_size_b, compressed_size_a, \
        decompressed_size_a, compressed_size_b2, decompressed_size_b2 = \
            self.get_key_block_size_list(p1)

        if compressed_size == -1:
            return [], -1, -1, -1, -1
        p += compressed_size_b
        f.seek(p)

        key_block = self.get_key_block(f, compressed_size, decompressed_size, compressed_size_b,
                                       decompressed_size_b)

        if key_block == b'':
            return [], -1, -1, -1, -1

        key_list = self._split_key_block(key_block)
        r_s_p1 = p1
        r_s_p2 = p2
        r_e_p1 = p1
        r_e_p2 = p2

        my_list = f_list = b_list = []
        myt_list = []

        total_len = len(key_list)
        total_num = num

        if r_s_p2 > total_len - 1:
            return [], -1, -1, -1, -1

        while total_num + 1 > total_len:
            myt2_list, r_e_p2 = self.search_key_block_list(key_list, p2, len(key_list), True)
            myt_list.extend(myt2_list)

            num = num - len(key_list)

            p = self._key_block_offset + num_bytes + self.key_block_info_size
            if self._version >= 2.0:
                p += 4
            compressed_size, decompressed_size, compressed_size_b, decompressed_size_b, compressed_size_a, \
            decompressed_size_a, compressed_size_b2, decompressed_size_b2 = \
                self.get_key_block_size_list(r_e_p1 + 1)

            if compressed_size == -1:
                return myt_list, r_s_p1, r_s_p2, r_e_p1, r_e_p2

            p += compressed_size_b
            f.seek(p)

            key_block = self.get_key_block(f, compressed_size, decompressed_size, compressed_size_b,
                                           decompressed_size_b)
            if key_block == b'':
                return myt_list, r_s_p1, r_s_p2, r_e_p1, r_e_p2

            key_list = self._split_key_block(key_block)

            r_e_p1 += 1
            r_e_p2 = 0

            total_len += len(key_list)
            p2 = 0

        if direction > 0:
            my_list, r_e_p2 = self.search_key_block_list(key_list, p2, num, True)
        elif direction < 0:
            my_list, r_s_p2 = self.search_key_block_list(key_list, p2, num, False)
        elif direction == 0:
            f_list, r_s_p2 = self.search_key_block_list(key_list, p2, math.floor(num / 2), False)
            b_list, r_e_p2 = self.search_key_block_list(key_list, p2, math.ceil(num / 2) + 1, True)
            # 这里加1，总数才是num，后面处理是否少了个+1
            if f_list[-1][2] == -1 and len(b_list) > 1:
                f_list[-1][2] = b_list[1][1]
            my_list.extend(f_list)
            my_list.extend(b_list[1:])

        my_list_len = len(my_list)

        if my_list_len == num:
            if my_list[-1][2] == -1 and compressed_size_a != -1:
                key_block = self.get_key_block(f, compressed_size_a, decompressed_size_a, compressed_size,
                                               decompressed_size)
                my_list[-1][2] = unpack(self._number_format, key_block[0:self._number_width])[0]
        elif my_list_len < num:

            if direction > 0:
                if compressed_size_a != -1:
                    r_e_p1 += 1
                    key_block = self.get_key_block(f, compressed_size_a, decompressed_size_a, compressed_size,
                                                   decompressed_size)
                    key_list = self._split_key_block(key_block)
                    t_list, r_e_p2 = self.search_key_block_list(key_list, 0, num - my_list_len, True)
                    my_list[-1][2] = t_list[0][1]
                    my_list.extend(t_list)

            elif direction < 0:
                if compressed_size_b2 != -1:
                    r_s_p1 -= 1

                    p -= (compressed_size_b - compressed_size_b2)
                    f.seek(p)
                    key_block = self.get_key_block(f, compressed_size_b, decompressed_size_b, compressed_size_b2,
                                                   decompressed_size_b2)
                    key_list = self._split_key_block(key_block)
                    t_list, r_s_p2 = self.search_key_block_list(key_list, len(key_list) - 1, num - my_list_len,
                                                                False)

                    t_list[-1][2] = my_list[0][1]
                    t_list.extend(my_list)
                    my_list = t_list
            elif direction == 0:
                if len(f_list) < math.floor(num / 2):
                    if compressed_size_b2 != -1:
                        r_s_p1 -= 1

                        p -= (compressed_size_b - compressed_size_b2)
                        f.seek(p)
                        key_block = self.get_key_block(f, compressed_size_b, decompressed_size_b, compressed_size_b2,
                                                       decompressed_size_b2)
                        key_list = self._split_key_block(key_block)
                        t_list, r_s_p2 = self.search_key_block_list(key_list, len(key_list) - 1,
                                                                    math.floor(num / 2) - len(f_list),
                                                                    False)
                        t_list[-1][2] = my_list[len(f_list)][1]
                        t_list.extend(my_list)
                        my_list = t_list
                if len(b_list) < math.ceil(num / 2):
                    if compressed_size_a != -1:
                        r_e_p1 += 1
                        key_block = self.get_key_block(f, compressed_size_a, decompressed_size_a, compressed_size,
                                                       decompressed_size)
                        key_list = self._split_key_block(key_block)
                        t_list, r_e_p2 = self.search_key_block_list(key_list, 0, math.ceil(num / 2) - len(b_list),
                                                                    True)
                        my_list[-1][2] = t_list[0][1]
                        my_list.extend(t_list)
        myt_list.extend(my_list)

        return myt_list, r_s_p1, r_s_p2, r_e_p1, r_e_p2

    def look_up_key(self, key, f):
        if self._strip_key == 2:
            self._strip_key = 1
            r_list = self._decode_key_block_search(key, f)
            if len(r_list) == 0:
                self._strip_key = 0
                r_list = self._decode_key_block_search(key, f)
            self._strip_key = 2
        else:
            r_list = self._decode_key_block_search(key, f)
        r_list.sort(key=lambda k: (k[2], k[3]))  # 按照实际顺序排序
        return r_list

    def _split_key_block(self, key_block):
        key_list = []
        key_start_index = 0
        key_end_index = 0

        while key_start_index < len(key_block):
            # the corresponding record's offset in record block
            key_id = unpack(self._number_format, key_block[key_start_index:key_start_index + self._number_width])[0]
            # key text ends with '\x00'
            if self._encoding == 'UTF-16':
                delimiter = b'\x00\x00'
                width = 2
            else:
                delimiter = b'\x00'
                width = 1
            i = key_start_index + self._number_width
            while i < len(key_block):
                if key_block[i:i + width] == delimiter:
                    key_end_index = i
                    break
                i += width

            key_text = key_block[key_start_index + self._number_width:key_end_index]
            key_start_index = key_end_index + width
            key_list += [(key_id, key_text)]
        return key_list

    def _read_header(self, f):

        # number of bytes of header text
        header_bytes_size = unpack('>I', f.read(4))[0]
        header_bytes = f.read(header_bytes_size)
        # 4 bytes: adler32 checksum of header, in little endian
        adler32 = unpack('<I', f.read(4))[0]
        assert (adler32 == zlib.adler32(header_bytes) & 0xffffffff)
        # mark down key block offset
        self._key_block_offset = f.tell()

        # header text in utf-16 encoding ending with '\x00\x00'
        header_text = header_bytes[:-2].decode('utf-16', errors='replace')
        header_tag = self._parse_header(header_text)
        if not self._encoding:
            encoding = header_tag['Encoding']
            if sys.hexversion >= 0x03000000:
                encoding = encoding
            # GB18030 > GBK > GB2312
            if encoding in ['GBK', 'GB2312']:
                encoding = 'GB18030'
            self._encoding = encoding
        # encryption flag
        #   0x00 - no encryption
        #   0x01 - encrypt record block
        #   0x02 - encrypt key info block
        if 'Encrypted' not in header_tag or header_tag['Encrypted'] == 'No':
            self._encrypt = 0
        elif header_tag['Encrypted'] == 'Yes':
            self._encrypt = 1
        else:
            self._encrypt = int(header_tag['Encrypted'])

        # stylesheet attribute if present takes form of:
        #   style_number # 1-255
        #   style_begin  # or ''
        #   style_end    # or ''
        # store stylesheet in dict in the form of
        # {'number' : ('style_begin', 'style_end')}
        self._stylesheet = {}
        if header_tag.get('StyleSheet'):
            lines = header_tag['StyleSheet'].splitlines()
            for i in range(0, len(lines), 3):
                self._stylesheet[lines[i]] = (lines[i + 1], lines[i + 2])

        # before version 2.0, number is 4 bytes integer
        # version 2.0 and above uses 8 bytes
        self._version = float(header_tag['GeneratedByEngineVersion'])
        if self._version < 2.0:
            self._number_width = 4
            self._number_format = '>I'
            # >表示big-endian大端，I是4字节无符号整型，相当于java中的int，Q是8字节无符号整型，相当于java中的long。
        else:
            self._number_width = 8
            self._number_format = '>Q'

        return header_tag

    def _read_keys_brutal(self, f):
        # the following numbers could be encrypted, disregard them!
        if self._version >= 2.0:
            num_bytes = 8 * 5 + 4
            key_block_type = b'\x02\x00\x00\x00'
        else:
            num_bytes = 4 * 4
            key_block_type = b'\x01\x00\x00\x00'
        # block = f.read(num_bytes)
        f.read(num_bytes)

        # key block info
        # 4 bytes '\x02\x00\x00\x00'
        # 4 bytes adler32 checksum
        # unknown number of bytes follows until '\x02\x00\x00\x00' which marks the beginning of key block
        key_block_info = f.read(8)
        if self._version >= 2.0:
            assert key_block_info[:4] == b'\x02\x00\x00\x00'
        while True:
            fpos = f.tell()
            t = f.read(1024)
            index = t.find(key_block_type)
            if index != -1:
                key_block_info += t[:index]
                f.seek(fpos + index)
                break
            else:
                key_block_info += t

        key_block_info_list = self._decode_key_block_info(key_block_info)
        key_block_size = sum(list(zip(*key_block_info_list))[0])
        self._record_block_offset = f.tell() + key_block_size

        return key_block_info_list

    def reduce_record_block(self, s, e, start):
        if e <= s:
            return -1, -1, -1, -1
        half = int((e + s) / 2)
        record_block_info_list = self._record_list
        if record_block_info_list[half - 1][1] <= start < record_block_info_list[half][1]:
            return record_block_info_list[half - 1][0], record_block_info_list[half - 1][1], \
                   record_block_info_list[half][0], record_block_info_list[half][1]
        elif start < record_block_info_list[half - 1][1]:
            return self.reduce_record_block(s, half, start)
        else:
            return self.reduce_record_block(half + 1, e, start)

    def _decode_record_block(self, start, end, f):
        if self._version >= 2.0:
            num_bytes = 8 * 4
        else:
            num_bytes = 4 * 4
        record_block_info_list = self._record_list

        compressed_size_b = 0
        decompressed_size_b = 0
        compressed_size = 0
        decompressed_size = 0
        length = len(record_block_info_list)

        if start < 0 or end > record_block_info_list[length - 1][1]:
            # compressed_size_b = -1
            # decompressed_size_b = -1
            return b''

        if start < record_block_info_list[0][1]:
            compressed_size = record_block_info_list[0][0]
            decompressed_size = record_block_info_list[0][1]
        elif record_block_info_list[length - 2][1] < start < record_block_info_list[length - 1][1]:
            compressed_size = record_block_info_list[length - 1][0]
            decompressed_size = record_block_info_list[length - 1][1]
            compressed_size_b = record_block_info_list[length - 2][0]
            decompressed_size_b = record_block_info_list[length - 2][1]
        else:
            compressed_size_b, decompressed_size_b, compressed_size, decompressed_size = \
                self.reduce_record_block(0, length, start)

        if compressed_size_b == -1:
            print('-1未查询到')

        p = self._record_block_offset + num_bytes + self.record_block_info_size + compressed_size_b
        f.seek(p)

        record_block_compressed = f.read(compressed_size - compressed_size_b)

        # 4 bytes indicates block compression type
        record_block_type = record_block_compressed[:4]

        # 4 bytes adler checksum of uncompressed content
        adler32 = unpack('>I', record_block_compressed[4:8])[0]

        record_block = b''
        # no compression
        if record_block_type == b'\x00\x00\x00\x00':
            record_block = record_block_compressed[8:]
        # lzo compression
        elif record_block_type == b'\x01\x00\x00\x00':
            if lzo is None:
                print("LZO compression is not supported")
                return b''
            #                break
            # decompress
            header = b'\xf0' + pack('>I', decompressed_size - decompressed_size_b)
            record_block = lzo.decompress(header + record_block_compressed[8:])
        # zlib compression
        elif record_block_type == b'\x02\x00\x00\x00':
            # decompress
            record_block = zlib.decompress(record_block_compressed[8:])

        if end == -1:
            record = record_block[start - decompressed_size_b:]
        else:
            record = record_block[start - decompressed_size_b:end - decompressed_size_b]

        return record


class MDD(MDict):
    def __init__(self, fpath, passcode=None):
        MDict.__init__(self, fpath, encoding='UTF-16', passcode=passcode)

    def look_up(self, key, f):
        """
        get the resource from the MDD file
        @param key: resouce name
        @return:
        """
        result_list = self.look_up_key(key, f)
        if len(result_list) == 0:
            return []
        r_list = []
        for r in result_list:
            record = self.look_up_record(r[0], r[1], f)
            r_list.append((r[0], r[1], r[2], r[3], r[4], record))
        return r_list

    def look_up_record(self, start, end, f):
        """
        get the resouce using the position
        @param start: the start position of content in the uncompressed record_block
        @param end: the end position of content in the uncompressed record_block
        @param f: the MDD file object
        @return:
        """
        record = self._decode_record_block(start, end, f)
        return record


class MDX(MDict):
    def __init__(self, fpath, encoding='', passcode=None):
        MDict.__init__(self, fpath, encoding, passcode)

    def substitute_stylesheet(self, txt):
        """
        some dictionarys' css style stored in the header['StyleSheet'].
        when header['Compact'] is Yes, the style should be added to the content.
        @param txt: the content of entry
        @return: the processed content
        """

        if self._stylesheet:
            txt_list = re.split(r'`\d+`', txt)
            txt_tag = re.findall(r'`\d+`', txt)
            txt_styled = txt_list[0]

            for j, p in enumerate(txt_list[1:]):
                t = txt_tag[j][1:-1]
                # 21世纪英汉汉英双向词典的a词条的有一个键不在self._stylesheet中，报错。
                if t in self._stylesheet:
                    style = self._stylesheet[t]
                    if p and p[-1] == '\n':
                        txt_styled = txt_styled + style[0] + p.rstrip() + style[1] + '\r\n'
                    else:
                        txt_styled = txt_styled + style[0] + p + style[1]
                else:
                    if p and p[-1] == '\n':
                        txt_styled = txt_styled + p.rstrip() + '\r\n'
                    else:
                        txt_styled = txt_styled + p
            return txt_styled
        else:
            # self._stylesheet为空时，清除r'`\d+`'
            return re.sub(r'`\d+`', '', txt)

    def look_up_list(self, required, f):
        rr_dict = {}
        t_list = []
        for key in required:
            r_list = []
            key = key.strip()
            result_list = self.look_up_key(key, f)
            if len(result_list) == 0:
                continue
            for r in result_list:
                if r[0] not in t_list:
                    t_list.append(r[0])
                    record = self.look_up_record(r[0], r[1], f)
                    r_list.append((r[0], r[1], r[2], r[3], r[4], record))
            rr_dict.update({key: r_list})
        return rr_dict

    def look_up(self, key, f):
        """
        search a entry in the MDX file
        @param key: the entry to search
        @return:
        """
        key = key.strip()
        result_list = self.look_up_key(key, f)

        if len(result_list) == 0:
            return []
        r_list = []
        for r in result_list:
            record = self.look_up_record(r[0], r[1], f)
            r_list.append((r[0], r[1], r[2], r[3], r[4], record))

        return r_list

    def look_up_record(self, start, end, f):
        """
        search the content according to position
        the position of start==0 is self._record_block_offset + num_bytes + self.record_block_info_size
        @param start: the start position of content in the uncompressed record_block
        @param end: the end position of centent in the uncompressed record_block
        @param f: the MDX file object
        @return:
        """
        record = self._decode_record_block(start, end, f)
        record = record.decode(self._encoding, errors='replace').strip(u'\x00')

        # 21世纪英汉汉英双向词典 的header中没有Compact，但有Compat，此外是否要考虑可能有的词典header键的大小写不规范
        if 'Compact' in self.header:
            if self.header['Compact'] == 'Yes':
                record = self.substitute_stylesheet(record)
        elif 'Compat' in self.header:
            if self.header['Compat'] == 'Yes':
                record = self.substitute_stylesheet(record)

        return record

    def look_up_record_list(self, p_list, f):
        record_list = []
        for s, e in p_list:
            record_list.append(self.look_up_record(s, e, f))

        return record_list

    def look_up_sug_list(self, required, num, f):
        """
        search the suggestion of key
        @param key: entry to search
        @param num: the number of suggestion to get
        @return:
        """

        sug = []
        for key in required:

            self._sug_flag = -1
            extra = self._decode_key_block_sug(key, f, num)

            for e in extra:
                if e != '' and e not in sug:
                    sug.append(e)

        return sug

    def look_up_sug(self, key, num, f):
        """
        search the suggestion of key
        @param key: entry to search
        @param num: the number of suggestion to get
        @return:
        """

        self._sug_flag = -1
        extra = self._decode_key_block_sug(key, f, num)
        sug = []

        for e in extra:
            if e != '':
                sug.append(e)

        return sug

    def look_up_key_list(self, p1, p2, num, direction, f):
        """
        to get a continuous list of entry in the dictionary
        @param p1: position of entry in the key_block_info_list
        @param p2: position of entry in the key_list
        @param num: number of entrys wang to get
        @param direction: direction>0 means back, direction<0 meand front,
                direction=0 means getting half front and half back.
        @return:
        """
        self._sug_flag = -1
        entry_list, r_s_p1, r_s_p2, r_e_p1, r_e_p2 = self._decode_key_block_list(f, p1, p2, num, direction)
        return entry_list, r_s_p1, r_s_p2, r_e_p1, r_e_p2
