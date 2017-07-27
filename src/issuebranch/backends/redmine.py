import os
import requests

from functools import lru_cache

from . import BaseBackend

ISSUE_BACKEND_URL = os.environ['ISSUE_BACKEND_URL']
ISSUE_BACKEND_ENDPOINT = '/issues/{issue}.json'
ISSUE_BACKEND_API_KEY = os.environ['ISSUE_BACKEND_API_KEY']


class Backend(BaseBackend):
    @property
    @lru_cache()
    def session(self):
        s = requests.Session()
        s.headers.update({
            'X-Redmine-API-Key': ISSUE_BACKEND_API_KEY,
        })

        return s

    @property
    @lru_cache()
    def issue(self):
        full_url = '{}{}'.format(ISSUE_BACKEND_URL, ISSUE_BACKEND_ENDPOINT).format(issue=self.issue_number)

        response = self.session.get(full_url)

        response.raise_for_status()

        return response.json()['issue']

    @property
    def subject(self):
        return self.issue['subject']
