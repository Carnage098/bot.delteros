from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.errors import CeremonyError
from utils.respond import respond_ephemeral
from .common import handle_command_error, require_guild_member


class AdoubementCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="adoubement", description="Ouvre l'examen final d'un candidat en période d'épreuve.")
    async def start(self, interaction: discord.Interaction, candidat: discord.Member) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            nomination = await self.bot.nomination_repository.get_active_for_candidate(guild.id, candidat.id)
            if nomination is None:
                raise CeremonyError("Ce membre ne possède aucune candidature active.")
            await self.bot.ceremony_service.start_adoubement(
                guild=guild,
                actor=actor,
                nomination=nomination,
            )
            await respond_ephemeral(interaction, "✅ La confirmation finale du candidat a été demandée.")
        except Exception as error:
            await handle_command_error(interaction, error)


async def setup(bot) -> None:
    await bot.add_cog(AdoubementCog(bot))
