"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/brmmm3/fastthreadpool
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='fastthreadpool',
    version='1.0.3',
    description='An efficient and leightweight thread pool.',
    long_description=long_description,

    url='https://github.com/brmmm3/fastthreadpool',
    download_url = 'https://github.com/brmmm3/fastthreadpool/archive/fastthreadpool-1.0.3.tar.gz',

    author='Martin Bammer',
    author_email='mrbm74@gmail.com',
    license='MIT',

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='fast threading pool',
    #py_modules=["fastthreadpool"],
    packages=find_packages(exclude=['examples', 'doc', 'tests']),
)
