from django.urls import path
from .views import AnnouncementCreateView

urlpatterns = [
    path('create-announcement/', AnnouncementCreateView.as_view(), name='create-announcement'),
]
