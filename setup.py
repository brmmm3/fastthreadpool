"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/brmmm3/fastthreadpool
"""

import os
import sys
# To use a consistent encoding
from codecs import open
from os import path, listdir

from setuptools import find_packages
try:
    from setuptools import setup
    from setuptools import Extension
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension

from Cython.Distutils import build_ext
from Cython.Build import cythonize
import Cython.Compiler.Version

from pyorcy import extract_cython

BASEDIR = os.path.dirname(__file__)
PKGNAME = 'fastthreadpool'
PKGDIR = os.path.join(BASEDIR, PKGNAME)

for filename in os.listdir(PKGDIR):
    if filename.endswith(".cpp") or filename.endswith(".pyx") or filename.endswith(".html"):
        os.remove(os.path.join(PKGDIR, filename))

extract_cython(os.path.join(PKGDIR, 'fastthreadpool.py'))

MODULES = [filename[:-4] for filename in os.listdir(PKGDIR)
           if filename.endswith('.pyx')]

# Get the long description from the README file
with open(os.path.join(BASEDIR, 'README.rst'), encoding='utf-8') as F:
    long_description = F.read()

print("building with Cython " + Cython.Compiler.Version.version)


class build_ext_subclass(build_ext):

    def build_extensions(self):
        if self.compiler.compiler_type == "msvc":
            for extension in self.extensions:
                extension.extra_compile_args = ["/O2", "/EHsc"]
        else:
            for extension in self.extensions:
                extension.extra_compile_args = ["-O2"]
        build_ext.build_extensions(self)

annotate = "annotate" in sys.argv

cythonize("fastthreadpool/*.pyx", language_level = 3, annotate = annotate,
          language = "c++", exclude = ["setup.py"])

if annotate:
    sys.exit(0)

ext_modules = [
    Extension(module_name,
              sources=[os.path.join(PKGDIR, module_name+".pyx")],
              language = "c++")
    for module_name in MODULES]


setup(
    name='fastthreadpool',
    version='1.2.5',
    description='An efficient and leightweight thread pool.',
    long_description=long_description,
    long_description_content_type='text/x-rst',

    url='https://github.com/brmmm3/fastthreadpool',
    download_url = 'https://github.com/brmmm3/fastthreadpool/releases/download/1.2.4/fastthreadpool-1.2.5.tar.gz',

    author='Martin Bammer',
    author_email='mrbm74@gmail.com',
    license='MIT',

    classifiers=[  # Optional
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: MIT License',

        'Operating System :: OS Independent',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='fast threading thread pool',
    include_package_data=True,
    #packages=find_packages(where='fastthreadpool', exclude=['examples', 'doc', 'tests']),
    #exclude_package_data={'fastthreadpool': ['fastthreadpool.pyx']},
    ext_modules = ext_modules,
    cmdclass={ 'build_ext': build_ext_subclass }
)

