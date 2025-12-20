# batches/serializers.py
from rest_framework import serializers

class BatchCreateSerializer(serializers.Serializer):
    batchName = serializers.CharField(max_length=100)
    courseId = serializers.IntegerField()
    start_date = serializers.DateField()       # Date format (YYYY-MM-DD) handle karega
    timing = serializers.CharField(max_length=100)
    mode = serializers.CharField(max_length=50)

class AssignUserToBatchSerializer(serializers.Serializer):
    batchId = serializers.IntegerField()
    userId = serializers.CharField(max_length=20)
    role = serializers.ChoiceField(choices=['trainer', 'student'])
