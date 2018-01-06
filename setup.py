#!/usr/bin/env python

from setuptools import setup, find_packages
import os, sys
from taiga import __version__


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

extra_kwargs = {}
if sys.version_info >= (3,):
    extra_kwargs['setup_requires'] = ['setuptools']

classifiers = [
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
]

setup(
    name="python-taiga",
    version=__version__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    description="Taiga python API",
    long_description=read('README.rst'),
    license="MIT",
    author="Nephila",
    author_email="info@nephila.it",
    url="https://github.com/nephila/python-taiga",
    keywords="taiga kanban wrapper api",
    install_requires=[
        "requests",
        "six",
        "python-dateutil",
        "pyjwkest"
    ],
    classifiers=classifiers,
    zip_safe=False,
    **extra_kwargs)
