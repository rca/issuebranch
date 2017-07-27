#!/usr/bin/env python
"""
create a new branch for the given redmine issue
"""
import argparse
import importlib
import os
import sh
import sys

from slugify import slugify


def make_branch(name):
    command_l = 'git checkout -b {} master'.format(name).split()

    getattr(sh, command_l[0])(*command_l[1:])


def issuebranch():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prefix', help='branch prefix, e.g. feature, bugfix, etc.')
    parser.add_argument('--subject', help='provide subject text instead of fetching')
    parser.add_argument('issue_number', type=int, help='the issue tracker\'s issue number')

    args = parser.parse_args()

    issue_number = args.issue_number

    backend_name = os.environ['ISSUE_BACKEND']
    backend_module = importlib.import_module('issuebranch.backends.{}'.format(backend_name))

    issue = getattr(backend_module, 'Backend')(issue_number)

    prefix = args.prefix
    if not prefix:
        prefix = issue.prefix

    subject = args.subject
    if not subject:
        subject = issue.subject

    branch_name = '{}/{}-{}'.format(prefix, issue_number, subject)

    slug = slugify(branch_name)

    make_branch(slug)
