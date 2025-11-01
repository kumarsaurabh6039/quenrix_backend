# resume/urls.py
from django.urls import path
from .views import AddProficiencyView, AddSkillView, AddTechStackView, CreateOrUpdateResumeView, GetResumeView, ResumeSetupDataView

urlpatterns = [
    path('create-resume/', CreateOrUpdateResumeView.as_view(), name='create_resume'),
    path('get-resume/<str:userId>/', GetResumeView.as_view(), name='get_resume'),
    path('setup-data/', ResumeSetupDataView.as_view(), name='resume_setup_data'),
    path('add-techstack/', AddTechStackView.as_view(), name='add_techstack'),
    path('add-skill/', AddSkillView.as_view(), name='add_skill'),
    path('add-proficiency/', AddProficiencyView.as_view(), name='add_proficiency'),
]
