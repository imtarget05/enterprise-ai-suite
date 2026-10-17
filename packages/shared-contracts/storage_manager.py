"""
Object Storage Manager for Enterprise AI Suite Monorepo.
Supports Cloudflare R2 and MinIO via S3 API, with automatic fallback
to local persistent disk for zero-dependency offline runs.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple


class StorageManager:
    def __init__(
        self,
        provider: str = "local",
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: str = "enterprise-qc-evidence",
        local_dir: str = "/tmp/enterprise_storage",
    ):
        self.provider = provider
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.local_dir = Path(local_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self._s3_client = None

        if self.provider in ("r2", "minio") and self.endpoint_url and self.access_key and self.secret_key:
            try:
                import boto3
                self._s3_client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name="auto" if self.provider == "r2" else "us-east-1",
                )
            except Exception:
                self.provider = "local"

    def upload_bytes(self, data: bytes, object_name: str, content_type: str = "image/jpeg") -> Tuple[str, str]:
        sha256 = hashlib.sha256(data).hexdigest()
        if self._s3_client:
            try:
                self._s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=data,
                    ContentType=content_type,
                )
                return f"s3://{self.bucket_name}/{object_name}", sha256
            except Exception:
                pass

        target_path = self.local_dir / object_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(data)
        return f"file://{target_path.absolute()}", sha256
