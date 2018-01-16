from rest_framework import viewsets
from rest_framework.response import Response


# noinspection PyMethodMayBeStatic
class WebhookViewSet(viewsets.ViewSet):
    def create(self, request):
        """
        Handles POST requests
        """
        data = request.data

        print(f'data={data}')

        return Response('ok')
