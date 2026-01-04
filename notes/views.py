from rest_framework.decorators import api_view, permission_classes # Import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Note
from .serializers import NoteSerializer
from blogs.utils.aws import generate_presigned_url, generate_presigned_download_url
import uuid

BUCKET = "amzn-hyd-myapp-lms-bucket01"

@api_view(["POST"])
@permission_classes([AllowAny]) # Makes this view public
def create_note_presigned(request):
    try:
        title = request.data.get("title")
        description = request.data.get("description")
        category = request.data.get("category", "Lecture Note")
        subject = request.data.get("subject", "General")

        if not title or not subject:
            return Response({"error": "Title and Subject are required"}, status=400)

        filename = f"{uuid.uuid4()}.pdf"
        clean_subject = subject.strip().replace(" ", "_")
        object_key = f"Notes-PDF/{clean_subject}/{filename}"

        presigned_url = generate_presigned_url(BUCKET, object_key)

        if not presigned_url:
            return Response({"error": "Failed to generate S3 URL"}, status=500)

        s3_file_url = f"https://{BUCKET}.s3.ap-south-2.amazonaws.com/{object_key}"

        note = Note.objects.create(
            title=title,
            description=description,
            category=category,
            subject=subject,
            pdf_url=s3_file_url
        )

        return Response({
            "upload_url": presigned_url,
            "file_url": s3_file_url,
            "note_id": note.id
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
@permission_classes([AllowAny]) # Makes this view public
def get_note_pdf_presigned(request, note_id):
    try:
        note = Note.objects.get(id=note_id)
        if ".amazonaws.com/" in note.pdf_url:
            object_key = note.pdf_url.split(".amazonaws.com/")[1]
        else:
            return Response({"error": "Invalid URL"}, status=500)

        presigned_url = generate_presigned_download_url(BUCKET, object_key)
        return Response({"download_url": presigned_url})
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=404)

@api_view(["GET"])
@permission_classes([AllowAny]) # Makes this view public
def list_notes(request):
    notes = Note.objects.all().order_by("-uploaded_at")
    subject = request.GET.get('subject')
    category = request.GET.get('category')

    if subject:
        notes = notes.filter(subject__iexact=subject)
    if category:
        notes = notes.filter(category__iexact=category)

    serializer = NoteSerializer(notes, many=True)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([AllowAny]) # Makes this view public
def get_subjects(request):
    """
    fetching unique subjects for showing on page
    """
    subjects = Note.objects.values_list('subject', flat=True).distinct().order_by('subject')
    return Response(list(subjects))