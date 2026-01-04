from rest_framework import viewsets
from .models import SuccessStory
from .serializers import SuccessStorySerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
class SuccessStoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows success stories to be viewed, created, updated, or deleted.
    """
    permission_classes = [AllowAny]  #i am writing this for allowing permission(saurabh)
    queryset = SuccessStory.objects.all()
    serializer_class = SuccessStorySerializer