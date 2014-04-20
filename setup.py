#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup


HERE = os.path.abspath(os.path.dirname(__file__))


def make_readme(root_path):
    FILES = ('README.rst', 'LICENSE', 'CHANGELOG', 'CONTRIBUTORS')
    for filename in FILES:
        filepath = os.path.realpath(os.path.join(HERE, filename))
        if os.path.isfile(filepath):
            with open(filepath, mode='r') as f:
                yield f.read()

LONG_DESCRIPTION = "\r\n\r\n----\r\n\r\n".join(make_readme(HERE))

setup(
    name='django-urlmonitor',
    version='0.1.0',
    author='Keryn Knight',
    author_email='python-package@kerynknight.com',
    description="listen for URL changes at an object level",
    long_description=LONG_DESCRIPTION,
    packages=[
        'urlmonitor',
    ],
    include_package_data=True,
    install_requires=[
        'Django>=1.4.10',
    ],
    zip_safe=False,
    keywords='django urls',
    license="BSD License",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Framework :: Django',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Topic :: Internet :: WWW/HTTP',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)
