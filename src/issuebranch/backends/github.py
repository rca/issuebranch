import os
import json
import requests

from requests.exceptions import HTTPError

from functools import lru_cache as lru_cache_base, wraps

from . import BaseBackend
from ..exceptions import CommandError, PrefixError

CARD_CREATE_ENDPOINT = '/projects/columns/{column_id}/cards'
CARD_ENDPOINT = '/projects/columns/cards/{id}'
CARD_MOVE_ENDPOINT = CARD_ENDPOINT + '/moves'

COLUMN_DELETE_ENDPOINT = '/projects/columns/{id}'
COLUMN_MOVE_ENDPOINT = '/projects/columns/{id}/moves'

ISSUE_BACKEND_API_KEY = os.environ['ISSUE_BACKEND_API_KEY']
ISSUE_BACKEND_REPO = os.environ['ISSUE_BACKEND_REPO']
ISSUE_BACKEND_URL = 'https://api.github.com'
ISSUE_BACKEND_USER = os.environ['ISSUE_BACKEND_USER']

ISSUE_LIST_ENDPOINT = '/repos/{owner}/{repo}/issues'
ISSUE_COMMENT_ENDPOINT = ISSUE_LIST_ENDPOINT + '/{number}/comments'
ISSUE_UPDATE_ENDPOINT = ISSUE_LIST_ENDPOINT + '/{number}'

ISSUE_BACKEND_ENDPOINT = ISSUE_LIST_ENDPOINT + '/{issue}'
ISSUE_LABELS_ENDPOINT = '/repos/{owner}/{repo}/issues/{number}/labels'

LABELS_CREATE_ENDPOINT = '/repos/{owner}/{repo}/labels'

MILESTONES_ENDPOINT = '/repos/{owner}/{repo}/milestones'

PROJECTS_ENDPOINT = '/orgs/{owner}/projects'
PROJECT_ENDPOINT = '/projects/{project_id}'
PROJECT_CREATE_COLUMN = '/projects/{project_id}/columns'

REPO_LABELS_ENDPOINT = '/repos/{owner}/{repo}/labels'

SEARCH_ISSUE_ENDPOINT = '/search/issues'


class CardError(Exception):
    pass


class HDict(dict):
    def __hash__(self):
        return hash(json.dumps(self))


def lru_cache():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            h_args = [HDict(x) if isinstance(x, dict) else x for x in args]

            return lru_cache_base()(fn)(*h_args, **kwargs)
        return wrapper
    return decorator


class GithubLinkHeader(object):
    def __init__(self, **kwargs):
        self.url = None
        self.rel = None

        for k, v in kwargs.items():
            if k not in self.__dict__:
                raise AttributeError(f'{k} is not in {self.__class__}')

            setattr(self, k, v)
        pass

    @staticmethod
    def parse(link_header):
        """
        Returns a list of GithubLinkHeader objects
        """
        links = []

        for item in link_header.split(','):
            item = item.strip()

            attrs = {}

            for token in item.split(';'):
                token = token.strip()

                if token.startswith('<'):
                    attrs['url'] = token[1:-1]
                else:
                    _t = [x.strip() for x in token.split('=', 1)]
                    attrs[_t[0]] = json.loads(_t[1])

            links.append(GithubLinkHeader(**attrs))

        return links

