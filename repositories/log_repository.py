from __future__ import annotations

import json

import asyncpg


class LogRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def add(
        self,
        *,
        guild_id: int,
        event_type: str,
        nomination_id: int | None = None,
        actor_id: int | None = None,
        details: dict | None = None,
    ) -> None:
        await self.pool.execute(
            """
            INSERT INTO ceremony_logs(nomination_id, guild_id, actor_id, event_type, details)
            VALUES($1,$2,$3,$4,$5::jsonb)
            """,
            nomination_id,
            guild_id,
            actor_id,
            event_type,
            json.dumps(details or {}, ensure_ascii=False),
        )
