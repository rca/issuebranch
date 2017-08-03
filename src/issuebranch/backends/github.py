from __future__ import absolute_import

import os
import requests

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

from . import BaseBackend
from ..exceptions import PrefixError

ISSUE_BACKEND_API_KEY = os.environ['ISSUE_BACKEND_API_KEY']
ISSUE_BACKEND_REPO = os.environ['ISSUE_BACKEND_REPO']
ISSUE_BACKEND_URL = 'https://api.github.com'
ISSUE_BACKEND_USER = os.environ['ISSUE_BACKEND_USER']

ISSUE_BACKEND_ENDPOINT = '/repos/{}/{}/issues/{{issue}}'.format(ISSUE_BACKEND_USER, ISSUE_BACKEND_REPO)

class Backend(BaseBackend):
    @property
    @lru_cache()
    def session(self):
        s = requests.Session()
        s.headers.update({
            'Authorization': 'token {}'.format(ISSUE_BACKEND_API_KEY),
        })

        return s

    @property
    @lru_cache()
    def issue(self):
        full_url = '{}{}'.format(ISSUE_BACKEND_URL, ISSUE_BACKEND_ENDPOINT).format(issue=self.issue_number)

        response = self.session.get(full_url)

        response.raise_for_status()

        return response.json()

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
    def subject(self):
        return self.issue['title']
