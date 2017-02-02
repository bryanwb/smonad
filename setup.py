# -*- coding: utf-8 -*-
import sys
from os import path
from distutils.core import setup
from smonad import VERSION
from smonad import __doc__ as DESCRIPTION

if sys.version_info < (2, 7):
    sys.exit('smonad requires Python 2.7 or higher')

ROOT_DIR = path.abspath(path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)

LONG_DESCRIPTION = open(path.join(ROOT_DIR, 'README.rst')).read()

setup(
    name='smonad',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    author='Bryan W. Berry',
    author_email='bryan.berry@gmail.com',
    url='https://github.com/bryanwb/smonad/',
    download_url=(
        'https://github.com/bryanwb/smonad/archive/%s.zip' % VERSION),
    packages=['smonad', 'smonad.types'],
    license='BSD-New',
)
