import shutil
from distutils.core import setup
from Cython.Build import cythonize

shutil.copy('../src/readmdict.py', 'readmdict.pyx')
shutil.copy('../src/ripemd128.py', 'ripemd128.pyx')
shutil.copy('../src/pureSalsa20.py', 'pureSalsa20.pyx')
shutil.copy('../src/readzim.py', 'readzim.pyx')

setup(name='readmdict',
      ext_modules=cythonize("readmdict.pyx", annotate=False, language_level="3")
      )

setup(name='ripemd128',
      ext_modules=cythonize("ripemd128.pyx", annotate=False, language_level="3")
      )

setup(name='pureSalsa20',
      ext_modules=cythonize("pureSalsa20.pyx", annotate=False, language_level="3")
      )
setup(name='readzim',
      ext_modules=cythonize("readzim.pyx", annotate=False, language_level="3")
      )
