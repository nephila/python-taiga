#!/usr/bin/env python

import os
import setuptools
import sys

from taiga import __version__

requirements = [
    'requests>2.11',
    'six>=1.9',
    'python-dateutil>=2.4',
    'pyjwkest>=1.0'
]
test_suite = 'tests'

setuptools.setup(
    name='python-taiga',
    version=__version__,
    url='https://github.com/nephila/python-taiga',
    author='Nephila',
    author_email='info@nephila.it',
    description='Taiga python API',
    long_description=open('README.rst').read(),
    license='MIT',
    packages=setuptools.find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=requirements,
    test_suite=test_suite,
    keywords='taiga kanban wrapper api',
    zip_safe=False,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
