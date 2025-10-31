from rest_framework import serializers
from .models import SubjectsTopicswiseQuestions


class SubjectsTopicswiseQuestionsSerializer(serializers.ModelSerializer):
    subjectname = serializers.CharField(source='subjectid.subjectname', read_only=True)

    class Meta:
        model = SubjectsTopicswiseQuestions
        fields = [
            'topicquestionid',
            'subjectid',
            'subjectname',
            'topicname',
            'practice_questions_url',
            'is_active',
            'created_at',
        ]


class CreateTopicwiseQuestionRequestSerializer(serializers.Serializer):
    subjectId = serializers.IntegerField()
    topicName = serializers.CharField(max_length=100)
    practice_questions_url = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
