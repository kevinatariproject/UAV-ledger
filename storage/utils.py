from django.conf import settings
from .s3_client import s3_client, flight_key

def list_flight_ids():
    s3 = s3_client()
    bucket = settings.AWS_S3_BUCKET
    prefix = settings.AWS_S3_FLIGHT_PREFIX.strip("/") + "/"

    flights, token = [], None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix, "Delimiter": "/"}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)

        for cp in resp.get("CommonPrefixes", []):
            subprefix = cp.get("Prefix")
            flight_id = subprefix[len(prefix):].strip("/")
            try:
                s3.head_object(Bucket=bucket, Key=flight_key(flight_id))
                flights.append(flight_id)
            except s3.exceptions.ClientError:
                pass

        if resp.get("IsTruncated"):
            token = resp["NextContinuationToken"]
        else:
            break

    return sorted(flights)

def list_versions(flight_id: str):
    s3 = s3_client()
    bucket = settings.AWS_S3_BUCKET
    key = flight_key(flight_id)

    resp = s3.list_object_versions(Bucket=bucket, Prefix=key)
    versions = [
        {
            "version_id": v.get("VersionId"),
            "is_latest": v.get("IsLatest"),
            "size": v.get("Size"),
            "last_modified": v.get("LastModified"),
            "etag": v.get("ETag"),
        }
        for v in resp.get("Versions", []) if v.get("Key") == key
    ]
    # newest first
    versions.sort(key=lambda x: x["last_modified"], reverse=True)
    return key, versions
