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
            'backlog-milestone = issuebranch.console_scripts:backlog_milestone',
            'issue-branch = issuebranch.console_scripts:issue_branch',
            'issue-close-done = issuebranch.console_scripts:issue_close_done',
            'issue-closed = issuebranch.console_scripts:issue_closed',
            'issue-create = issuebranch.console_scripts:issue_create',
            'issue-column = issuebranch.console_scripts:issue_column',
            'issue-icebox = issuebranch.console_scripts:issue_icebox',
            'issue-show = issuebranch.console_scripts:issue_show',
            'milestones = issuebranch.console_scripts:milestones',
            'projects = issuebranch.console_scripts:projects',
        ],
    },
    install_requires=[
        'requests',
        'sh',
        'python-slugify',
    ]
)
