import base64
import json
import os

from functools import lru_cache

import requests
import yaml

from requests.auth import HTTPBasicAuth

from ..exceptions import PrefixError

ISSUE_BACKEND_API_KEY = os.environ["ISSUE_BACKEND_API_KEY"]

ISSUE_BACKEND_API_URL = os.environ.get("ISSUE_BACKEND_API_URL")
ISSUES_ENDPOINT = "{ISSUE_BACKEND_API_URL}/rest/api/2/issue/{issueIdOrKey}"


ISSUE_BACKEND_PROJECT = os.environ.get("ISSUE_BACKEND_PROJECT")


@lru_cache()
def get_user_mapping():
    with open(os.path.expanduser(os.environ["YOUTRACK_USER_MAPPING"]), "r") as fh:
        data = yaml.load(fh)

    return data["user_mapping"]


class Backend:
    PrefixError = PrefixError

    ACTIVE_COLUMN = "In Progress"

    def __init__(self, issue_number):
        self.issue_number = issue_number

    def move_card(self, column_name):
        self.session.move_card(self.issue_number, column_name)

    @property
    @lru_cache()
    def session(self):
        return Session()

    @property
    def subject(self):
        issue = self.session.get_issue(self.issue_number)

        # print(json.dumps(issue, indent=4))

        subject = issue["fields"]["summary"]

        return subject


class Session:
    @property
    @lru_cache()
    def session(self):
        user, token = ISSUE_BACKEND_API_KEY.split(":", 1)

        session = requests.Session()
        session.auth = HTTPBasicAuth(user, token)
        # s.headers.update(
        #     {
        #         "Accept": "application/json",
        #         "Content-Type": "application/json",
        #     }
        # )

        return session

    def create_issue(
        self,
        type: str,
        subsystem: str,
        summary: str,
        description: str,
        extra_fields: "list | None" = None,
    ):
        pass

    def get_issue(self, issue_id: str):
        issue_endpoint = ISSUES_ENDPOINT.format(
            ISSUE_BACKEND_API_URL=ISSUE_BACKEND_API_URL, issueIdOrKey=issue_id
        )

        params = {
            "fields": "*all",
        }

        response = self.session.get(issue_endpoint, params=params)

        response.raise_for_status()

        return response.json()

    def move_card(self, issue_id: str, column_name: str):
        pass
