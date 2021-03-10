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

PKGNAME = 'fastthreadpool'
PKGVERSION = '1.8.1'
BASEDIR = os.path.dirname(__file__)
PKGDIR = PKGNAME if not BASEDIR else os.path.join(BASEDIR, PKGNAME)


# noinspection PyPep8Naming
class build_ext_subclass(build_ext):

    def run(self):
        build_ext.run(self)
        shutil.copyfile(PKGNAME + "/__init__.py", self.build_lib + "/" + PKGNAME + "/__init__.py")

    def build_extensions(self):
        if self.compiler.compiler_type == "msvc":
            for extension in self.extensions:
                if bDebug:
                    extension.extra_compile_args = ["/Od", "/EHsc", "-Zi", "/D__PYX_FORCE_INIT_THREADS=1"]
                    extension.extra_link_args = ["-debug"]
                else:
                    extension.extra_compile_args = ["/O2", "/EHsc", "/D__PYX_FORCE_INIT_THREADS=1"]
        else:
            for extension in self.extensions:
                if bDebug:
                    extension.extra_compile_args = ["-O0", "-g", "-ggdb", "-D__PYX_FORCE_INIT_THREADS=1"]
                    extension.extra_link_args = ["-g"]
                else:
                    extension.extra_compile_args = ["-O2", "-D__PYX_FORCE_INIT_THREADS=1"]
        build_ext.build_extensions(self)


for filename in os.listdir(PKGDIR):
    for ext in (".cpp", ".c", ".pyx", ".html"):
        if filename.endswith(ext):
            pathname = os.path.join(PKGDIR, filename)
            if os.path.exists(pathname):
                os.remove(pathname)

# Get the long description from the README file
with open(os.path.join(BASEDIR, 'README.rst'), encoding='utf-8') as F:
    long_description = F.read()

extract_cython(os.path.join(PKGDIR, 'fastthreadpool.py'))

MODULES = [filename[:-4] for filename in os.listdir(PKGDIR)
           if filename.endswith('.pyx')]

print("Building with Cython " + Cython.Compiler.Version.version)

bAnnotate = "annotate" in sys.argv
bDebug = "debug" in sys.argv
if bDebug:
    sys.argv.remove("debug")


cythonize(PKGDIR + "/*.pyx", language_level=3, annotate=bAnnotate,
          exclude=["setup.py"])

if bAnnotate:
    sys.exit(0)

ext_modules = [
    Extension(PKGNAME + "." + PKGNAME,
              sources=[os.path.join(PKGDIR, PKGNAME + ".pyx")],
              language="c++")
    ]


setup(
    name=PKGNAME,
    version=PKGVERSION,
    description='An efficient and leightweight thread pool.',
    long_description=long_description,
    long_description_content_type='text/x-rst',

    url='https://github.com/brmmm3/' + PKGNAME,
    download_url='https://github.com/brmmm3/%s/releases/download/%s/%s-%s.tar.gz' % (PKGNAME, PKGVERSION, PKGNAME, PKGVERSION),

    author='Martin Bammer',
    author_email='mrbm74@gmail.com',
    license='MIT',

    classifiers=[  # Optional
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',

        'License :: OSI Approved :: MIT License',

        'Operating System :: OS Independent',

        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],

    keywords='fast threading thread pool',
    include_package_data=True,
    cmdclass={'build_ext': build_ext_subclass}, install_requires=['Cython'],
    ext_modules=ext_modules
)
