from django.urls import path
from .views import InquiryCreateView, InquiryListView, InquiryDeleteView

urlpatterns = [
    # 1. for submitting
    path('inquiries/create/', InquiryCreateView.as_view(), name='inquiry-create'),
    
    # 2. for fetching
    path('inquiries/list/', InquiryListView.as_view(), name='inquiry-list'),

    # 3. for deleting (Single, All, Date-wise)
    path('inquiries/delete/', InquiryDeleteView.as_view(), name='inquiry-delete'),
]