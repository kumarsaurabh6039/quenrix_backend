from django.db import models
from batches.models import Batches

class Announcement(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_by = models.CharField(max_length=20, db_column='created_by', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'announcements'


class AnnouncementBatches(models.Model):
    id = models.AutoField(primary_key=True)
    announcement = models.ForeignKey(
        Announcement, models.DO_NOTHING, db_column='announcement_id'
    )
    batch = models.ForeignKey(
        Batches, models.DO_NOTHING, db_column='batchId'
    )

    class Meta:
        db_table = 'announcement_batches'
