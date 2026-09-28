from __future__ import annotations

from db.migrate import apply_schema
from partner_logo_migration import migrate_bundled_logos
from partners import PACKAGE_ROOT
from tests.conftest import S3_BUCKET, requires_db


async def _seed(store):
    async with store._pool.acquire() as conn:
        await apply_schema(conn)


@requires_db
async def test_bundled_logos_move_to_storage(store, asset_storage, s3):
    await _seed(store)

    report = await migrate_bundled_logos(store, asset_storage)

    partners = await store.list_partners()
    assert len(report.migrated) == len(partners) == 5
    for partner in partners:
        assert partner.logo_path.startswith(f"partners/{partner.id}/logo-")
        original = next(m.source for m in report.migrated if m.partner_id == partner.id)
        body = s3.get_object(Bucket=S3_BUCKET, Key=partner.logo_path)["Body"].read()
        assert body == (PACKAGE_ROOT / original).read_bytes()


@requires_db
async def test_rerun_and_next_deploy_keep_migrated_logos(store, asset_storage, s3):
    await _seed(store)
    await migrate_bundled_logos(store, asset_storage)
    before = {p.id: p.logo_path for p in await store.list_partners()}

    second = await migrate_bundled_logos(store, asset_storage)
    await _seed(store)

    assert second.migrated == []
    assert {p.id: p.logo_path for p in await store.list_partners()} == before


@requires_db
async def test_missing_bundled_file_is_reported_and_skipped(store, asset_storage, s3, tmp_path):
    await _seed(store)
    (tmp_path / "media/partners").mkdir(parents=True)
    (tmp_path / "media/partners/esim.jpeg").write_bytes(b"\xff\xd8\xff" + b"\x00" * 8)

    report = await migrate_bundled_logos(store, asset_storage, root=tmp_path)

    assert [m.source for m in report.migrated] == ["media/partners/esim.jpeg"]
    assert len(report.missing) == 4
    still_bundled = [p.logo_path for p in await store.list_partners() if p.logo_path.startswith("media/")]
    assert sorted(still_bundled) == sorted(m.source for m in report.missing)
