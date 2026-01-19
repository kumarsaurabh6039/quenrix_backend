from rest_framework.decorators import api_view
from rest_framework.response import Response

from blogs.serializers import BlogSerializer
from .models import Blog
from .utils.aws import generate_presigned_url, get_s3_client
from .utils.aws import generate_presigned_url, get_s3_client
# import for giving access to all by saurabh
from rest_framework.decorators import api_view, permission_classes # Import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
BUCKET = "amzn-hyd-myapp-lms-bucket01"

@api_view(["POST"])
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
def list_blogs(request):
    blogs = Blog.objects.all().order_by("-uploaded_at")
    serializer = BlogSerializer(blogs, many=True)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([AllowAny])
def delete_blog(request, blog_id):
    try:
        blog = Blog.objects.get(id=blog_id)
    except Blog.DoesNotExist:
        return Response({"error": "Blog not found"}, status=404)

    # Extract object key
    object_key = blog.pdf_url.split(".amazonaws.com/")[1]

    # Delete from S3
    s3 = get_s3_client()
    s3.delete_object(Bucket=BUCKET, Key=object_key)

    # Delete DB record
    blog.delete()

    return Response({"message": "Blog deleted successfully"})