from __future__ import annotations

from typing import Any, Mapping

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

_REQUIRED = (
    "S3_ENDPOINT_URL",
    "S3_REGION",
    "S3_BUCKET",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "S3_PUBLIC_BASE_URL",
)

# Fail fast so an operator sees "storage unavailable" instead of a hung form.
_CLIENT_CONFIG = Config(connect_timeout=5, read_timeout=20, retries={"max_attempts": 2})


class StorageError(Exception):
    """The bucket could not be reached or refused the request."""


class AssetStorage:
    """Dynamic assets (partner logos, place photos) in S3-compatible storage."""

    def __init__(self, *, bucket: str, public_base_url: str, client: Any) -> None:
        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")
        self._client = client

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> AssetStorage | None:
        values = {name: (env.get(name) or "").strip() for name in _REQUIRED}
        if not all(values.values()):
            return None
        client = boto3.client(
            "s3",
            endpoint_url=values["S3_ENDPOINT_URL"],
            region_name=values["S3_REGION"],
            aws_access_key_id=values["S3_ACCESS_KEY_ID"],
            aws_secret_access_key=values["S3_SECRET_ACCESS_KEY"],
            config=_CLIENT_CONFIG,
        )
        return cls(
            bucket=values["S3_BUCKET"],
            public_base_url=values["S3_PUBLIC_BASE_URL"],
            client=client,
        )

    def upload(self, key: str, data: bytes, content_type: str) -> str:
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ACL="public-read",
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(str(exc)) from exc
        return self.public_url(key)

    def copy(self, source_key: str, key: str) -> str:
        try:
            self._client.copy_object(
                Bucket=self._bucket,
                Key=key,
                CopySource={"Bucket": self._bucket, "Key": source_key},
                ACL="public-read",
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(str(exc)) from exc
        return self.public_url(key)

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(str(exc)) from exc

    def expire_prefix(self, prefix: str, *, days: int) -> None:
        """Have the bucket delete objects under prefix after N days (keeps other rules)."""
        rule_id = f"expire-{prefix.strip('/').replace('/', '-')}"
        try:
            try:
                existing = self._client.get_bucket_lifecycle_configuration(
                    Bucket=self._bucket
                )["Rules"]
            except ClientError as exc:
                if exc.response["Error"]["Code"] != "NoSuchLifecycleConfiguration":
                    raise
                existing = []
            rules = [rule for rule in existing if rule.get("ID") != rule_id]
            rules.append(
                {
                    "ID": rule_id,
                    "Status": "Enabled",
                    "Filter": {"Prefix": prefix},
                    "Expiration": {"Days": days},
                }
            )
            self._client.put_bucket_lifecycle_configuration(
                Bucket=self._bucket, LifecycleConfiguration={"Rules": rules}
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(str(exc)) from exc

    def public_url(self, key: str) -> str:
        return f"{self._public_base_url}/{key}"
