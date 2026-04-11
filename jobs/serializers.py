from rest_framework import serializers
from .models import Createjob


class CreateJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Createjob
        fields = '__all__'


class CreateJobRequestSerializer(serializers.Serializer):
    jobtitle = serializers.CharField(max_length=255)
    job_type = serializers.CharField(max_length=100)
    reqexp = serializers.IntegerField(required=False, allow_null=True, default=0) 
    company = serializers.CharField(max_length=255)
    location = serializers.CharField(max_length=255)
    from_passed_out_year = serializers.IntegerField()
    to_passed_out_year = serializers.IntegerField()
    hr_phone = serializers.CharField(max_length=20)
    hr_email = serializers.CharField(max_length=255)
    job_description = serializers.CharField()
    apply_before_date = serializers.DateField()
    is_active = serializers.BooleanField()
