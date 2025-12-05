from rest_framework import serializers
from .models import CourseInquiry

class CourseInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseInquiry
        fields = ['name', 'phone_number', 'email', 'course_name', 'created_at']