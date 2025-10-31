from rest_framework import serializers
from .models import Exams, Questions, Options, ExamAttempts, StudentAnswers, ExamResults

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Options
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = Questions
        fields = '__all__'

    def get_options(self, obj):
        return OptionSerializer(obj.options_set.all(), many=True).data

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exams
        fields = '__all__'

class ExamAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamAttempts
        fields = '__all__'

class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswers
        fields = '__all__'

class ExamResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamResults
        fields = '__all__'


class ExamCreateSerializer(serializers.Serializer):
    examName = serializers.CharField(max_length=100, required=False)
    courseId = serializers.IntegerField()
    batchId = serializers.IntegerField()
    subjectId = serializers.IntegerField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    questions = serializers.ListField(child=serializers.DictField())
