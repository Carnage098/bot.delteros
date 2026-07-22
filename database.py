from __future__ import annotations

import logging
from pathlib import Path

import asyncpg

LOGGER = logging.getLogger(__name__)


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self.pool is not None:
            return
        self.pool = await asyncpg.create_pool(
            dsn=self.database_url,
            min_size=1,
            max_size=10,
            command_timeout=60,
            statement_cache_size=0,
        )
        LOGGER.info("Connexion PostgreSQL établie.")

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            LOGGER.info("Connexion PostgreSQL fermée.")

    def require_pool(self) -> asyncpg.Pool:
        if self.pool is None:
            raise RuntimeError("La base de données n'est pas connectée.")
        return self.pool

    async def run_migrations(self) -> None:
        pool = self.require_pool()
        migrations_dir = Path(__file__).parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))

        async with pool.acquire() as connection:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            for path in migration_files:
                already_applied = await connection.fetchval(
                    "SELECT 1 FROM schema_migrations WHERE filename = $1",
                    path.name,
                )
                if already_applied:
                    continue

                sql = path.read_text(encoding="utf-8")
                async with connection.transaction():
                    await connection.execute(sql)
                    await connection.execute(
                        "INSERT INTO schema_migrations(filename) VALUES($1)",
                        path.name,
                    )
                LOGGER.info("Migration appliquée : %s", path.name)
