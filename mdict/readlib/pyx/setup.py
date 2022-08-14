import os
import shutil
import hashlib
from distutils.core import setup
from Cython.Build import cythonize


def get_md5(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    return hashlib.md5(data).hexdigest()


def cmp_md5(file1, file2):
    if os.path.exists(file2):
        if get_md5(file1) == get_md5(file2):
            return True
        else:
            return False
    else:
        return False


lib_list = ['ripemd128', 'pureSalsa20', 'readmdict', 'readzim']

for libfile in lib_list:
    libfile1 = '../src/' + libfile + '.py'
    libfile2 = libfile + '.pyx'
    if not os.path.exists('mdict/readlib/pyx') or not cmp_md5(libfile1, libfile2):
        shutil.copy(libfile1, libfile2)

os.makedirs('mdict/readlib/pyx')

for libfile in lib_list:
    libfile1 = '../src/' + libfile + '.py'
    libfile2 = libfile + '.pyx'
    setup(name=libfile, ext_modules=cythonize(libfile2, annotate=False, language_level="3"))
