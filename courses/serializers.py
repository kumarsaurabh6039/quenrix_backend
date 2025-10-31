from rest_framework import serializers
from .models import Content, Subjects, Courses, CourseSubjects, SystemSetups

class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = ['contentid', 'contentname', 'contenturl', 'created_at']

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subjects
        fields = ['subjectid', 'subjectname']

class CourseSerializer(serializers.ModelSerializer):
    contentid = ContentSerializer()
    subjects = serializers.SerializerMethodField()

    class Meta:
        model = Courses
        fields = ['courseid', 'coursename', 'contentid', 'created_at', 'subjects']

    def get_subjects(self, obj):
        linked_subjects = Subjects.objects.filter(
            coursesubjects__courseid=obj.courseid
        ).values('subjectid', 'subjectname')
        return list(linked_subjects)

# Serializer for creating a course via stored procedure
class CourseCreateSerializer(serializers.Serializer):
    courseName = serializers.CharField(max_length=255)
    contentUrl = serializers.CharField(max_length=500)
    subjects = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=False
    )


class CourseUpdateSerializer(serializers.Serializer):
    courseId = serializers.IntegerField()
    courseName = serializers.CharField(max_length=255, required=False)
    contentUrl = serializers.CharField(max_length=500, required=False)
    subjects = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False
    )


class SystemSetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetups
        fields = [
            'setupid',
            'setupname',
            'setupdescription',
            'setupurl',
            'is_active',
            'created_at'
        ]
