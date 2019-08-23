import os

from functools import lru_cache

import requests
import yaml

ISSUE_BACKEND_API_KEY = os.environ.get('YOUTRACK_TOKEN')

YOUTRACK_API_URL = os.environ.get('YOUTRACK_API_URL')
ISSUES_ENDPOINT = f'{YOUTRACK_API_URL}/issues'

YOUTRACK_PROJECT = os.environ.get('YOUTRACK_PROJECT')


@lru_cache()
def get_user_mapping():
    with open(os.path.expanduser(os.environ['YOUTRACK_USER_MAPPING']), 'r') as fh:
        data = yaml.load(fh)

    return data['user_mapping']


class Session:
    @property
    @lru_cache()
    def session(self):
        s = requests.Session()
        s.headers.update({
            'Authorization': 'Bearer {}'.format(ISSUE_BACKEND_API_KEY),
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })

        return s

    def _get_custom_field(self, name, value, field_type=None):
        field_type = field_type or 'SingleEnumIssueCustomField'

        # if the value is a SingleEnumIssueCustomField, convert the value to a dict
        # otherwise leave it alone
        value = value
        if field_type == 'SingleEnumIssueCustomField':
            value = {'name': value}

        return {
            'name': name,
            '$type': field_type,
            'value': value,
        }

    def create_issue(self, type: str, subsystem: str, summary: str, description: str, extra_fields: list = None):
        custom_fields = [
            self._get_custom_field('Type', type),
            self._get_custom_field('Subsystem', subsystem),
        ]

        if extra_fields:
            for field in extra_fields:
                field_type = field.get('$type')
                field_obj = self._get_custom_field(field['name'], field['value'], field_type=field_type)
                custom_fields.append(field_obj)

        data = {
            'project': {'id': YOUTRACK_PROJECT},
            'summary': summary,
            'description': description,
            'usesMarkdown': True,
            'customFields': custom_fields,
        }

        response = self.session.post(ISSUES_ENDPOINT, json=data)
        response.raise_for_status()

        return response
