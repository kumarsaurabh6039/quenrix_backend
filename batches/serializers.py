# batches/serializers.py
from rest_framework import serializers

class BatchCreateSerializer(serializers.Serializer):
    batchName = serializers.CharField(max_length=100)
    courseId = serializers.IntegerField()


class AssignUserToBatchSerializer(serializers.Serializer):
    batchId = serializers.IntegerField()
    userId = serializers.CharField(max_length=20)
    role = serializers.ChoiceField(choices=['trainer', 'student'])
