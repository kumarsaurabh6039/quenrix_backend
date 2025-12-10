from django.db import models

class Blog(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    pdf_url = models.TextField()            # S3 object URL
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
from django.db import models

# ... apka purana Blog model yaha hoga ...

class Note(models.Model):
    CATEGORY_CHOICES = [
        ('Lecture Note', 'Lecture Note'),
        ('Lab Manual', 'Lab Manual'),
        ('Assignment', 'Assignment'),
        ('Question Paper', 'Question Paper'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Lecture Note')
    subject = models.CharField(max_length=100, help_text="Ex: Data Structures, OS")
    
    pdf_url = models.URLField(max_length=500) # S3 Public URL
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.title}"
