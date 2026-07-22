from __future__ import annotations

import asyncpg

from models.records import GuildConfig


class ConfigRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    @staticmethod
    def _to_model(row: asyncpg.Record | None) -> GuildConfig | None:
        if row is None:
            return None
        return GuildConfig(
            guild_id=row["guild_id"],
            founder_id=row["founder_id"],
            ceremony_channel_id=row["ceremony_channel_id"],
            log_channel_id=row["log_channel_id"],
            admin_role_id=row["admin_role_id"],
            staff_role_id=row["staff_role_id"],
            moderator_role_id=row["moderator_role_id"],
            future_admin_role_id=row["future_admin_role_id"],
            future_staff_role_id=row["future_staff_role_id"],
            future_moderator_role_id=row["future_moderator_role_id"],
            quorum_percentage=row["quorum_percentage"],
        )

    async def get(self, guild_id: int) -> GuildConfig | None:
        row = await self.pool.fetchrow(
            "SELECT * FROM guild_configs WHERE guild_id = $1",
            guild_id,
        )
        return self._to_model(row)

    async def upsert(self, config: GuildConfig) -> GuildConfig:
        row = await self.pool.fetchrow(
            """
            INSERT INTO guild_configs (
                guild_id, founder_id, ceremony_channel_id, log_channel_id,
                admin_role_id, staff_role_id, moderator_role_id,
                future_admin_role_id, future_staff_role_id,
                future_moderator_role_id, quorum_percentage
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            ON CONFLICT (guild_id) DO UPDATE SET
                founder_id = EXCLUDED.founder_id,
                ceremony_channel_id = EXCLUDED.ceremony_channel_id,
                log_channel_id = EXCLUDED.log_channel_id,
                admin_role_id = EXCLUDED.admin_role_id,
                staff_role_id = EXCLUDED.staff_role_id,
                moderator_role_id = EXCLUDED.moderator_role_id,
                future_admin_role_id = EXCLUDED.future_admin_role_id,
                future_staff_role_id = EXCLUDED.future_staff_role_id,
                future_moderator_role_id = EXCLUDED.future_moderator_role_id,
                quorum_percentage = EXCLUDED.quorum_percentage,
                updated_at = NOW()
            RETURNING *
            """,
            config.guild_id,
            config.founder_id,
            config.ceremony_channel_id,
            config.log_channel_id,
            config.admin_role_id,
            config.staff_role_id,
            config.moderator_role_id,
            config.future_admin_role_id,
            config.future_staff_role_id,
            config.future_moderator_role_id,
            config.quorum_percentage,
        )
        model = self._to_model(row)
        assert model is not None
        return model
