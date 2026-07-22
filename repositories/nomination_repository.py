from __future__ import annotations

from datetime import datetime

import asyncpg

from models.enums import DecisionType, NominationStatus, Rank
from models.records import Nomination


class NominationRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    @staticmethod
    def _to_model(row: asyncpg.Record | None) -> Nomination | None:
        if row is None:
            return None
        decision_type = DecisionType(row["decision_type"]) if row["decision_type"] else None
        return Nomination(
            id=row["id"],
            guild_id=row["guild_id"],
            candidate_id=row["candidate_id"],
            nominated_by_id=row["nominated_by_id"],
            rank=Rank(row["rank"]),
            reason=row["reason"],
            status=NominationStatus(row["status"]),
            current_commandment=row["current_commandment"],
            ceremony_channel_id=row["ceremony_channel_id"],
            ceremony_message_id=row["ceremony_message_id"],
            vote_message_id=row["vote_message_id"],
            pending_vote_kind=row["pending_vote_kind"],
            pending_founder_reason=row["pending_founder_reason"],
            decision_type=decision_type,
            decision_by_id=row["decision_by_id"],
            created_at=row["created_at"],
            probation_started_at=row["probation_started_at"],
            promoted_at=row["promoted_at"],
            closed_at=row["closed_at"],
        )

    async def create(
        self,
        *,
        guild_id: int,
        candidate_id: int,
        nominated_by_id: int,
        rank: Rank,
        reason: str | None,
        ceremony_channel_id: int,
    ) -> Nomination:
        row = await self.pool.fetchrow(
            """
            INSERT INTO nominations (
                guild_id, candidate_id, nominated_by_id, rank, reason,
                status, ceremony_channel_id
            ) VALUES ($1,$2,$3,$4,$5,$6,$7)
            RETURNING *
            """,
            guild_id,
            candidate_id,
            nominated_by_id,
            rank.value,
            reason,
            NominationStatus.CONVOCATION.value,
            ceremony_channel_id,
        )
        model = self._to_model(row)
        assert model is not None
        return model

    async def get(self, nomination_id: int) -> Nomination | None:
        return self._to_model(
            await self.pool.fetchrow("SELECT * FROM nominations WHERE id = $1", nomination_id)
        )

    async def get_active_for_candidate(self, guild_id: int, candidate_id: int) -> Nomination | None:
        row = await self.pool.fetchrow(
            """
            SELECT * FROM nominations
            WHERE guild_id = $1 AND candidate_id = $2
              AND status IN (
                'convocation','commandments','oath','suspended','nomination_vote',
                'waiting_founder','probation','final_confirmation','adoubement_vote'
              )
            ORDER BY created_at DESC
            LIMIT 1
            """,
            guild_id,
            candidate_id,
        )
        return self._to_model(row)

    async def list_active(self, guild_id: int) -> list[Nomination]:
        rows = await self.pool.fetch(
            """
            SELECT * FROM nominations
            WHERE guild_id = $1
              AND status IN (
                'convocation','commandments','oath','suspended','nomination_vote',
                'waiting_founder','probation','final_confirmation','adoubement_vote'
              )
            ORDER BY created_at DESC
            """,
            guild_id,
        )
        return [self._to_model(row) for row in rows if row is not None]  # type: ignore[misc]


    async def list_all_active(self) -> list[Nomination]:
        rows = await self.pool.fetch(
            """
            SELECT * FROM nominations
            WHERE status IN (
                'convocation','commandments','oath','suspended','nomination_vote',
                'waiting_founder','probation','final_confirmation','adoubement_vote'
            )
            ORDER BY created_at ASC
            """
        )
        return [self._to_model(row) for row in rows if row is not None]  # type: ignore[misc]

    async def list_history(self, guild_id: int, limit: int = 20) -> list[Nomination]:
        rows = await self.pool.fetch(
            "SELECT * FROM nominations WHERE guild_id = $1 ORDER BY created_at DESC LIMIT $2",
            guild_id,
            limit,
        )
        return [self._to_model(row) for row in rows if row is not None]  # type: ignore[misc]

    async def set_message_ids(
        self,
        nomination_id: int,
        *,
        ceremony_message_id: int | None = None,
        vote_message_id: int | None = None,
    ) -> None:
        await self.pool.execute(
            """
            UPDATE nominations SET
                ceremony_message_id = COALESCE($2, ceremony_message_id),
                vote_message_id = COALESCE($3, vote_message_id)
            WHERE id = $1
            """,
            nomination_id,
            ceremony_message_id,
            vote_message_id,
        )

    async def set_status(
        self,
        nomination_id: int,
        status: NominationStatus,
        *,
        close: bool = False,
    ) -> None:
        await self.pool.execute(
            """
            UPDATE nominations SET
                status = $2,
                closed_at = CASE WHEN $3 THEN NOW() ELSE closed_at END
            WHERE id = $1
            """,
            nomination_id,
            status.value,
            close,
        )

    async def accept_commandment(self, nomination_id: int, number: int) -> None:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    """
                    INSERT INTO commandment_acceptances(nomination_id, commandment_number)
                    VALUES($1,$2)
                    ON CONFLICT DO NOTHING
                    """,
                    nomination_id,
                    number,
                )
                await connection.execute(
                    "UPDATE nominations SET current_commandment = $2 WHERE id = $1",
                    nomination_id,
                    number,
                )

    async def start_probation(
        self,
        nomination_id: int,
        decision_type: DecisionType,
        decision_by_id: int | None,
    ) -> None:
        await self.pool.execute(
            """
            UPDATE nominations SET
                status = $2,
                probation_started_at = COALESCE(probation_started_at, NOW()),
                pending_vote_kind = NULL,
                pending_founder_reason = NULL,
                decision_type = $3,
                decision_by_id = $4
            WHERE id = $1
            """,
            nomination_id,
            NominationStatus.PROBATION.value,
            decision_type.value,
            decision_by_id,
        )

    async def mark_promoted(
        self,
        nomination_id: int,
        decision_type: DecisionType,
        decision_by_id: int | None,
    ) -> None:
        await self.pool.execute(
            """
            UPDATE nominations SET
                status = $2,
                promoted_at = NOW(),
                closed_at = NOW(),
                pending_vote_kind = NULL,
                pending_founder_reason = NULL,
                decision_type = $3,
                decision_by_id = $4
            WHERE id = $1
            """,
            nomination_id,
            NominationStatus.PROMOTED.value,
            decision_type.value,
            decision_by_id,
        )

    async def wait_for_founder(self, nomination_id: int, vote_kind: str, reason: str) -> None:
        await self.pool.execute(
            """
            UPDATE nominations SET
                status = $2,
                pending_vote_kind = $3,
                pending_founder_reason = $4
            WHERE id = $1
            """,
            nomination_id,
            NominationStatus.WAITING_FOUNDER.value,
            vote_kind,
            reason,
        )

    async def clear_votes_and_open(self, nomination_id: int, vote_kind: str) -> None:
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    "DELETE FROM council_votes WHERE nomination_id = $1 AND vote_kind = $2",
                    nomination_id,
                    vote_kind,
                )
                status = (
                    NominationStatus.NOMINATION_VOTE.value
                    if vote_kind == "nomination"
                    else NominationStatus.ADOUBEMENT_VOTE.value
                )
                await connection.execute(
                    """
                    UPDATE nominations SET status = $2, pending_vote_kind = $3,
                        pending_founder_reason = NULL
                    WHERE id = $1
                    """,
                    nomination_id,
                    status,
                    vote_kind,
                )

    async def set_final_confirmation(self, nomination_id: int) -> None:
        await self.set_status(nomination_id, NominationStatus.FINAL_CONFIRMATION)
