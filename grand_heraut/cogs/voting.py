from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from models.enums import NominationStatus, VoteKind
from utils.errors import CeremonyError
from utils.respond import respond_ephemeral
from .common import handle_command_error, require_guild_member


class VotingCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="vote_clore", description="Clôture le scrutin actif d'un candidat.")
    async def close_vote(self, interaction: discord.Interaction, candidat: discord.Member) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            nomination = await self.bot.nomination_repository.get_active_for_candidate(guild.id, candidat.id)
            if nomination is None:
                raise CeremonyError("Ce membre ne possède aucune candidature active.")
            if nomination.status is NominationStatus.NOMINATION_VOTE:
                vote_kind = VoteKind.NOMINATION
            elif nomination.status is NominationStatus.ADOUBEMENT_VOTE:
                vote_kind = VoteKind.ADOUBEMENT
            else:
                raise CeremonyError("Aucun scrutin n'est actuellement ouvert pour ce candidat.")

            summary = await self.bot.ceremony_service.close_vote(
                guild=guild,
                actor=actor,
                nomination=nomination,
                vote_kind=vote_kind,
            )
            if not summary.quorum_reached:
                message = "Le quorum n'est pas atteint : la décision du Fondateur est requise."
            elif summary.is_tie:
                message = "Le scrutin est à égalité : la voix prépondérante du Fondateur est requise."
            else:
                message = "Le scrutin a été clôturé et la décision a été appliquée."
            await respond_ephemeral(interaction, f"✅ {message}")
        except Exception as error:
            await handle_command_error(interaction, error)


async def setup(bot) -> None:
    await bot.add_cog(VotingCog(bot))
