from distutils.core import setup

from Cython.Build import cythonize

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
