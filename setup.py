#!/usr/bin/env python

from setuptools import setup, find_packages
import sys

extra_kwargs = {}
if sys.version_info >= (3,):
    extra_kwargs['setup_requires'] = ['setuptools']

setup(
    name="python-taiga",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    description="Taiga python API",
    license="MIT",
    author="Nephila",
    author_email="info@nephila.it",
    url="",
    keywords="taiga kanban wrapper api",
    install_requires=[
        "requests",
        "six"
    ],
    zip_safe=False,
    **extra_kwargs)
