from django.db import models

class SuccessStory(models.Model):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    package = models.CharField(max_length=100) # e.g., "24 LPA"
    quote = models.TextField()
    image = models.TextField(blank=True, null=True) 
    logo = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.company}"

    class Meta:
        ordering = ['-created_at'] # Latest stories pehle dikhengi