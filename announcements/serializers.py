from rest_framework import serializers
from .models import Announcement, AnnouncementBatches
from batches.models import Batches

class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batches
        fields = ['batchid', 'batchname']  # Adjust fields if needed


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    batch_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )

    class Meta:
        model = Announcement
        fields = ['title', 'message', 'batch_ids', 'created_by']
