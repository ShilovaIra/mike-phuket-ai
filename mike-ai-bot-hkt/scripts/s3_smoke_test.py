"""Live check that dynamic-asset storage works end to end.

Uploads a tiny public object with the S3_* settings from .env, fetches it back
through S3_PUBLIC_BASE_URL (the CDN / custom domain Telegram will use), then
deletes it. Exits 1 on any failure.

Run by hand after creating a bucket, rotating keys, or changing the CDN domain:

    python scripts/s3_smoke_test.py
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from storage import AssetStorage  # noqa: E402

# Fresh CDN custom domains can take a moment to serve a new object.
FETCH_ATTEMPTS = 5
FETCH_DELAY_SECONDS = 2


def main() -> int:
    storage = AssetStorage.from_env(os.environ)
    if storage is None:
        print("!! S3_* settings incomplete in .env")
        return 1

    key = f"smoke-test/{uuid.uuid4().hex}.txt"
    body = f"mike-phuket smoke test {key}".encode()

    print(f"upload  {key}")
    url = storage.upload(key, body, "text/plain")
    try:
        print(f"fetch   {url}")
        for attempt in range(1, FETCH_ATTEMPTS + 1):
            response = requests.get(url, timeout=15)
            if response.status_code == 200 and response.content == body:
                print("ok      public URL serves the uploaded object")
                return 0
            print(f"        attempt {attempt}: HTTP {response.status_code}")
            time.sleep(FETCH_DELAY_SECONDS)
        print("!! public URL never served the object")
        return 1
    finally:
        storage.delete(key)
        print(f"delete  {key}")


if __name__ == "__main__":
    raise SystemExit(main())
