from rest_framework.decorators import api_view
from rest_framework.response import Response

from blogs.serializers import BlogSerializer
from .models import Blog
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