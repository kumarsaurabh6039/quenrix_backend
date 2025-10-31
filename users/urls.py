from django.urls import path
from .views import HardDeleteUserView, RegisterUserView, UpdatePasswordView, SoftDeleteUserView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register-user'),
    path('update-password/', UpdatePasswordView.as_view(), name='update-password'),
    path('deactivate-user/', SoftDeleteUserView.as_view(), name='soft-delete-user'),
    path('delete-user/', HardDeleteUserView.as_view(), name='hard-delete-user'),
]
