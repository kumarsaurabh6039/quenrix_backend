from django.urls import path
from . import views

urlpatterns = [
    path('list-topicwise-questions/', views.list_topicwise_questions, name='list_topicwise_questions'),
    path('create-topicwise-questions/', views.create_topicwise_question, name='create_topicwise_question'),
]
