# batches/urls.py
from django.urls import path
from .views import (
    AssignUserToBatchView, 
    BatchCreateView, 
    BatchUsersView, 
    BatchesByCourseView, 
    DeactivateBatchView, 
    ReactivateBatchView,
    TrainerBatchesView
)

urlpatterns = [
    # Core Batch Management
    path('batch-create/', BatchCreateView.as_view(), name='batch-create'),
    path('batches-by-course/<int:course_id>/', BatchesByCourseView.as_view(), name='batches-by-course'),
    
    # User-Batch Assignments
    path('assign-user-to-batch/', AssignUserToBatchView.as_view(), name='assign-user-to-batch'),
    path('batch-users/<int:batch_id>/', BatchUsersView.as_view(), name='batch-users'),
    
    # Specific Dashboard Fetching (User-Centric)
    path('trainer-batches/<str:user_id>/', TrainerBatchesView.as_view(), name='trainer-batches'),
    
    # Lifecycle Management
    path('deactivate-batch/<int:batch_id>/', DeactivateBatchView.as_view(), name='deactivate-batch'),
    path('reactivate-batch/<int:batch_id>/', ReactivateBatchView.as_view(), name='reactivate-batch'),
]