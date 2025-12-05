from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SuccessStoryViewSet

# Router automatically URLs create kar dega standard REST actions ke liye
# GET /api/success-stories/ (List)
# POST /api/success-stories/ (Create)
# PUT /api/success-stories/{id}/ (Update)
# DELETE /api/success-stories/{id}/ (Delete)

router = DefaultRouter()
router.register(r'success-stories', SuccessStoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]