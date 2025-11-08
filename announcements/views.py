from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Announcement, AnnouncementBatches
from .serializers import AnnouncementCreateSerializer

class AnnouncementCreateView(generics.CreateAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementCreateSerializer
    permission_classes = [permissions.AllowAny]  # 👈 No auth needed

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract and remove batch IDs from validated data
        batch_ids = serializer.validated_data.pop('batch_ids', [])

        # Create announcement
        announcement = serializer.save()

        # Create announcement-batch links
        for batch_id in batch_ids:
            AnnouncementBatches.objects.create(
                announcement_id=announcement.id,
                batch_id=batch_id
            )

        return Response({
            "message": "Announcement created successfully",
            "announcement_id": announcement.id
        }, status=status.HTTP_201_CREATED)


