import logging

from rest_framework import viewsets
from rest_framework.response import Response

from . import handlers
from .utils import get_action_type

# noinspection PyMethodMayBeStatic
class WebhookViewSet(viewsets.ViewSet):
    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def create(self, request):
        """
        Handles POST requests
        """
        data = request.data

        action_type = get_action_type(data)
        if action_type:
            handler_cls = handlers.handler_types.get(action_type)
            handler_cls(data).run()
        else:
            self.logger.warning(f'No action_type found for data={data}')

        return Response('ok')
