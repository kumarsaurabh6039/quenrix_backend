from rest_framework import viewsets
from .models import SuccessStory
from .serializers import SuccessStorySerializer

class SuccessStoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows success stories to be viewed, created, updated, or deleted.
    """
    queryset = SuccessStory.objects.all()
    serializer_class = SuccessStorySerializer