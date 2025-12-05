from rest_framework import serializers
from .models import SuccessStory

class SuccessStorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SuccessStory
        fields = ['id', 'name', 'role', 'company', 'package', 'quote', 'image', 'logo', 'created_at']