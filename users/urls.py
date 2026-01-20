from django.urls import path
from .views import ForgotPasswordView, HardDeleteUserView, ListAllUsersView, LoginUserView, ReactivateUserView, RegisterUserView, UpdatePasswordView, SoftDeleteUserView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register-user'),
    path('update-password/', UpdatePasswordView.as_view(), name='update-password'),
    path('deactivate-user/', SoftDeleteUserView.as_view(), name='soft-delete-user'),
    path('delete-user/', HardDeleteUserView.as_view(), name='hard-delete-user'),
    path('login/', LoginUserView.as_view(), name='login-user'),
    path('all/', ListAllUsersView.as_view(), name='list-all-users'),
    path('reactivate-user/', ReactivateUserView.as_view(), name='reactivate-user'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
]
