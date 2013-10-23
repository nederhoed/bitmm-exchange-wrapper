"""\
"""
from distribute_setup import use_setuptools
use_setuptools()

import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

requires = ['']

setup(
    name='bitmm-exchange-wrapper',
    version='0.1',
    description=
        ('Python library to communicate with the BitMyMoney exchange '
            'wrapper REST API'),
    long_description=read('README.md'),
    license="GPLv2",
    author="Guido Wesdorp",
    author_email="johnnydebris@gmail.com",
    url='https://github.com/nederhoed/bitmm-exchange-wrapper',
    keywords='bitmm api bitcoin',
    packages=find_packages(),
    test_suite="tests",
    install_requires=requires,
    classifiers = [
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ]
)
