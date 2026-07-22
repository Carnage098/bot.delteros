from __future__ import annotations

import discord

from models.enums import Rank
from models.records import GuildConfig
from utils.errors import CeremonyError


class RoleService:
    @staticmethod
    def _role_id(config: GuildConfig, rank: Rank, future: bool) -> int:
        if future:
            return {
                Rank.STAFF: config.future_staff_role_id,
                Rank.MODERATOR: config.future_moderator_role_id,
                Rank.ADMINISTRATOR: config.future_admin_role_id,
            }[rank]
        return {
            Rank.STAFF: config.staff_role_id,
            Rank.MODERATOR: config.moderator_role_id,
            Rank.ADMINISTRATOR: config.admin_role_id,
        }[rank]

    @classmethod
    def get_role(
        cls,
        guild: discord.Guild,
        config: GuildConfig,
        rank: Rank,
        *,
        future: bool,
    ) -> discord.Role:
        role_id = cls._role_id(config, rank, future)
        role = guild.get_role(role_id)
        if role is None:
            raise CeremonyError(
                f"Le rôle Discord configuré pour **{'Futur ' if future else ''}{rank.label}** "
                "n'existe plus."
            )
        return role

    @staticmethod
    def ensure_manageable(guild: discord.Guild, role: discord.Role) -> None:
        me = guild.me
        if me is None:
            raise CeremonyError("Le bot n'est pas reconnu comme membre du serveur.")
        if not me.guild_permissions.manage_roles:
            raise CeremonyError("Le bot doit posséder la permission **Gérer les rôles**.")
        if role >= me.top_role:
            raise CeremonyError(
                f"Le rôle **{role.name}** doit être placé sous le rôle principal du bot."
            )

    async def assign_future_role(
        self,
        member: discord.Member,
        config: GuildConfig,
        rank: Rank,
    ) -> None:
        role = self.get_role(member.guild, config, rank, future=True)
        self.ensure_manageable(member.guild, role)
        if role not in member.roles:
            await member.add_roles(role, reason="Nomination provisoire par Le Grand Héraut")

    async def remove_future_role(
        self,
        member: discord.Member,
        config: GuildConfig,
        rank: Rank,
    ) -> None:
        role = self.get_role(member.guild, config, rank, future=True)
        self.ensure_manageable(member.guild, role)
        if role in member.roles:
            await member.remove_roles(role, reason="Clôture de la période d'épreuve")

    async def promote(
        self,
        member: discord.Member,
        config: GuildConfig,
        rank: Rank,
    ) -> None:
        future_role = self.get_role(member.guild, config, rank, future=True)
        final_role = self.get_role(member.guild, config, rank, future=False)
        self.ensure_manageable(member.guild, future_role)
        self.ensure_manageable(member.guild, final_role)
        await member.add_roles(final_role, reason="Adoubement officiel par Le Grand Héraut")
        if future_role in member.roles:
            await member.remove_roles(future_role, reason="Adoubement officiel terminé")
