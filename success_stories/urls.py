from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import get_success_story_upload_urls, SuccessStoryViewSet

# Standard Router for CRUD operations (GET, POST, PUT, DELETE)
router = DefaultRouter()
router.register(r'success-stories', SuccessStoryViewSet, basename='successstory')

urlpatterns = [
    path('', include(router.urls)),
    # Custom endpoint for S3 Presigned URLs - ensure this function exists in views.py
    path('get-upload-urls/', get_success_story_upload_urls, name='get-success-story-upload-urls'),
]