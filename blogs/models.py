from django.db import models

class Blog(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    pdf_url = models.TextField()            # S3 object URL
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title