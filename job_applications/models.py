from django.db import models

class JobApplication(models.Model):
    job_id = models.IntegerField(help_text="ID of the job position") # Linked to Job ID
    
    # Step 1: Personal Details
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    dob = models.DateField()
    gender = models.CharField(max_length=20)
    location = models.CharField(max_length=255)

    # Step 2: Education
    degree = models.CharField(max_length=100)
    university = models.CharField(max_length=255)
    grad_year = models.IntegerField()
    cgpa = models.CharField(max_length=50)

    # Step 2: Experience (Conditional)
    WORK_STATUS_CHOICES = [('Fresher', 'Fresher'), ('Experienced', 'Experienced')]
    work_status = models.CharField(max_length=20, choices=WORK_STATUS_CHOICES, default='Fresher')
    
    
    current_company = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    experience_years = models.CharField(max_length=50, blank=True, null=True) # Keeping char for '3.5 Years' format flexibility
    current_ctc = models.CharField(max_length=50, blank=True, null=True)
    expected_ctc = models.CharField(max_length=50, blank=True, null=True)
    notice_period = models.CharField(max_length=50, blank=True, null=True)

    
    linkedin_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    
    
    resume_url = models.URLField(max_length=500) 
    
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - Job {self.job_id}"