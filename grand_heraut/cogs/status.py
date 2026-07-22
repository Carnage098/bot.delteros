from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from embeds.ceremony import status_embed
from utils.errors import CeremonyError
from utils.respond import respond_ephemeral
from .common import handle_command_error, require_guild_member


class StatusCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="nomination_statut", description="Affiche l'état actuel d'une candidature.")
    async def status(self, interaction: discord.Interaction, candidat: discord.Member) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            await self.bot.permission_service.require_council(actor)
            nomination = await self.bot.nomination_repository.get_active_for_candidate(guild.id, candidat.id)
            if nomination is None:
                raise CeremonyError("Ce membre ne possède aucune candidature active.")
            if interaction.response.is_done():
                await interaction.followup.send(embed=status_embed(nomination, candidat), ephemeral=True)
            else:
                await interaction.response.send_message(embed=status_embed(nomination, candidat), ephemeral=True)
        except Exception as error:
            await handle_command_error(interaction, error)

    @app_commands.command(name="candidatures_actives", description="Liste toutes les candidatures actives.")
    async def active(self, interaction: discord.Interaction) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            await self.bot.permission_service.require_council(actor)
            nominations = await self.bot.nomination_repository.list_active(guild.id)
            if not nominations:
                await respond_ephemeral(interaction, "Aucune candidature n'est actuellement active.")
                return
            lines = [
                f"• **#{item.id}** — <@{item.candidate_id}> — {item.rank.label} — {item.status.label}"
                for item in nominations
            ]
            await respond_ephemeral(interaction, "\n".join(lines))
        except Exception as error:
            await handle_command_error(interaction, error)

    @app_commands.command(name="historique_nominations", description="Affiche les dernières cérémonies du serveur.")
    async def history(self, interaction: discord.Interaction) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            await self.bot.permission_service.require_council(actor)
            nominations = await self.bot.nomination_repository.list_history(guild.id, 20)
            if not nominations:
                await respond_ephemeral(interaction, "Aucune cérémonie n'a encore été enregistrée.")
                return
            lines = [
                f"• **#{item.id}** — <@{item.candidate_id}> — {item.rank.label} — {item.status.label}"
                for item in nominations
            ]
            await respond_ephemeral(interaction, "\n".join(lines))
        except Exception as error:
            await handle_command_error(interaction, error)


async def setup(bot) -> None:
    await bot.add_cog(StatusCog(bot))
