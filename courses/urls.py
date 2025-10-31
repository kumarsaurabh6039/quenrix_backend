from django.urls import path
from .views import CourseCreateView, CourseDeleteView, CourseListView, CourseUpdateView, SubjectWiseSystemSetupView

urlpatterns = [
    path('course-list/', CourseListView.as_view(), name='course-list'),
    path('course-create/', CourseCreateView.as_view(), name='course-create'),
    path('course-update/', CourseUpdateView.as_view(), name='course-update'),
    path('course-delete/<int:course_id>/', CourseDeleteView.as_view(), name='course-delete'),
    path('subjects/<int:subject_id>/system-setups/', SubjectWiseSystemSetupView.as_view(), name='subject-system-setups'),


]
