from rest_framework import serializers
from .models import Blog, Note

class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = ["id", "title", "description", "pdf_url", "uploaded_at"]
class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'title', 'description', 'category', 'subject', 'pdf_url', 'uploaded_at']
