from __future__ import annotations

import math

import discord

from models.records import GuildConfig
from repositories.config_repository import ConfigRepository
from utils.errors import CeremonyError


class PermissionService:
    def __init__(self, config_repository: ConfigRepository) -> None:
        self.config_repository = config_repository

    async def require_config(self, guild_id: int) -> GuildConfig:
        config = await self.config_repository.get(guild_id)
        if config is None:
            raise CeremonyError(
                "Le bot n'est pas encore configuré. Le propriétaire doit utiliser "
                "`/ceremonie_configurer`."
            )
        return config

    async def is_founder(self, member: discord.Member, config: GuildConfig | None = None) -> bool:
        config = config or await self.require_config(member.guild.id)
        return member.id == config.founder_id

    async def is_council_member(
        self,
        member: discord.Member,
        config: GuildConfig | None = None,
    ) -> bool:
        config = config or await self.require_config(member.guild.id)
        if member.id == config.founder_id:
            return True
        role_ids = {role.id for role in member.roles}
        council_roles = {
            config.admin_role_id,
            config.staff_role_id,
            config.moderator_role_id,
        }
        return bool(role_ids & council_roles)

    async def require_council(self, member: discord.Member) -> GuildConfig:
        config = await self.require_config(member.guild.id)
        if not await self.is_council_member(member, config):
            raise CeremonyError("Cette action est réservée aux membres du Conseil.")
        return config

    async def require_founder(self, member: discord.Member) -> GuildConfig:
        config = await self.require_config(member.guild.id)
        if member.id != config.founder_id:
            raise CeremonyError("Cette décision appartient uniquement au Fondateur.")
        return config

    async def eligible_council_ids(
        self,
        guild: discord.Guild,
        config: GuildConfig | None = None,
    ) -> set[int]:
        config = config or await self.require_config(guild.id)
        if not guild.chunked:
            try:
                await guild.chunk(cache=True)
            except discord.HTTPException:
                pass

        role_ids = {
            config.admin_role_id,
            config.staff_role_id,
            config.moderator_role_id,
        }
        eligible = {config.founder_id}
        for member in guild.members:
            if member.bot:
                continue
            if any(role.id in role_ids for role in member.roles):
                eligible.add(member.id)
        return eligible

    @staticmethod
    def required_quorum(eligible_count: int, percentage: int) -> int:
        if eligible_count <= 0:
            return 1
        return max(1, math.ceil(eligible_count * percentage / 100))
