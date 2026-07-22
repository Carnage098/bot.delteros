from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from models.enums import Rank
from utils.errors import CeremonyError
from utils.respond import respond_ephemeral
from .common import handle_command_error, require_guild_member

RANK_CHOICES = [
    app_commands.Choice(name="Futur Staff", value=Rank.STAFF.value),
    app_commands.Choice(name="Futur Modérateur", value=Rank.MODERATOR.value),
    app_commands.Choice(name="Futur Administrateur", value=Rank.ADMINISTRATOR.value),
]


class NominationCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="nomination", description="Ouvre une cérémonie de nomination.")
    @app_commands.choices(rang=RANK_CHOICES)
    async def nominate(
        self,
        interaction: discord.Interaction,
        candidat: discord.Member,
        rang: app_commands.Choice[str],
        raison: app_commands.Range[str, 1, 1000] | None = None,
    ) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            nomination = await self.bot.ceremony_service.create_nomination(
                guild=guild,
                candidate=candidat,
                nominator=actor,
                rank=Rank(rang.value),
                reason=raison,
            )
            await respond_ephemeral(
                interaction,
                f"✅ La cérémonie n°**{nomination.id}** a été ouverte dans le salon configuré.",
            )
        except Exception as error:
            await handle_command_error(interaction, error)

    @app_commands.command(name="nomination_annuler", description="Annule une candidature active.")
    async def cancel(
        self,
        interaction: discord.Interaction,
        candidat: discord.Member,
        raison: app_commands.Range[str, 1, 1000],
    ) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            nomination = await self.bot.nomination_repository.get_active_for_candidate(guild.id, candidat.id)
            if nomination is None:
                raise CeremonyError("Ce membre ne possède aucune candidature active.")
            await self.bot.ceremony_service.cancel_nomination(
                guild=guild,
                actor=actor,
                nomination=nomination,
                reason=raison,
            )
            await respond_ephemeral(interaction, "✅ La candidature a été annulée.")
        except Exception as error:
            await handle_command_error(interaction, error)

    @app_commands.command(name="nomination_reprendre", description="Reprend une cérémonie suspendue.")
    async def resume(self, interaction: discord.Interaction, candidat: discord.Member) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            nomination = await self.bot.nomination_repository.get_active_for_candidate(guild.id, candidat.id)
            if nomination is None:
                raise CeremonyError("Ce membre ne possède aucune candidature active.")
            await self.bot.ceremony_service.resume_nomination(guild, actor, nomination)
            await respond_ephemeral(interaction, "✅ La lecture des commandements reprend.")
        except Exception as error:
            await handle_command_error(interaction, error)


async def setup(bot) -> None:
    await bot.add_cog(NominationCog(bot))
