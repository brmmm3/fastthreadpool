"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/brmmm3/fastthreadpool
"""

import os
import sys
# To use a consistent encoding
from codecs import open
import shutil
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
PKGDIR = PKGNAME if not BASEDIR else os.path.join(BASEDIR, PKGNAME)
VERSION = '1.4.1'

for filename in os.listdir(PKGDIR):
    if filename.endswith(".cpp") or filename.endswith(".c") or filename.endswith(".pyx") or filename.endswith(".html"):
        os.remove(os.path.join(PKGDIR, filename))

extract_cython(os.path.join(PKGDIR, 'fastthreadpool.py'))

MODULES = [filename[:-4] for filename in os.listdir(PKGDIR)
           if filename.endswith('.pyx')]

# Get the long description from the README file
with open(os.path.join(BASEDIR, 'README.rst'), encoding='utf-8') as F:
    long_description = F.read()

print("building with Cython " + Cython.Compiler.Version.version)

annotate = "annotate" in sys.argv
debug = "debug" in sys.argv
if debug:
    del sys.argv[sys.argv.index("debug")]


# noinspection PyPep8Naming
class build_ext_subclass(build_ext):

    def run(self):
        build_ext.run(self)
        shutil.copyfile(PKGNAME + "/__init__.py", self.build_lib + "/" + PKGNAME + "/__init__.py")

    def build_extensions(self):
        if self.compiler.compiler_type == "msvc":
            for extension in self.extensions:
                if debug:
                    extension.extra_compile_args = ["/Od", "/EHsc", "-Zi", "/D__PYX_FORCE_INIT_THREADS=1"]
                    extension.extra_link_args = ["-debug"]
                else:
                    extension.extra_compile_args = ["/O2", "/EHsc", "/D__PYX_FORCE_INIT_THREADS=1"]
        else:
            for extension in self.extensions:
                if debug:
                    extension.extra_compile_args = ["-O0", "-g", "-ggdb", "-D__PYX_FORCE_INIT_THREADS=1"]
                    extension.extra_link_args = ["-g"]
                else:
                    extension.extra_compile_args = ["-O2", "-D__PYX_FORCE_INIT_THREADS=1"]
        build_ext.build_extensions(self)


cythonize("fastthreadpool/*.pyx", language_level=3, annotate=annotate,
          language="c++", exclude=["setup.py"])

if annotate:
    sys.exit(0)

ext_modules = [
    Extension(PKGNAME + "." + PKGNAME,
              sources=[os.path.join(PKGDIR, PKGNAME + ".pyx")],
              language="c++")
    ]


setup(
    name='fastthreadpool',
    version=VERSION,
    description='An efficient and leightweight thread pool.',
    long_description=long_description,
    long_description_content_type='text/x-rst',

    url='https://github.com/brmmm3/fastthreadpool',
    download_url='https://github.com/brmmm3/fastthreadpool/releases/download/%s/fastthreadpool-%s.tar.gz' % (VERSION, VERSION),

    author='Martin Bammer',
    author_email='mrbm74@gmail.com',
    license='MIT',

    classifiers=[  # Optional
        'Development Status :: 5 - Production/Stable',

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
    cmdclass={'build_ext': build_ext_subclass}, install_requires=['Cython'],
    ext_modules=ext_modules
)
