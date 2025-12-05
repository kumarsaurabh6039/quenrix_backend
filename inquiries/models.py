from django.db import models

# Create your models here.
class CourseInquiry(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    course_name = models.CharField(max_length=200, default="General") 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.course_name}"