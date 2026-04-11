from rest_framework import serializers
from .models import Announcement, AnnouncementBatches
from batches.models import Batches


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batches
        fields = ['batchid', 'batchname']


class AnnouncementCreateSerializer(serializers.ModelSerializer):
    batch_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True
    )

    class Meta:
        model = Announcement
        fields = ['title', 'message', 'batch_ids', 'created_by']


class AnnouncementListSerializer(serializers.ModelSerializer):
    """Used for GET — returns announcement data with its batch names."""
    batch_names = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'message', 'created_by', 'created_at', 'batch_names']

    def get_batch_names(self, obj):
        ab_qs = AnnouncementBatches.objects.filter(
            announcement_id=obj.id
        ).select_related('batch')
        return [ab.batch.batchname for ab in ab_qs]
