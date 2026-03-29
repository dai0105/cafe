import boto3
import uuid
from django.conf import settings

def upload_to_r2(file, folder=""):
    import uuid
    from django.conf import settings
    import boto3

    ext = file.name.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"

    # ← ここが重要
    folder = folder.rstrip("/")

    if folder:
        key = f"{folder}/{filename}"
    else:
        key = filename

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto"
    )

    s3.upload_fileobj(
        file,
        settings.R2_BUCKET_NAME,
        key,
        ExtraArgs={"ContentType": file.content_type}
    )

    return f"{settings.R2_PUBLIC_URL}/{key}"