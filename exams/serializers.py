from rest_framework import serializers
from .models import Exams, Questions, Options, ExamAttempts, StudentAnswers, ExamResults, StudentBatches # ✅ StudentBatches को import किया गया

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

class ExamResultDetailSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source='attemptid.examid.examname', read_only=True)
    attempt_date = serializers.DateTimeField(source='attemptid.attemptdate', read_only=True)
    user_id = serializers.CharField(source='attemptid.userid_id', read_only=True)

    class Meta:
        model = ExamResults
        fields = [
            'resultid', 'user_id', 'exam_name', 'attempt_date',
            'total_mcq_score', 'total_descriptive_score',
            'total_coding_score', 'final_score', 'updated_at'
        ]



class ExamCreateSerializer(serializers.Serializer):
    examName = serializers.CharField(max_length=100, required=False)
    courseId = serializers.IntegerField()
    batchId = serializers.IntegerField()
    subjectId = serializers.IntegerField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    questions = serializers.ListField(child=serializers.DictField())
class StudentBatchSerializer(serializers.ModelSerializer):
    batch_name = serializers.CharField(source='batchid.batchName', read_only=True) 
    course_id = serializers.IntegerField(source='batchid.courseid_id', read_only=True)

    class Meta:
        model = StudentBatches
        fields = ['studentbatchid', 'batchid', 'userid', 'batch_name', 'course_id'] 
        
