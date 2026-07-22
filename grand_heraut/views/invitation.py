from __future__ import annotations

import discord

from .base import PersistentCeremonyView
from utils.respond import respond_ephemeral


class NominationInvitationView(PersistentCeremonyView):
    def __init__(self, nomination_id: int) -> None:
        super().__init__()
        self.nomination_id = nomination_id

        accept = discord.ui.Button(
            label="Je m’avance devant le Conseil",
            emoji="⚔️",
            style=discord.ButtonStyle.success,
            custom_id=f"heraut:invite:accept:{nomination_id}",
        )
        refuse = discord.ui.Button(
            label="Je refuse la nomination",
            emoji="🚪",
            style=discord.ButtonStyle.danger,
            custom_id=f"heraut:invite:refuse:{nomination_id}",
        )
        accept.callback = self.accept  # type: ignore[method-assign]
        refuse.callback = self.refuse  # type: ignore[method-assign]
        self.add_item(accept)
        self.add_item(refuse)

    async def accept(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.client.ceremony_service.candidate_accept_invitation(interaction, self.nomination_id)  # type: ignore[attr-defined]
            await interaction.followup.send("Tu t’es avancé devant le Conseil.", ephemeral=True)
        except Exception as error:
            await self.handle_error(interaction, error)

    async def refuse(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.client.ceremony_service.candidate_renounce(interaction, self.nomination_id)  # type: ignore[attr-defined]
            await interaction.followup.send("Ta décision a été enregistrée.", ephemeral=True)
        except Exception as error:
            await self.handle_error(interaction, error)
