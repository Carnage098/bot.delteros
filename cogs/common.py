from __future__ import annotations

import discord

from utils.errors import CeremonyError
from utils.respond import respond_ephemeral


async def handle_command_error(interaction: discord.Interaction, error: Exception) -> None:
    if isinstance(error, CeremonyError):
        await respond_ephemeral(interaction, f"⚠️ {error}")
        return
    await respond_ephemeral(interaction, "❌ Une erreur inattendue est survenue.")
    raise error


def require_guild_member(interaction: discord.Interaction) -> tuple[discord.Guild, discord.Member]:
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        raise CeremonyError("Cette commande doit être utilisée dans un serveur Discord.")
    return interaction.guild, interaction.user
