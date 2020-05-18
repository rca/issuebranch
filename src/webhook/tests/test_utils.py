from django.test import TestCase

from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from webhook.utils import get_action_type
from webhook.tests.utils import get_issue_opened_data, get_project_webhook_data


class UtilsTestCase(TestCase):
    def test_get_action_type_project(self):
        data = get_project_webhook_data()

        action_type = get_action_type(data)

        self.assertEquals("project", action_type)

    def test_get_action_type_issue(self):
        data = get_issue_opened_data()

        action_type = get_action_type(data)

        self.assertEquals("issue", action_type)
