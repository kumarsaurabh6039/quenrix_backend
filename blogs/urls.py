from django.urls import path
from .views import create_blog_presigned, delete_blog, get_blog_pdf_presigned, list_blogs

urlpatterns = [
    path("upload-pdf/", create_blog_presigned, name="upload-pdf"),
    path("<int:blog_id>/download/", get_blog_pdf_presigned, name="blog-download"),
    path("list/", list_blogs, name="blog-list"),
    path("<int:blog_id>/delete/", delete_blog, name="blog-delete"),
]