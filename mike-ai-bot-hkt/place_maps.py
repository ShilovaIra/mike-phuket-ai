"""Count a Mini App tap that opens a place in Google Maps.

The row keeps the Partner who owned the place at that moment. A later
move, unlink, or deletion of the place leaves those rows where they are.
"""

from __future__ import annotations

from uuid import UUID

import asyncpg

SELECT_PLACE_MAP_OPEN_COUNT = """
SELECT COUNT(*)::int
FROM place_map_opens
WHERE partner_id = $1
"""


def tracked_maps_url(
    *, place_id: UUID, partner_id: UUID | None, maps_url: str | None
) -> str:
    raw = (maps_url or "").strip()
    if partner_id is None or not raw:
        return raw
    return f"/api/places/{place_id}/maps"


async def open_place_maps(pool: asyncpg.Pool, place_id: UUID) -> str | None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT id, partner_id, maps_url
                FROM places
                WHERE id = $1
                """,
                place_id,
            )
            if row is None or not (row["maps_url"] or "").strip():
                return None
            if row["partner_id"] is not None:
                await conn.execute(
                    """
                    INSERT INTO place_map_opens (partner_id, place_id)
                    VALUES ($1, $2)
                    """,
                    row["partner_id"],
                    row["id"],
                )
            return row["maps_url"]
