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


class ProjectError(Exception):
    pass


class Unbuffered(object):
   def __init__(self, stream):
       self.stream = stream
   def write(self, data):
       self.stream.write(data)
       self.stream.flush()
   def writelines(self, datas):
       self.stream.writelines(datas)
       self.stream.flush()
   def __getattr__(self, attr):
       return getattr(self.stream, attr)

sys.stdout = Unbuffered(sys.stdout)


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
        try:
            prefix = issue.get_prefix()
        except issue.PrefixError:
            changetypes = sorted([x for x in issue.get_labels() if x['name'].startswith('changetype:')], key=lambda x: x['name'])
            print('no changetype found; select which one to use:')

            for idx, _changetype in enumerate(changetypes):
                print(f'{idx}: {_changetype["name"]}')

            index_number = int(input('enter index number: '))
            changetype = changetypes[index_number]

            issue.add_label(changetype)

            prefix = issue.get_prefix(changetype=changetype['name'])

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


def issue_closed():
    """
    Finds issues that are closed in all project columns (except `done`)
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('project', help='the project name')
    parser.add_argument('--column', default='done', help='the column closed issues should go to, default `done`')

    args = parser.parse_args()

    column = args.column.lower()

    session = GithubSession()

    project = session.get_project(args.project)

    for column_data in session.get_columns(project):
        column_name = column_data['name'].lower()
        if column_name == column:
            continue

        print(f'\nlooking at column {column_name}')

        # print(json.dumps(column_data, indent=4))

        for card in session.get_cards(column_data):
            # print(json.dumps(card, indent=4))

            issue_data = session.request('get', card['content_url']).json()

            if issue_data['state'] != 'closed':
                print('.', end='')

                continue

            issue_number = issue_data['number']

            print(f'\nmoving issue {issue_number} to {column}')

            issue_column(['issue_column', args.project, issue_number, column, '--position=bottom'])


def issue_column(argv=None):
    parser = argparse.ArgumentParser()

    parser.add_argument('project', help='the project name')
    parser.add_argument('issue_number', type=int, help='the issue tracker\'s issue number')
    parser.add_argument('column', help='the name of the column to move the issue to')
    parser.add_argument('--position', help='location of the card; can be \'top\' or \'bottom\'')

    if argv:
        argv = [str(x) for x in argv]
    else:
        argv = sys.argv

    args = parser.parse_args(argv[1:])

    issue = get_issue(args.issue_number)
    issue_data = issue.issue

    project = issue.get_project(args.project)
    column = issue.get_column(project, args.column)

    try:
        card = issue.get_card(project, issue_data)
    except issue.CardError:
        issue.create_card(column, issue_data)
    else:
        issue.move_card(card, column, position=args.position)


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
            issue.create_card(column, issue_data)
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


def projects():
    parser = argparse.ArgumentParser()

    # parser.add_argument('-g', '--global')

    subcommands = parser.add_subparsers(dest="subcommand")

    clone_parser = subcommands.add_parser('clone')
    clone_parser.add_argument('name', help='name of the project to clone')
    clone_parser.add_argument('new_name', help='name of the new project')

    args = parser.parse_args()

    command_fn_name = f'projects_{args.subcommand}'
    command_fn = globals()[command_fn_name]

    command_fn(args)

def projects_clone(args):
    session = GithubSession()

    project = None
    new_project = None

    for _project in session.projects:
        _name = _project['name'].lower()

        if _name == args.name.lower():
            project = _project
        elif _name == args.new_name.lower():
            new_project = _project

        if project and new_project:
            break

    if not project:
        raise ProjectError(f'unable to find project {args.name}')

    # print(json.dumps(project, indent=4))
    # print(json.dumps(new_project, indent=4))

    # create the new project if it doesn't exist
    if not new_project:
        print(f'creating {args.new_name}')

        session.create_project(args.new_name, project['body'])

    # get the new project's columns and index them by name
    new_columns = {}
    for column in session.get_columns(new_project):
        new_columns[column['name']] = column

    # go through all the columns in the old project and create them in the
    # new one if they don't already exist
    for column_data in session.get_columns(project):
        column_name = column_data['name']
        new_column_data = new_columns.get(column_name)
        if not new_column_data:
            print(f'creating column {column_name}')

            new_column_data = session.create_column(new_project, column_name)

        # print(new_column_data)

        # get the new column's cards
        new_cards = dict([(x['content_url'], x) for x in session.get_cards(new_column_data)])

        # get the old column's cards
        old_cards = reversed(list(session.get_cards(column_data)))

        for old_card_data in old_cards:
            old_content_url = old_card_data['content_url']

            if old_content_url not in new_cards:
                # get the issue number from the URL
                issue_data = session.request('get', old_content_url).json()

                new_card = session.create_card(new_column_data, issue_data)
