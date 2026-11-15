"""POST /uploads/presign - short-lived S3 POST policy so the browser uploads images straight to S3."""
import os
import uuid

import boto3
from botocore.config import Config

from common import domain
from common.http import api
from common.domain import choice

_s3 = None


def s3():
    global _s3
    if _s3 is None:
        region = os.environ.get("AWS_REGION", "us-east-1")
        _s3 = boto3.client("s3", region_name=region, config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}))
    return _s3


@api
def handler(req):
    uid = req.require_user()
    domain.require_profile(uid, roles=["BUSINESS"])
    content_type = choice(req.json(), "contentType", list(domain.IMAGE_TYPES))
    key = f"images/{uid}/{uuid.uuid4().hex}.{domain.IMAGE_TYPES[content_type]}"
    post = s3().generate_presigned_post(
        Bucket=os.environ["IMAGE_BUCKET"],
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, domain.MAX_IMAGE_BYTES],
        ],
        ExpiresIn=300,
    )
    return {"url": post["url"], "fields": post["fields"], "key": key, "maxBytes": domain.MAX_IMAGE_BYTES}
