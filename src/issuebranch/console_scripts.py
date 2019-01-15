#!/usr/bin/env python
"""
misc utilities for managing GitHub issues
"""
import argparse
import importlib
import json
import os
import re
import tempfile

import sh
import shlex
import sys

from slugify import slugify

from issuebranch.backends.github import GithubSession, HTTPError
from issuebranch.shell import run_command
from issuebranch.settings import SCRUM_BOARD_NAME, DEFAULT_COLUMN_NAME

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


def backlog_milestone():
    """
    Moves issue cards within the given miletone from icebox to the backlog column
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'project',
        help='name of the project'
    )
    parser.add_argument('milestone', help='name of the milestone')

    args = parser.parse_args()

    session = GithubSession()

    project_data = session.get_project(args.project)

    milestone_data = session.get_milestone(args.milestone)
    milestone_title = milestone_data['title']

    backlog_data = session.get_column(project_data, 'backlog')
    icebox_data = session.get_column(project_data, 'icebox')

    results = session.search(f'repo:openslate/openslate milestone:"{milestone_title}"')
    for search_data in results['items']:
        issue_data = get_issue(search_data['number']).issue
        issue_card = session.get_card(project_data, issue_data)

        if issue_card['column_url'] == icebox_data['url']:
            session.move_card(issue_card, backlog_data)

        print('.', end='')


def issue_create():
    """
    Create an issue in GitHub and place it as a card in a project.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a',
        '--assignees',
        default=[],
        nargs='*',
        help='users to assign to this issue'
    )
    parser.add_argument(
        '-b',
        '--body',
        default=None,
        help='text body of the issue'
    )
    parser.add_argument(
        '-c',
        '--column',
        default=DEFAULT_COLUMN_NAME,
        help='name of column to place card in'
    )
    parser.add_argument(
        '-i',
        '--interactive',
        action='store_true',
        default=DEFAULT_COLUMN_NAME,
        help='Edit issue title and body in vim',
    )
    parser.add_argument(
        '-l',
        '--labels',
        default=None,
        nargs='*',
        help='labels to add to the new issue'
    )
    parser.add_argument(
        '-m',
        '--milestone',
        default=None,
        help='milestone id to place this issue in. '
             'This should be an integer. '
             'Find milestone ids with the `milestones` command.'
    )
    parser.add_argument(
        '-p',
        '--project',
        default=SCRUM_BOARD_NAME,
        help='project to create issue in'
    )
    parser.add_argument(
        'title',
        default=None,
        nargs='?',
        help='issue title'
    )

    args = parser.parse_args()

    # only required arg for creating an issue. can be overridden in interactive mode
    title = args.title

    # this can be overridden in interactive mode
    body = args.body

    if args.interactive:
        with tempfile.NamedTemporaryFile('w') as fh:
            path = fh.name

            editor = os.environ.get('EDITOR', os.environ.get('VISUAL', 'vi'))

            proc = getattr(sh, editor)

            proc(path, _fg=True)

            with open(path, 'r') as rfh:

                # grab top line as title
                title = rfh.readline().replace('\n', '')

                # grab remaining lines as body
                body = ''.join(rfh.readlines())

    session = GithubSession()

    additional_args = {
        'assignees': args.assignees,
        'body': body,
        'labels': args.labels,
        'milestone': args.milestone,
    }

    issue = session.create_issue(title, **additional_args)

    column_name = args.column
    project_name = args.project

    project = session.get_project(project_name)
    column = session.get_column(project, column_name)

    # finally, create the card
    session.create_card(column, issue)

    print(json.dumps(issue, indent=2))


def get_issue(issue_number):
    """
    Returns the issue object for the given number
    """
    backend_name = os.environ['ISSUE_BACKEND']
    backend_module = importlib.import_module('issuebranch.backends.{}'.format(backend_name))

    return getattr(backend_module, 'Backend')(issue_number)


def make_branch(name, base):
    run_command('git checkout -b {} {}'.format(name, base))


def make_pull_request(issue, upstream=None):
    """
    Injects an empty commit and opens a pull_request
    """
    run_command('git commit --allow-empty -m "Open Pull Request"')

    push_command = 'git push -u'
    if upstream:
        push_command += ' {}' .format(upstream)

    run_command(push_command)

    # Open the actual pull request
    message = 'WIP: {}\n\nImplements {}/{}#{}'.format(issue.subject, issue.owner, issue.repo, issue.issue_number)
    run_command('hub pull-request -o -m "{}" --edit'.format(message), _fg=True)


def issue_branch():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b', '--base',
        default=DEFAULT_BASE_BRANCH,
        help=f'base branch to make this branch from, default {DEFAULT_BASE_BRANCH}'
    )
    parser.add_argument('--prefix', help='branch prefix, e.g. feature, bugfix, etc.')
    parser.add_argument('--pull-request', '--pr', action='store_true', help='open a pull request seeded with an empty commit')
    parser.add_argument('--upstream', '-u', help='the remote to push the branch for creating pull requests')
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
            changetypes = sorted(
                [x for x in issue.get_labels() if x['name'].startswith('changetype:')], key=lambda x: x['name']
            )
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

    # move this issue to the active column
    try:
        issue_column(['issue_column', SCRUM_BOARD_NAME, issue_number, 'active'])
    except:
        print('Unable to move card to the active column, is it in triage?')

    make_branch(slug, base)

    # open a pull-request
    if args.pull_request:
        make_pull_request(issue, upstream=args.upstream)


