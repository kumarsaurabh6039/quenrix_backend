from django.urls import path
from .views import InquiryCreateView, InquiryListView

urlpatterns = [
    # 1. for submiting
    path('inquiries/create/', InquiryCreateView.as_view(), name='inquiry-create'),
    
    # 2. for fetching
    path('inquiries/list/', InquiryListView.as_view(), name='inquiry-list'),
]