#!/usr/bin/env python

import re

from setuptools import find_packages, setup


with open('py_mstr/__init__.py', 'rb') as f:
    version = str(re.search('__version__ = "(.+?)"', f.read().decode('utf-8')).group(1))


tests_require = ['mox==0.5.3', 'discover']
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
        'pyquery>=1.2.8,<1.3.0',
        'requests>=2.3.0',
    ],
    download_url='https://github.com/infoscout/py-mstr/tarball/v0.1.0',
    tests_require=tests_require,
    test_suite="tests.get_tests",
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
)
