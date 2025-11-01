# resume/serializers.py
from rest_framework import serializers

from resume.models import ProficiencyLevels, SkillsMaster, TechStack

class ResumeSerializer(serializers.Serializer):
    userId = serializers.CharField(max_length=20)
    personalInfo = serializers.JSONField()
    education = serializers.JSONField(required=False)
    experience = serializers.JSONField(required=False)
    skills = serializers.JSONField(required=False)
    projects = serializers.JSONField(required=False)


class ResumeResponseSerializer(serializers.Serializer):
    resume_json = serializers.JSONField()

class TechStackSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechStack
        fields = ['tech_stackid', 'techname']


class SkillsMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillsMaster
        fields = ['skillmasterid', 'skillname', 'categoryid']


class ProficiencyLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProficiencyLevels
        fields = ['proficiencyid', 'levelname']