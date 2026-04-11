from django.urls import path
from .views import (
    AnnouncementCreateView,
    AnnouncementListView,
    AnnouncementDeleteView,
    BatchListView,
)

urlpatterns = [
    # POST  — create a new announcement
    path('create-announcement/', AnnouncementCreateView.as_view(), name='create-announcement'),

    # GET   — list active announcements (optional ?batch_id= filter)
    path('list/', AnnouncementListView.as_view(), name='announcement-list'),

    # DELETE — soft-delete a specific announcement
    path('<int:pk>/delete/', AnnouncementDeleteView.as_view(), name='announcement-delete'),

    # GET   — all batches (used by the admin create-announcement form)
    path('batches/', BatchListView.as_view(), name='batch-list'),
]
