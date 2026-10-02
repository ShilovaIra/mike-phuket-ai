from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import S3_BUCKET, S3_ENV, requires_db

CDN = S3_ENV["S3_PUBLIC_BASE_URL"]
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.fixture(autouse=True)
def _admin_jwt_secret(monkeypatch):
    monkeypatch.setenv("ADMIN_JWT_SECRET", "test-admin-jwt-secret-at-least-32-chars")


@asynccontextmanager
async def authed_client(store, storage):
    from admin_api.app import create_app

    await store.create_admin_user(email="admin@example.com", password="admin123")
    app = create_app(store=store, storage=storage)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "admin123"},
        )
        client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
        yield client


def _key_from_url(url: str) -> str:
    assert url.startswith(CDN + "/")
    return url[len(CDN) + 1 :]


async def _upload(client, data: bytes, filename: str = "logo.png", content_type: str = "image/png"):
    return await client.post(
        "/api/partner-logos/uploads",
        files={"file": (filename, data, content_type)},
    )


@requires_db
async def test_upload_stages_logo_under_tmp_with_preview(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        response = await _upload(client, PNG)

    assert response.status_code == 201
    body = response.json()
    assert body["upload_token"]
    key = _key_from_url(body["preview_url"])
    assert key.startswith("tmp/") and key.endswith(".png")
    obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
    assert obj["Body"].read() == PNG
    assert obj["ContentType"] == "image/png"


def _bucket_keys(s3) -> list[str]:
    return [o["Key"] for o in s3.list_objects_v2(Bucket=S3_BUCKET).get("Contents", [])]


@requires_db
async def test_upload_rejects_non_jpeg_png_even_if_named_png(store, asset_storage, s3):
    webp = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 32
    async with authed_client(store, asset_storage) as client:
        response = await _upload(client, webp, filename="logo.png", content_type="image/png")

    assert response.status_code == 400
    assert response.json()["detail"] == "Только JPEG или PNG"
    assert _bucket_keys(s3) == []


@requires_db
async def test_upload_rejects_file_over_5_mb(store, asset_storage, s3):
    too_big = PNG + b"\x00" * (5 * 1024 * 1024 - len(PNG) + 1)
    async with authed_client(store, asset_storage) as client:
        response = await _upload(client, too_big)

    assert response.status_code == 400
    assert response.json()["detail"] == "Файл больше 5 МБ"
    assert _bucket_keys(s3) == []


STORAGE_DOWN = "Хранилище недоступно, попробуйте позже"


@requires_db
async def test_upload_reports_unreachable_storage(store, s3):
    from storage import AssetStorage

    broken = AssetStorage.from_env({**S3_ENV, "S3_BUCKET": "no-such-bucket"})
    async with authed_client(store, broken) as client:
        response = await _upload(client, PNG)

    assert response.status_code == 503
    assert response.json()["detail"] == STORAGE_DOWN


async def _create_partner(client, name: str = "Test Dive") -> str:
    created = await client.post(
        "/api/partners",
        json={"name": name, "type": "excursions", "referral_url": "https://example.com/dive"},
    )
    assert created.status_code == 201
    return created.json()["id"]


async def _link(client, partner_id: str, upload_token: str):
    return await client.put(
        f"/api/partners/{partner_id}/logo",
        json={"upload_token": upload_token},
    )


@requires_db
async def test_link_moves_upload_to_partner_and_returns_logo_url(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        partner_id = await _create_partner(client)
        upload = (await _upload(client, PNG)).json()

        linked = await _link(client, partner_id, upload["upload_token"])
        listed = (await client.get("/api/partners")).json()

    assert linked.status_code == 200
    body = linked.json()
    assert body["logo_path"].startswith(f"partners/{partner_id}/logo-")
    assert body["logo_path"].endswith(".png")
    assert body["logo_url"] == f"{CDN}/{body['logo_path']}"
    assert _bucket_keys(s3) == [body["logo_path"]]
    assert s3.get_object(Bucket=S3_BUCKET, Key=body["logo_path"])["Body"].read() == PNG
    assert [p["logo_url"] for p in listed if p["id"] == partner_id] == [body["logo_url"]]


def _expired_upload_token(key: str) -> str:
    import jwt

    from admin_api.tokens import jwt_secret

    payload = {"purpose": "logo_upload", "key": key, "exp": 1}
    return jwt.encode(payload, jwt_secret(), algorithm="HS256")


@requires_db
@pytest.mark.parametrize("token_kind", ["garbage", "expired", "admin_session"])
async def test_link_rejects_invalid_upload_token(store, asset_storage, s3, token_kind):
    async with authed_client(store, asset_storage) as client:
        partner_id = await _create_partner(client)
        upload = (await _upload(client, PNG)).json()
        staged_key = _key_from_url(upload["preview_url"])
        token = {
            "garbage": "not-a-token",
            "expired": _expired_upload_token(staged_key),
            "admin_session": client.headers["Authorization"].removeprefix("Bearer "),
        }[token_kind]

        linked = await _link(client, partner_id, token)
        listed = (await client.get("/api/partners")).json()

    assert linked.status_code == 400
    assert linked.json()["detail"] == "Загрузка устарела, выберите файл заново"
    assert [p["logo_path"] for p in listed if p["id"] == partner_id] == [""]


@requires_db
async def test_relinking_deletes_previous_uploaded_logo(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        partner_id = await _create_partner(client)
        first = (await _upload(client, PNG)).json()
        first_key = (await _link(client, partner_id, first["upload_token"])).json()["logo_path"]
        second = (await _upload(client, JPEG, "new.jpg", "image/jpeg")).json()

        relinked = (await _link(client, partner_id, second["upload_token"])).json()

    assert relinked["logo_path"] != first_key
    assert relinked["logo_path"].endswith(".jpg")
    assert _bucket_keys(s3) == [relinked["logo_path"]]


@requires_db
async def test_relinking_leaves_bundled_logo_files_alone(store, asset_storage, s3):
    from pathlib import Path

    from partners import PACKAGE_ROOT

    async with authed_client(store, asset_storage) as client:
        partner_id = await _create_partner(client)
        async with store._pool.acquire() as conn:
            await conn.execute(
                "UPDATE partners SET logo_path = 'media/partners/esim.jpeg' WHERE id = $1",
                partner_id,
            )
        upload = (await _upload(client, PNG)).json()

        linked = await _link(client, partner_id, upload["upload_token"])

    assert linked.status_code == 200
    assert Path(PACKAGE_ROOT, "media/partners/esim.jpeg").is_file()
    assert _bucket_keys(s3) == [linked.json()["logo_path"]]


@requires_db
async def test_link_to_unknown_partner_leaves_no_copy(store, asset_storage, s3):
    from uuid import uuid4

    async with authed_client(store, asset_storage) as client:
        upload = (await _upload(client, PNG)).json()

        linked = await _link(client, str(uuid4()), upload["upload_token"])

    assert linked.status_code == 404
    assert _bucket_keys(s3) == [_key_from_url(upload["preview_url"])]


@requires_db
async def test_remove_logo_clears_partner_and_deletes_file(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        partner_id = await _create_partner(client)
        upload = (await _upload(client, PNG)).json()
        await _link(client, partner_id, upload["upload_token"])

        removed = await client.delete(f"/api/partners/{partner_id}/logo")

    assert removed.status_code == 200
    assert removed.json()["logo_path"] == ""
    assert removed.json()["logo_url"] == ""
    assert _bucket_keys(s3) == []


@requires_db
async def test_upload_requires_admin_login(store, asset_storage, s3):
    async with authed_client(store, asset_storage) as client:
        del client.headers["Authorization"]
        response = await _upload(client, PNG)

    assert response.status_code == 401
    assert _bucket_keys(s3) == []


@requires_db
async def test_upload_reports_unconfigured_storage(store):
    async with authed_client(store, None) as client:
        response = await _upload(client, PNG)

    assert response.status_code == 503
    assert response.json()["detail"] == STORAGE_DOWN
