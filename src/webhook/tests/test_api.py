from unittest import mock

from django.test import TestCase

from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from webhook.tests.utils import get_project_webhook_data


class ProjectTestCase(TestCase):
    @mock.patch('webhook.views.handlers')
    def test_project_call(self, *mocks):
        """
        Ensure the project action is called
        """
        data = get_project_webhook_data()

        client = APIClient()

        url = reverse('webhook-list')

        response = client.post(url, data, format='json')

        self.assertEquals(200, response.status_code)

        handlers_mock = mocks[0]

        handlers_mock.handler_types.get.assert_called_with('project')

        handler = handlers_mock.handler_types.get.return_value
        handler.assert_called_with(data)

        handler.return_value.run.assert_called_with()

    @mock.patch('webhook.views.WebhookViewSet.logger', new_callable=mock.PropertyMock)
    @mock.patch('webhook.views.get_action_type')
    def test_no_action_logged(self, *mocks):
        get_action_type_mock = mocks[0]
        get_action_type_mock.return_value = None

        logger_mock = mocks[1]

        data = {}

        client = APIClient()

        url = reverse('webhook-list')

        response = client.post(url, data, format='json')

        self.assertEquals(200, response.status_code)

        # ensure a warning is logged for an unknown payload
        logger_mock.return_value.warning.assert_called_with(mock.ANY)
