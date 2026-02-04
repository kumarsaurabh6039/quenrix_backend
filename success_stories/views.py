from rest_framework import viewsets, status
from .models import SuccessStory
from .serializers import SuccessStorySerializer
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
import uuid
import boto3
from botocore.config import Config

# S3 Client (Signature V4 mandatory for ap-south-2)
s3_client = boto3.client(
    "s3",
    region_name="ap-south-2",
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "virtual"}
    )
)

BUCKET = "amzn-hyd-myapp-lms-bucket01"

def generate_presigned_get_url(key):
    """
    Helper to generate a temporary GET URL for private S3 objects
    """
    try:
        return s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": BUCKET, "Key": key},
            ExpiresIn=3600 # URL valid for 1 hour
        )
    except Exception:
        return None

def extract_s3_key(url_or_key):
    """
    Extracts the key from a full S3 URL if necessary.
    If it's already a key (like 'Success-Stories/...'), it returns it as is.
    """
    if not url_or_key:
        return None
    if "amazonaws.com/" in url_or_key:
        return url_or_key.split("amazonaws.com/")[-1]
    return url_or_key

class SuccessStoryViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = SuccessStory.objects.all()
    serializer_class = SuccessStorySerializer

    def list(self, request, *args, **kwargs):
        """
        Override list to inject presigned GET URLs for all stories
        """
        response = super().list(request, *args, **kwargs)
        for item in response.data:
            if item.get("image"):
                key = extract_s3_key(item["image"])
                item["image"] = generate_presigned_get_url(key)
            if item.get("logo"):
                key = extract_s3_key(item["logo"])
                item["logo"] = generate_presigned_get_url(key)
        return response

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to inject presigned GET URLs for a single story
        """
        response = super().retrieve(request, *args, **kwargs)
        if response.data.get("image"):
            key = extract_s3_key(response.data["image"])
            response.data["image"] = generate_presigned_get_url(key)
        if response.data.get("logo"):
            key = extract_s3_key(response.data["logo"])
            response.data["logo"] = generate_presigned_get_url(key)
        return response


@api_view(["POST"])
@permission_classes([AllowAny])
def get_success_story_upload_urls(request):
    """
    Generate presigned PUT URLs for image & logo upload (Working as before)
    """
    try:
        image_mime = request.data.get("image_mime")
        logo_mime = request.data.get("logo_mime")

        if not image_mime or not logo_mime:
            return Response(
                {"error": "image_mime and logo_mime are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        mime_to_ext = {
            "image/png": "png",
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/webp": "webp"
        }

        image_ext = mime_to_ext.get(image_mime, "jpg")
        logo_ext = mime_to_ext.get(logo_mime, "png")

        image_key = f"Success-Stories/Profiles/{uuid.uuid4()}.{image_ext}"
        logo_key = f"Success-Stories/Logos/{uuid.uuid4()}.{logo_ext}"

        image_upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET,
                "Key": image_key,
                "ContentType": image_mime
            },
            ExpiresIn=3600,
            HttpMethod="PUT"
        )

        logo_upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET,
                "Key": logo_key,
                "ContentType": logo_mime
            },
            ExpiresIn=3600,
            HttpMethod="PUT"
        )

        return Response({
            "image": {
                "upload_url": image_upload_url,
                "final_url": f"https://{BUCKET}.s3.ap-south-2.amazonaws.com/{image_key}"
            },
            "logo": {
                "upload_url": logo_upload_url,
                "final_url": f"https://{BUCKET}.s3.ap-south-2.amazonaws.com/{logo_key}"
            }
        })

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )