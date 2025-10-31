from rest_framework import serializers
from .models import Doubts, Solutions
from users.models import Users
from courses.models import Subjects


class SubjectsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subjects
        fields = ['subjectid', 'subjectname']


class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['userid', 'username']


class DoubtsSerializer(serializers.ModelSerializer):
    subjectid = SubjectsSerializer(read_only=True)
    userid = UsersSerializer(read_only=True)

    class Meta:
        model = Doubts
        fields = ['doubtid', 'subjectid', 'userid', 'doubttext', 'created_at', 'is_active']


class CreateDoubtSerializer(serializers.Serializer):
    subjectid = serializers.IntegerField()
    userid = serializers.CharField(max_length=20)
    doubttext = serializers.CharField()

    class Meta:
        fields = ['subjectid', 'userid', 'doubttext']


class SolutionsSerializer(serializers.ModelSerializer):
    doubtid = DoubtsSerializer(read_only=True)
    userid = UsersSerializer(read_only=True)

    class Meta:
        model = Solutions
        fields = ['solutionid', 'doubtid', 'solution', 'userid', 'created_at', 'is_active']


class CreateSolutionSerializer(serializers.Serializer):
    doubtid = serializers.IntegerField()
    solution = serializers.CharField()
    userid = serializers.CharField(max_length=20, required=False, allow_null=True)

    class Meta:
        fields = ['doubtid', 'solution', 'userid']
