# resume/serializers.py
from rest_framework import serializers

class ResumeSerializer(serializers.Serializer):
    userId = serializers.CharField(max_length=20)
    personalInfo = serializers.JSONField()
    education = serializers.JSONField(required=False)
    experience = serializers.JSONField(required=False)
    skills = serializers.JSONField(required=False)
    projects = serializers.JSONField(required=False)


class ResumeResponseSerializer(serializers.Serializer):
    resume_json = serializers.JSONField()
