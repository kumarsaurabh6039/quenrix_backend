from django.urls import path
from .views import codexa_chat_view, execute_code

urlpatterns = [
    path('execute/', execute_code),
    path("codexa/chat/", codexa_chat_view),
]