def issue_close_done():
    """
    Closes any issue that is still open in the done column
    """
    parser = argparse.ArgumentParser(description=issue_close_done.__doc__)

    parser.add_argument('project', help='the project name')
    parser.add_argument('--column', default='done', help='the column to close issues in, default `done`')

    args = parser.parse_args()

    session = GithubSession()

    project_data = session.get_project(args.project)

    column_name = args.column.lower()
    column_data = session.get_column(project_data, column_name)

    for card in session.get_cards(column_data):
        issue_data = session.request('get', card['content_url']).json()

        if issue_data['state'] == 'closed':
            print('.', end='')

            continue

        issue_number = issue_data['number']

        print(f'\nclosing issue {issue_number}')

        session.comment('closing issue in done column', number=issue_number)
        session.update_issue(number=issue_number, state='closed')


def issue_closed():
    """
    Finds issues that are closed in all project columns (except `done`) and moves them to `done`
    """
    parser = argparse.ArgumentParser(description=issue_closed.__doc__)

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
    """
    Moves an issue to the given column
    """
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
    """
    Find issues not in any project and add them to the roadmap icebox
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('project', help='the project name')
    parser.add_argument('--icebox-column', default='icebox')

    args = parser.parse_args()

    icebox_column = args.icebox_column

    session = GithubSession()

    results = session.search('repo:openslate/openslate is:issue is:open no:project')

    # print(json.dumps(results, indent=4))

    for issue_data in results['items']:
        issue = get_issue(issue_data['number'])

        project = issue.get_project(args.project)
        column = issue.get_column(project, icebox_column)

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

    parser.add_argument('name', help='name of the project to clone')

    subcommands = parser.add_subparsers(dest="subcommand")

    clone_parser = subcommands.add_parser('clone')
    clone_parser.add_argument('new_name', help='name of the new project')
    clone_parser.add_argument('--no-cards', action='store_false', dest='cards', help='do not clone cards')

    columns_parser = subcommands.add_parser('columns')
    columns_parser.add_argument('--action', action='store_const', const=projects_columns_print, default=projects_columns_print, help='print the columns')
    columns_parser.add_argument('--clear', action='store_const', const=projects_columns_clear, dest='action', help='clear the column in the specified project')
    columns_parser.add_argument('--verbose', '-v', action='store_true', help='show all json')
    columns_parser.add_argument('column', nargs='?', help='name of the column to clear')

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

        new_project = session.create_project(args.new_name, project['body'])

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

        # when cloning cards is not desired, loop here
        if not args.cards:
            continue

        # get the new column's cards
        new_cards = dict([(x['content_url'], x) for x in session.get_cards(new_column_data)])

        # get the old column's cards
        old_cards = reversed(list(session.get_cards(column_data)))

        print(f'filling {column_name}')

        for old_card_data in old_cards:
            old_content_url = old_card_data['content_url']

            if old_content_url not in new_cards:
                try:
                    issue_data = session.request('get', old_content_url).json()
                except HTTPError as exc:
                    print(f'Warning: unable to create card {old_content_url} in {column_name}')

                    continue
                else:
                    new_card = session.create_card(new_column_data, issue_data)

    # close the new project
    session.close_project(new_project)


def projects_columns(args):
    session = GithubSession()

    project_name = args.name.lower()

    column_name = args.column
    if column_name:
        column_name = column_name.lower()

    project = None
    for _project in session.projects:
        _name = _project['name'].lower()

        if project_name == _name:
            project = _project
            break
    else:
        raise ProjectError('cannot find project {project_name}')

    return args.action(args, session, column_name, project)

def projects_columns_clear(args, session, column_name, project):
    found_column = None
    last_column = None
    position = None

    for _column in session.get_columns(project):
        _column_name = _column['name'].lower()

        if column_name and column_name == _column_name:
            found_column = _column

            if last_column:
                position = f'after:{last_column["id"]}'
            else:
                position = 'first'

            break

        last_column = _column

    print(f'clear, found_column={found_column}, position={position}')

    if found_column:
        session.delete_column(found_column)

        column_name = found_column['name']

    column_data = session.create_column(project, column_name)

    if position:
        session.move_column(column_data, position)


def projects_columns_print(args, session, column_name, project):
    for _column in session.get_columns(project):
        _column_name = _column['name'].lower()

        if column_name and column_name != _column_name:
            continue

        if args.verbose:
            print(json.dumps(_column, indent=4))
        else:
            print(_column['name'])


def milestones():

    session = GithubSession()

    display_pairs = sorted([(m.get("number"), m.get("title")) for m in session.get_milestones()], key=lambda x: x[1])

    for pair in display_pairs:
        print(f'{pair[0]} {pair[1]}')
