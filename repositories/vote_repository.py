from __future__ import annotations

import asyncpg

from models.enums import VoteChoice, VoteKind


class VoteRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def upsert(
        self,
        nomination_id: int,
        vote_kind: VoteKind,
        voter_id: int,
        choice: VoteChoice,
    ) -> None:
        await self.pool.execute(
            """
            INSERT INTO council_votes(nomination_id, vote_kind, voter_id, choice)
            VALUES($1,$2,$3,$4)
            ON CONFLICT (nomination_id, vote_kind, voter_id)
            DO UPDATE SET choice = EXCLUDED.choice, updated_at = NOW()
            """,
            nomination_id,
            vote_kind.value,
            voter_id,
            choice.value,
        )

    async def counts(self, nomination_id: int, vote_kind: VoteKind) -> dict[str, int]:
        rows = await self.pool.fetch(
            """
            SELECT choice, COUNT(*)::INTEGER AS count
            FROM council_votes
            WHERE nomination_id = $1 AND vote_kind = $2
            GROUP BY choice
            """,
            nomination_id,
            vote_kind.value,
        )
        result = {"approve": 0, "reject": 0, "abstain": 0}
        for row in rows:
            result[row["choice"]] = row["count"]
        return result

    async def list_votes(self, nomination_id: int, vote_kind: VoteKind) -> list[asyncpg.Record]:
        return await self.pool.fetch(
            """
            SELECT voter_id, choice
            FROM council_votes
            WHERE nomination_id = $1 AND vote_kind = $2
            """,
            nomination_id,
            vote_kind.value,
        )

    async def list_voter_ids(self, nomination_id: int, vote_kind: VoteKind) -> set[int]:
        rows = await self.pool.fetch(
            "SELECT voter_id FROM council_votes WHERE nomination_id = $1 AND vote_kind = $2",
            nomination_id,
            vote_kind.value,
        )
        return {row["voter_id"] for row in rows}
