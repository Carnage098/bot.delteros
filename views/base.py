from __future__ import annotations

import logging

import discord

from utils.errors import CeremonyError
from utils.respond import respond_ephemeral

LOGGER = logging.getLogger(__name__)


class PersistentCeremonyView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    async def handle_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if isinstance(error, CeremonyError):
            await respond_ephemeral(interaction, f"⚠️ {error}")
            return
        LOGGER.error(
            "Erreur dans un bouton de cérémonie",
            exc_info=(type(error), error, error.__traceback__),
        )
        await respond_ephemeral(interaction, "❌ Une erreur inattendue est survenue.")
