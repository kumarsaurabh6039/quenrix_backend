from django.urls import path
from .views import create_note_presigned, get_note_pdf_presigned, get_subjects, list_notes

urlpatterns = [
    path("upload/", create_note_presigned, name="upload-note"),
    path("<int:note_id>/download/", get_note_pdf_presigned, name="note-download"),
    path("list/", list_notes, name="note-list"),
    path("subjects/", get_subjects, name="subject-list"),
]