#!/usr/bin/env python
"""
create a new branch for the given redmine issue
"""
import argparse
import importlib
import os
import re
import sh
import shlex
import sys

from slugify import slugify

DEFAULT_BASE_BRANCH = 'origin/master'
MAX_SLUG_LENGTH = 32

SUBJECT_EXCLUDE_RE = re.compile(r'[/]')

def make_branch(name, base):
    command_l = 'git checkout -b {} {}'.format(name, base).split()

    getattr(sh, command_l[0])(*command_l[1:])


def issuebranch():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b', '--base',
        default=DEFAULT_BASE_BRANCH,
        help=f'base branch to make this branch from, default {DEFAULT_BASE_BRANCH}'
    )
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

    subject = SUBJECT_EXCLUDE_RE.sub('', subject)

    branch_name = '{}/{}-{}'.format(prefix, issue_number, subject)

    # add the forward slash to the allowed regex
    # default is: r'[^-a-z0-9]+'
    regex_pattern = r'[^/\-a-z0-9_]+'
    slug = slugify(branch_name, max_length=MAX_SLUG_LENGTH, regex_pattern=regex_pattern)

    # if the base branch is given as '.', expand that to the current branch
    base = args.base
    if base == '.':
        command_l = shlex.split('git rev-parse --abbrev-ref HEAD')
        proc = getattr(sh, command_l[0])

        base = proc(*command_l[1:]).stdout.decode('utf8').strip()

    make_branch(slug, base)
