#!/usr/bin/env python
import os

from setuptools import setup


setup(
    name='issuebranch',
    url='https://github.com/rca/issuebranch',
    version='0.0.0',
    author='roberto aguilar',
    author_email='roberto.c.aguilar@gmail.com',
    package_dir={'': 'src'},
    packages=['issuebranch','issuebranch.backends'],
    entry_points={
        'console_scripts': [
            'issue-branch = issuebranch.console_scripts:issuebranch',
        ],
    },
    install_requires=[
        'requests',
        'python-slugify',
    ]
)
