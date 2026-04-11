from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Announcement, AnnouncementBatches
from .serializers import AnnouncementCreateSerializer, AnnouncementListSerializer
from batches.models import Batches


class AnnouncementCreateView(generics.CreateAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        batch_ids = serializer.validated_data.pop('batch_ids', [])
        announcement = serializer.save()

        for batch_id in batch_ids:
            AnnouncementBatches.objects.create(
                announcement_id=announcement.id,
                batch_id=batch_id
            )

        return Response({
            "message": "Announcement created successfully",
            "announcement_id": announcement.id
        }, status=status.HTTP_201_CREATED)


class AnnouncementListView(APIView):
    """
    GET /announcements/list/?batch_id=<id>
    Returns active announcements for a given batch (or all if no batch_id).
    Ordered by newest first.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        batch_id = request.query_params.get('batch_id')

        if batch_id:
            announcement_ids = AnnouncementBatches.objects.filter(
                batch_id=batch_id
            ).values_list('announcement_id', flat=True)

            announcements = Announcement.objects.filter(
                id__in=announcement_ids,
                is_active=True
            ).order_by('-created_at')
        else:
            announcements = Announcement.objects.filter(
                is_active=True
            ).order_by('-created_at')

        serializer = AnnouncementListSerializer(announcements, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AnnouncementDeleteView(APIView):
    """
    DELETE /announcements/<id>/delete/
    Soft-deletes an announcement by setting is_active = False.
    """
    permission_classes = [permissions.AllowAny]

    def delete(self, request, pk):
        try:
            announcement = Announcement.objects.get(pk=pk)
            announcement.is_active = False
            announcement.save()
            return Response({"message": "Announcement deleted."}, status=status.HTTP_200_OK)
        except Announcement.DoesNotExist:
            return Response({"error": "Announcement not found."}, status=status.HTTP_404_NOT_FOUND)


class BatchListView(APIView):
    """
    GET /announcements/batches/
    Returns all batches for the announcement creation form.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        batches = Batches.objects.all().order_by('batchname')
        data = [{'batchid': b.batchid, 'batchname': b.batchname} for b in batches]
        return Response(data, status=status.HTTP_200_OK)
