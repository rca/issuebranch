#!/usr/bin/env python
import os

from setuptools import setup


setup(
    name='issuebranch',
    url='https://github.com/rca/issuebranch',
    version='0.0.1',
    author='roberto aguilar',
    author_email='roberto.c.aguilar@gmail.com',
    package_dir={'': 'src'},
    packages=['issuebranch','issuebranch.backends'],
    entry_points={
        'console_scripts': [
            'issue-branch = issuebranch.console_scripts:issue_branch',
            'issue-closed = issuebranch.console_scripts:issue_closed',
            'issue-column = issuebranch.console_scripts:issue_column',
            'issue-icebox = issuebranch.console_scripts:issue_icebox',
            'issue-show = issuebranch.console_scripts:issue_show',
            'projects = issuebranch.console_scripts:projects'
        ],
    },
    install_requires=[
        'requests',
        'sh',
        'python-slugify',
    ]
)
