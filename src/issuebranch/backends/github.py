import os
import json
import requests

from functools import lru_cache as lru_cache_base, wraps

from . import BaseBackend
from ..exceptions import PrefixError

ISSUE_BACKEND_API_KEY = os.environ['ISSUE_BACKEND_API_KEY']
ISSUE_BACKEND_REPO = os.environ['ISSUE_BACKEND_REPO']
ISSUE_BACKEND_URL = 'https://api.github.com'
ISSUE_BACKEND_USER = os.environ['ISSUE_BACKEND_USER']

ISSUE_BACKEND_ENDPOINT = '/repos/{}/{}/issues/{{issue}}'.format(ISSUE_BACKEND_USER, ISSUE_BACKEND_REPO)

PROJECTS_ENDPOINT = '/orgs/{org}/projects'

CARD_CREATE_ENDPOINT = '/projects/columns/{column_id}/cards'
CARD_MOVE_ENDPOINT = '/projects/columns/cards/{id}/moves'


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


class Backend(BaseBackend):
    CardError = CardError

    def create_card(self, column):
        url = self.get_full_url(CARD_CREATE_ENDPOINT, column_id=column['id'])
        data = {
            'content_id': self.issue['id'],
            'content_type': 'Issue',
        }

        return self.request('post', url, json=data)

    @lru_cache()
    def get_card(self, project):
        """
        Returns the card for this issue within the project
        """
        issue_data = self.issue
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
    def get_cards(self, column):
        cards_url = column['cards_url']

        return self.request('get', cards_url).json()

    @lru_cache()
    def get_columns(self, project):
        '''
        Returns the columns in the given project

        Args:
            project (dict): the dictionary from the projects API requests
        '''
        columns_url = project['columns_url']

        return self.request('get', columns_url).json()

    def get_full_url(self, endpoint, **format_args):
        full_url = f'{ISSUE_BACKEND_URL}{endpoint}'.format(**format_args)

        return full_url

    def move_card(self, card, column):
        full_url = self.get_full_url(CARD_MOVE_ENDPOINT, id=card['id'])
        data = {
          'position': 'top',
          'column_id': column['id'],
        }

        try:
            return self.request('post', full_url, json=data)
        except Exception as exc:
            import pdb; pdb.set_trace()
            print(exc)

    def request(self, method, *args, **kwargs):
        method_fn = getattr(self.session, method)

        response = method_fn(*args, **kwargs)
        response.raise_for_status()

        return response

    @property
    @lru_cache()
    def session(self):
        s = requests.Session()
        s.headers.update({
            'Authorization': 'token {}'.format(ISSUE_BACKEND_API_KEY),
            'Accept': 'application/vnd.github.inertia-preview+json',

        })

        return s

    @property
    @lru_cache()
    def issue(self):
        full_url = self.get_full_url(ISSUE_BACKEND_ENDPOINT, issue=self.issue_number)

        return self.request('get', full_url).json()

    @property
    def prefix(self):
        changetype = None

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
    @lru_cache()
    def projects(self):
        full_url = self.get_full_url(PROJECTS_ENDPOINT, org=ISSUE_BACKEND_REPO)

        return self.request('get', full_url).json()

    @property
    def subject(self):
        return self.issue['title']
