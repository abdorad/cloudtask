from functools import lru_cache
from typing import BinaryIO

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class ObjectStorage:
    """Small S3 adapter that owns the bucket used by CloudTask."""

    def __init__(self) -> None:
        self.bucket = settings.required("s3_bucket")
        self.client: BaseClient = boto3.client(
            "s3",
            endpoint_url=settings.required("s3_endpoint_url"),
            aws_access_key_id=settings.required("s3_access_key"),
            aws_secret_access_key=settings.required("s3_secret_key"),
            region_name="us-east-1",
            config=Config(
                connect_timeout=settings.s3_connect_timeout_seconds,
                read_timeout=settings.s3_read_timeout_seconds,
                retries={"mode": "standard", "total_max_attempts": settings.s3_max_attempts},
            ),
        )

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as error:
            error_code = error.response.get("Error", {}).get("Code", "")
            if error_code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            try:
                self.client.create_bucket(Bucket=self.bucket)
            except ClientError as create_error:
                if create_error.response.get("Error", {}).get("Code") not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                    raise

    def put_stream(self, key: str, stream: BinaryIO, content_type: str) -> None:
        self.ensure_bucket()
        stream.seek(0)
        self.client.upload_fileobj(stream, self.bucket, key, ExtraArgs={"ContentType": content_type})

    def put_json(self, key: str, body: bytes) -> None:
        self.ensure_bucket()
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body, ContentType="application/json")

    def get_bytes(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"]
        try:
            return body.read()
        finally:
            body.close()

    def get_json_response(self, key: str):
        return self.client.get_object(Bucket=self.bucket, Key=key)

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


@lru_cache
def get_object_storage() -> ObjectStorage:
    return ObjectStorage()
