from django.db import models

class ZoomMeeting(models.Model):
    topic = models.CharField(max_length=200)
    zoom_meeting_id = models.CharField(max_length=50)
    start_url = models.TextField()
    join_url = models.TextField()
    start_time = models.DateTimeField()
    recording_url = models.TextField(null=True, blank=True)
