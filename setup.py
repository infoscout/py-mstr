#!/usr/bin/env python

import re

from setuptools import find_packages, setup


with open('py_mstr/__init__.py', 'rb') as f:
    version = str(re.search('__version__ = "(.+?)"', f.read().decode('utf-8')).group(1))


setup(
    name='py-mstr',
    version=version,
    packages=find_packages(),
    description='Python API for Microstrategy Web Tasks',
    url='http://github.com/infoscout/py-mstr',
    author='InfoScout',
    author_email='oss@infoscoutinc.com',
    license='MIT',
    install_requires=[
        'pyquery >= 1.2.8, < 1.3.0',
        'requests >= 2.3.0',
    ],
    download_url='https://github.com/infoscout/py-mstr/tarball/v0.1.0',
    tests_require=['discover', 'mox == 0.5.3'],
    test_suite="tests",
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
    ],
)
