from django.urls import path
from .views import (
    chatbot_view,
    category_list_create,
    category_detail,
    document_upload,
    document_list,
    document_delete,
)

urlpatterns = [
    # ── Chatbot (RAG) ─────────────────────────────────────────────────────
    path("chat/", chatbot_view, name="chatbot_view"),

    # ── Category management ───────────────────────────────────────────────
    path("categories/", category_list_create, name="category_list_create"),
    path("categories/<int:category_id>/", category_detail, name="category_detail"),

    # ── Document management ───────────────────────────────────────────────
    path("documents/upload/", document_upload, name="document_upload"),
    path("categories/<int:category_id>/documents/", document_list, name="document_list"),
    path("documents/<int:doc_id>/", document_delete, name="document_delete"),
]
