from django.urls import path
from .views import create_blog_presigned, create_note_presigned, get_blog_pdf_presigned, get_note_pdf_presigned, list_blogs, list_notes

urlpatterns = [
    path("upload-pdf/", create_blog_presigned, name="upload-pdf"),
    path("<int:blog_id>/download/", get_blog_pdf_presigned, name="blog-download"),
    path("list/", list_blogs, name="blog-list"),
    path("notes/upload/", create_note_presigned, name="upload-note"),
    path("notes/<int:note_id>/download/", get_note_pdf_presigned, name="note-download"),
    path("notes/list/", list_notes, name="note-list"),
]