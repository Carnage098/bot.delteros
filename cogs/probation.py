from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.errors import CeremonyError
from utils.respond import respond_ephemeral
from .common import handle_command_error, require_guild_member

VERDICT_CHOICES = [
    app_commands.Choice(name="Positive", value="positive"),
    app_commands.Choice(name="Neutre", value="neutral"),
    app_commands.Choice(name="Négative", value="negative"),
]


class ProbationCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="evaluation", description="Ajoute une évaluation privée à une période d'épreuve.")
    @app_commands.choices(avis=VERDICT_CHOICES)
    async def evaluate(
        self,
        interaction: discord.Interaction,
        candidat: discord.Member,
        avis: app_commands.Choice[str],
        commentaire: app_commands.Range[str, 1, 1500],
    ) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            nomination = await self.bot.nomination_repository.get_active_for_candidate(guild.id, candidat.id)
            if nomination is None:
                raise CeremonyError("Ce membre ne possède aucune candidature active.")
            await self.bot.ceremony_service.add_evaluation(
                guild=guild,
                author=actor,
                nomination=nomination,
                verdict=avis.value,
                comment=commentaire,
            )
            await respond_ephemeral(interaction, "✅ Ton évaluation privée a été enregistrée.")
        except Exception as error:
            await handle_command_error(interaction, error)

    @app_commands.command(name="evaluations_consulter", description="Consulte les évaluations privées d'un candidat.")
    async def list_evaluations(self, interaction: discord.Interaction, candidat: discord.Member) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            await self.bot.permission_service.require_council(actor)
            nomination = await self.bot.nomination_repository.get_active_for_candidate(guild.id, candidat.id)
            if nomination is None:
                raise CeremonyError("Ce membre ne possède aucune candidature active.")
            rows = await self.bot.evaluation_repository.list_for_nomination(nomination.id)
            if not rows:
                await respond_ephemeral(interaction, "Aucune évaluation n'a encore été enregistrée.")
                return
            icons = {"positive": "✅", "neutral": "⚪", "negative": "❌"}
            lines = []
            for row in rows[:15]:
                lines.append(
                    f"{icons[row['verdict']]} <@{row['author_id']}> — "
                    f"{row['comment'][:350]}"
                )
            await respond_ephemeral(interaction, "\n\n".join(lines))
        except Exception as error:
            await handle_command_error(interaction, error)


async def setup(bot) -> None:
    await bot.add_cog(ProbationCog(bot))
