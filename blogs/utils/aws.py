import boto3
from django.conf import settings
from botocore.exceptions import ClientError


# def get_s3_client():
#     """Reusable S3 client"""
#     return boto3.client(
#         "s3",
#         region_name='ap-south-2',
#         aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
#     )

def get_s3_client():
    """Reusable S3 client"""
    return boto3.client(
        "s3",
        region_name='ap-south-2',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url="https://s3.ap-south-2.amazonaws.com"
    )


def generate_presigned_url(bucket_name, object_name, expiration=3600):
    s3_client = get_s3_client()

    try:
        url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket_name,
                "Key": object_name,
                "ContentType": "application/pdf"
            },
            ExpiresIn=expiration
        )
        return url

    except ClientError as e:
        print("Error:", e)
        return None



def generate_presigned_download_url(bucket_name, object_key, expiration=3600):
    s3_client = get_s3_client()

    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration
        )
        return url

    except ClientError as e:
        print("Error:", e)
        return None



def generate_presigned_delete_url(bucket_name, object_key, expiration=3600):
    s3_client = get_s3_client()

    try:
        url = s3_client.generate_presigned_url(
            "delete_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print("Error:", e)
        return None
