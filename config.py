from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
    discord_token: str
    database_url: str
    guild_id: int | None
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN", "").strip()
        database_url = os.getenv("DATABASE_URL", "").strip()
        guild_raw = os.getenv("GUILD_ID", "").strip()

        if not token:
            raise RuntimeError("La variable DISCORD_TOKEN est obligatoire.")
        if not database_url:
            raise RuntimeError("La variable DATABASE_URL est obligatoire.")

        guild_id = int(guild_raw) if guild_raw else None
        return cls(
            discord_token=token,
            database_url=database_url,
            guild_id=guild_id,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
