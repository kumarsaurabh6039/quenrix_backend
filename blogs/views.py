import uuid
from rest_framework.decorators import api_view
from rest_framework.response import Response

from blogs.serializers import BlogSerializer, NoteSerializer
from .models import Blog, Note
from .utils.aws import generate_presigned_url

BUCKET = "amzn-hyd-myapp-lms-bucket01"

@api_view(["POST"])
def create_blog_presigned(request):
    title = request.data.get("title")
    description = request.data.get("description")

    # Generate file name and path
    import uuid
    filename = f"{uuid.uuid4()}.pdf"
    object_key = f"Blogs-PDF/{filename}"

    # Generate upload URL
    presigned_url = generate_presigned_url(BUCKET, object_key)

    if not presigned_url:
        return Response({"error": "Failed to generate S3 URL"}, status=500)

    # Final S3 URL (to save in DB)
    s3_file_url = f"https://{BUCKET}.s3.ap-south-2.amazonaws.com/{object_key}"

    # Save metadata in MS SQL DB
    blog = Blog.objects.create(
        title=title,
        description=description,
        pdf_url=s3_file_url
    )

    return Response({
        "upload_url": presigned_url,
        "file_url": s3_file_url,
        "blog_id": blog.id
    })



from .utils.aws import generate_presigned_download_url

BUCKET = "amzn-hyd-myapp-lms-bucket01"

@api_view(["GET"])
def get_blog_pdf_presigned(request, blog_id):
    try:
        blog = Blog.objects.get(id=blog_id)
    except Blog.DoesNotExist:
        return Response({"error": "Blog not found"}, status=404)

    # Extract the object key from the saved URL
    # https://bucket.s3.region.amazonaws.com/Blogs-PDF/xxxx.pdf
    object_key = blog.pdf_url.split(".amazonaws.com/")[1]

    # Generate presigned URL for GET
    presigned_url = generate_presigned_download_url(BUCKET, object_key)

    return Response({"download_url": presigned_url})


@api_view(["GET"])
def list_blogs(request):
    blogs = Blog.objects.all().order_by("-uploaded_at")
    serializer = BlogSerializer(blogs, many=True)
    return Response(serializer.data)

@api_view(["POST"])
def create_note_presigned(request):
    """
    Step 1: Save Note metadata and generate S3 Upload URL.
    """
    title = request.data.get("title")
    description = request.data.get("description")
    category = request.data.get("category", "Lecture Note") # Default
    subject = request.data.get("subject", "General")

    # Generate unique filename
    filename = f"{uuid.uuid4()}.pdf"
    # S3 Folder structure: Notes-PDF/Subject/filename.pdf (Organized storage)
    # Space hatane ke liye replace use kiya
    clean_subject = subject.replace(" ", "_")
    object_key = f"Notes-PDF/{clean_subject}/{filename}"

    # Generate Upload URL
    presigned_url = generate_presigned_url(BUCKET, object_key)

    if not presigned_url:
        return Response({"error": "Failed to generate S3 URL"}, status=500)

    # Final S3 URL
    s3_file_url = f"https://{BUCKET}.s3.ap-south-2.amazonaws.com/{object_key}"

    # Save to DB
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
        "note_id": note.id,
        "message": "Metadata saved. Use upload_url to send file."
    })


@api_view(["GET"])
def get_note_pdf_presigned(request, note_id):
    """
    Generate Secure Download Link for a Note
    """
    try:
        note = Note.objects.get(id=note_id)
    except Note.DoesNotExist:
        return Response({"error": "Note not found"}, status=404)

    # Extract Key: "https://bucket.../Notes-PDF/Subject/xyz.pdf" -> "Notes-PDF/Subject/xyz.pdf"
    try:
        object_key = note.pdf_url.split(".amazonaws.com/")[1]
    except IndexError:
        return Response({"error": "Invalid S3 URL in database"}, status=500)

    presigned_url = generate_presigned_download_url(BUCKET, object_key)
    
    return Response({"download_url": presigned_url})


@api_view(["GET"])
def list_notes(request):
    """
    Fetch all notes OR Filter by Category/Subject
    Usage:
    - /api/notes/list/ (All notes)
    - /api/notes/list/?subject=Maths (Only Maths)
    - /api/notes/list/?category=Assignment (Only Assignments)
    """
    notes = Note.objects.all().order_by("-uploaded_at")

    # --- Filtering Logic ---
    subject_filter = request.GET.get('subject')
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search')

    if subject_filter:
        notes = notes.filter(subject__iexact=subject_filter)
    
    if category_filter:
        notes = notes.filter(category__iexact=category_filter)

    if search_query:
        notes = notes.filter(title__icontains=search_query)

    serializer = NoteSerializer(notes, many=True)
    return Response(serializer.data)