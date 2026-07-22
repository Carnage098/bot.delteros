from __future__ import annotations

import asyncpg


class EvaluationRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def create(
        self,
        nomination_id: int,
        author_id: int,
        verdict: str,
        comment: str,
    ) -> None:
        await self.pool.execute(
            """
            INSERT INTO evaluations(nomination_id, author_id, verdict, comment)
            VALUES($1,$2,$3,$4)
            """,
            nomination_id,
            author_id,
            verdict,
            comment,
        )

    async def list_for_nomination(self, nomination_id: int) -> list[asyncpg.Record]:
        return await self.pool.fetch(
            """
            SELECT * FROM evaluations
            WHERE nomination_id = $1
            ORDER BY created_at DESC
            """,
            nomination_id,
        )
