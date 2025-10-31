# resume/urls.py
from django.urls import path
from .views import CreateOrUpdateResumeView, GetResumeView

urlpatterns = [
    path('create-resume/', CreateOrUpdateResumeView.as_view(), name='create_resume'),
    path('get-resume/<str:userId>/', GetResumeView.as_view(), name='get_resume'),
]
