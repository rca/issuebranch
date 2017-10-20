#!/usr/bin/env python
"""
create a new branch for the given redmine issue
"""
import argparse
import importlib
import json
import os
import re
import sh
import shlex
import sys

from slugify import slugify

from issuebranch.backends.github import GithubSession

DEFAULT_BASE_BRANCH = 'origin/master'
MAX_SLUG_LENGTH = 32

SUBJECT_EXCLUDE_RE = re.compile(r'[/]')


class CommandError(Exception):
    pass


def get_issue(issue_number):
    """
    Returns the issue object for the given number
    """
    backend_name = os.environ['ISSUE_BACKEND']
    backend_module = importlib.import_module('issuebranch.backends.{}'.format(backend_name))

    return getattr(backend_module, 'Backend')(issue_number)


def make_branch(name, base):
    command_l = 'git checkout -b {} {}'.format(name, base).split()

    getattr(sh, command_l[0])(*command_l[1:])


def issue_branch():
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

    issue = get_issue(issue_number)

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


def issue_column():
    parser = argparse.ArgumentParser()

    parser.add_argument('project', help='the project name')
    parser.add_argument('issue_number', type=int, help='the issue tracker\'s issue number')
    parser.add_argument('column', help='the name of the column to move the issue to')

    args = parser.parse_args()

    issue = get_issue(args.issue_number)
    issue_data = issue.issue

    project = issue.get_project(args.project)
    column = issue.get_column(project, args.column)

    try:
        card = issue.get_card(project)
    except issue.CardError:
        issue.create_card(column)
    else:
        issue.move_card(card, column)


def issue_icebox():
    parser = argparse.ArgumentParser()

    parser.add_argument('project', help='the project name')

    args = parser.parse_args()

    session = GithubSession()

    results = session.search('repo:openslate/openslate is:issue is:open no:project')

    # print(json.dumps(results, indent=4))

    for issue_data in results['items']:
        issue = get_issue(issue_data['number'])

        project = issue.get_project(args.project)
        column = issue.get_column(project, 'icebox')

        try:
            issue.create_card(column)
        except Exception as exc:
            print(json.dumps(issue_data, indent=4))
            print(f'Error: unable to process issue exc={exc}')


def issue_show():
    parser = argparse.ArgumentParser()

    parser.add_argument('issue_number', type=int, help='the issue tracker\'s issue number')

    args = parser.parse_args()

    issue = get_issue(args.issue_number)
    issue_data = issue.issue

    print(json.dumps(issue_data, indent=4))
