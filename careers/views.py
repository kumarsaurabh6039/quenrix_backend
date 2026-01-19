from rest_framework import generics
from .models import Job
from .serializers import JobSerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
class JobListCreateView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]

    queryset = Job.objects.all()
    serializer_class = JobSerializer

class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [AllowAny]
    queryset = Job.objects.all()
    serializer_class = JobSerializer