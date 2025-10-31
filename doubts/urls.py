from django.urls import path
from .views import (
    CreateDoubtView, CreateSolutionView,
    ListDoubtsView, ListSolutionsView
)

urlpatterns = [
    path('create-doubt/', CreateDoubtView.as_view(), name='create_doubt'),
    path('create-solution/', CreateSolutionView.as_view(), name='create_solution'),
    path('list-doubts/', ListDoubtsView.as_view(), name='list_doubts'),
    path('list-solutions/', ListSolutionsView.as_view(), name='list_solutions'),
]
