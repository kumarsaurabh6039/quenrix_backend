from django.urls import path
from .views import create_zoom_meeting, list_recordings

urlpatterns = [
    path("create/", create_zoom_meeting),
    path("recordings/", list_recordings),

]