class GithubSession(object):
    # alias exceptions to make it easy to get without additional imports
    CardError = CardError
    PrefixError = PrefixError

    def add_label(self, label_data, number=None):
        """
        Adds a label to an issue

        Args:
            label_data (dict): Github API label data
            number (int): optional issue number, or the current issue by default
        """
        number = number or self.issue_number

        url = self.get_full_url(
            ISSUE_LABELS_ENDPOINT,
            owner=ISSUE_BACKEND_USER,
            repo=ISSUE_BACKEND_REPO,
            number=number
        )

        data = [
            label_data['name'],
        ]

        return self.request('post', url, json=data)

    def close_project(self, project_data):
        """
        closes the given project
        """
        url = self.get_full_url(PROJECT_ENDPOINT, project_id=project_data['id'])

        data = {
            'state': 'closed',
        }

        return self.request('patch', url, json=data).json()

    def comment(self, comment, number=None):
        number = number or self.issue_number

        url = self.get_full_url(
            ISSUE_COMMENT_ENDPOINT,
            owner=ISSUE_BACKEND_USER,
            repo=ISSUE_BACKEND_REPO,
            number=number
        )

        data = {
            'body': comment,
        }

        return self.request('post', url, json=data).json()

    def create_card(self, column_data, issue_data):
        url = self.get_full_url(CARD_CREATE_ENDPOINT, column_id=column_data['id'])
        data = {
            'content_id': issue_data['id'],
            'content_type': 'Issue',
        }

        return self.request('post', url, json=data)

    def create_column(self, project, name):
        url = self.get_full_url(PROJECT_CREATE_COLUMN, project_id=project['id'])
        data = {
            'name': name,
        }

        return self.request('post', url, json=data).json()

    def create_issue(self, title, **kwargs):
        """
        Create an issue on the default board.
        """
        url = self.get_full_url(
            ISSUE_LIST_ENDPOINT,
            owner=ISSUE_BACKEND_USER,
            repo=ISSUE_BACKEND_REPO
        )
        required_fields = {
            'title': title,
        }
        data = dict([(k, v) for k, v in kwargs.items() if v])
        data.update(required_fields)

        return self.request('post', url, json=data).json()

    def create_label(self, name, color):
        """
        Creates a label in the user/repo data from the environent
        """
        url = self.get_full_url(
            LABELS_CREATE_ENDPOINT,
            owner=ISSUE_BACKEND_USER,
            repo=ISSUE_BACKEND_REPO
        )

        data = {
            "name": name,
            "color": color,
        }

        return self.request('post', url, json=data).json()

    def create_project(self, name, body):
        url = self.get_full_url(
            PROJECTS_ENDPOINT,
            owner=ISSUE_BACKEND_USER
        )

        data = {
          'name': name,
          'body': body,
        }

        print(data)

        return self.request('post', url, json=data).json()

    def delete_card(self, card_data):
        url = self.get_full_url(CARD_ENDPOINT, id=card_data['id'])

        return self.request('delete', url)

    def delete_column(self, column_data):
        url = self.get_full_url(COLUMN_DELETE_ENDPOINT, id=column_data['id'])

        return self.request('delete', url)

    @lru_cache()
    def get_card(self, project, issue_data):
        """
        Returns the card for this issue within the project

        Args:
            project (dict): the project data from the github api
            issue_data (dict): issue data from the github api
        """
        issue_url = issue_data['url']

        # print('\n\nissue:')
        # print(json.dumps(issue_data, indent=4))

        for column in self.get_columns(project):
            for card in self.get_cards(column):
                if card['content_url'] == issue_url:
                    return card
        else:
            raise CardError(f'Unable to find card for issue {issue_url}')

    @lru_cache()
    def get_cards(self, column_data):
        """
        Iterates through all the cards in a column_data

        This method checks the response headers for the "Link" header
        which provides pagination urls to get the next batch of cards
        """
        cards_url = column_data['cards_url']
        for response in self.get_paginated(cards_url):
            for item in response.json():
                yield item

    @lru_cache()
    def get_column(self, project, name):
        columns = self.get_columns(project)
        for column in columns:
            if column['name'].lower() == name:
                return column
        else:
            raise CommandError(f'Unable to find name={name}')

    @lru_cache()
    def get_columns(self, project):
        '''
        Returns the columns in the given project

        Args:
            project (dict): the dictionary from the projects API requests
        '''
        columns_url = project['columns_url']
        for response in self.get_paginated(columns_url):
            for item in response.json():
                yield item

    def get_full_url(self, endpoint, **format_args):
        full_url = f'{ISSUE_BACKEND_URL}{endpoint}'.format(**format_args)

        return full_url

    def get_issues(self, **filters):
        """
        Returns all the issues in the user/repo values in the environment

        Args:
            filters (dict): parameters per the v3 API
        """
        url = self.get_full_url(
            ISSUE_LIST_ENDPOINT,
            owner=ISSUE_BACKEND_USER,
            repo=ISSUE_BACKEND_REPO
        )

        params = filters or {}

        for response in self.get_paginated(url, params=params):
            for item in response.json():
                yield item

    def get_labels(self):
        """
        Returns all the labels for ISSUE_BACKEND_REPO
        """
        url = self.get_full_url(
            REPO_LABELS_ENDPOINT,
            owner=ISSUE_BACKEND_USER,
            repo=ISSUE_BACKEND_REPO
        )

        for response in self.get_paginated(url):
            for item in response.json():
                yield item

    def get_milestone(self, name):
        """
        Returns a single milestone
        """
        for milestone in self.get_milestones():
            if milestone['title'].lower() == name.lower():
                return milestone
        else:
            raise CommandError(f'unable to find milestone name={name}')

    def get_milestones(self):
        """
        Returns all the milestones for the user/repo values in the environment
        """
        columns_url = self.get_full_url(
            MILESTONES_ENDPOINT,
            owner=ISSUE_BACKEND_USER,
            repo=ISSUE_BACKEND_REPO
        )
        for response in self.get_paginated(columns_url):
            for item in response.json():
                yield item

    def get_paginated(self, url, *args, **kwargs):
        while url:
            response = self.request('get', url, *args, **kwargs)

            yield response

            url = None
            link_header = response.headers.get('Link')
            if link_header:
                links = GithubLinkHeader.parse(link_header)
                for link in links:
                    if link.rel == 'next':
                        url = link.url
                        break

    def get_project(self, name):
        projects = self.projects
        for project in projects:
            if project['name'].lower() == name.lower():
                return project
        else:
            raise CommandError(f'Unable to find project name={name}')

    def move_card(self, card, column, position=None):
        position = (position or 'top')
        if position not in ('bottom', 'top'):
            raise CardError('position must be \'bottom\' or \'top\'')

        full_url = self.get_full_url(CARD_MOVE_ENDPOINT, id=card['id'])
        data = {
          'position': position,
          'column_id': column['id'],
        }

        try:
            return self.request('post', full_url, json=data)
        except Exception as exc:
            import pdb; pdb.set_trace()
            print(exc)

    def move_column(self, column_data, position):
        url = self.get_full_url(COLUMN_MOVE_ENDPOINT, id=column_data['id'])
        data = {
            'position': position,
        }

        return self.request('post', url, json=data)

    @property
    def owner(self):
        return ISSUE_BACKEND_USER

    @property
    def repo(self):
        return ISSUE_BACKEND_REPO

    @property
    @lru_cache()
    def projects(self):
        full_url = self.get_full_url(PROJECTS_ENDPOINT, owner=ISSUE_BACKEND_REPO)

        return self.request('get', full_url).json()

    def request(self, method, *args, **kwargs):
        method_fn = getattr(self.session, method)

        response = method_fn(*args, **kwargs)
        response.raise_for_status()

        return response

    @lru_cache()
    def search(self, q):
        """
        Args:
            q (str): a github api search query
        """
        url = self.get_full_url(SEARCH_ISSUE_ENDPOINT)
        params = {
            'q': q,
        }

        return self.request('get', url, params=params).json()

    @property
    @lru_cache()
    def session(self):
        s = requests.Session()
        s.headers.update({
            'Authorization': 'token {}'.format(ISSUE_BACKEND_API_KEY),
            'Accept': 'application/vnd.github.inertia-preview+json',

        })

        return s

    def update_issue(self, number=None, **kwargs):
        number = number or self.issue_number

        url = self.get_full_url(
            ISSUE_UPDATE_ENDPOINT,
            owner=ISSUE_BACKEND_USER,
            repo=ISSUE_BACKEND_REPO,
            number=number
        )

        return self.request('patch', url, json=kwargs).json()


class Backend(BaseBackend, GithubSession):
    @property
    @lru_cache()
    def issue(self):
        full_url = self.get_full_url(
            ISSUE_BACKEND_ENDPOINT,
            owner=ISSUE_BACKEND_USER,
            repo=ISSUE_BACKEND_REPO,
            issue=self.issue_number
        )

        return self.request('get', full_url).json()

    def get_prefix(self, changetype=None):
        """
        Returns the issues changetype label

        Args:
            changetype (str): optional changetype to use, otherwise, get it from the issue
        """
        if not changetype:
            labels = self.issue['labels']
            for label in labels:
                label_name = label['name']
                if label_name.startswith('changetype:'):
                    changetype = label_name

                    break
            else:
                raise PrefixError('prefix not found for issue_number={}'.format(self.issue_number))

        return changetype.split(':', 1)[-1]

    @property
    def subject(self):
        return self.issue['title']
