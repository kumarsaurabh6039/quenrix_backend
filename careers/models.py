from django.db import models

class Job(models.Model):
    # Note: Removed strict CHOICES to allow manual entry from frontend
    
    title = models.CharField(max_length=200)
    
    # Department ab hardcoded nahi hai, user naya bhi daal sakta hai
    department = models.CharField(max_length=100, default='Development') 
    
    # Type ab hardcoded nahi hai
    type = models.CharField(max_length=100, default='Full Time')
    
    location = models.CharField(max_length=100)
    experience = models.CharField(max_length=100) # e.g. "2-4 Years"
    description = models.TextField()
    skills = models.JSONField(default=list) # Stores array of skills
    posted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.department}"

    class Meta:
        ordering = ['-posted_date']