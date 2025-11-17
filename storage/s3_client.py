import boto3
from django.conf import settings

def s3_client():
    kwargs = {"region_name": settings.AWS_REGION}
    if getattr(settings, "AWS_ACCESS_KEY_ID", None) and getattr(settings, "AWS_SECRET_ACCESS_KEY", None):
        kwargs.update({
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        })
    return boto3.client("s3", **kwargs)

def flight_key(flight_id: str) -> str:
    # e.g., flights/flight-001/flight.log
    prefix = settings.AWS_S3_FLIGHT_PREFIX.strip("/")
    return f"{prefix}/{flight_id}/flight.log"