from django.urls import path
from .views import submit_application
from .views import submit_application, list_applications


urlpatterns = [
    path("submit/", submit_application, name="submit-application"),
    path("list/", list_applications, name="list-applications"),
]