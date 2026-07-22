from __future__ import annotations

import discord

from .base import PersistentCeremonyView


class FounderDecisionView(PersistentCeremonyView):
    def __init__(self, nomination_id: int) -> None:
        super().__init__()
        self.nomination_id = nomination_id
        accept = discord.ui.Button(
            label="Accepter définitivement",
            emoji="👑",
            style=discord.ButtonStyle.success,
            custom_id=f"heraut:founder:accept:{nomination_id}",
        )
        refuse = discord.ui.Button(
            label="Refuser définitivement",
            emoji="⚖️",
            style=discord.ButtonStyle.danger,
            custom_id=f"heraut:founder:refuse:{nomination_id}",
        )
        accept.callback = self.accept  # type: ignore[method-assign]
        refuse.callback = self.refuse  # type: ignore[method-assign]
        self.add_item(accept)
        self.add_item(refuse)

    async def accept(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.client.ceremony_service.founder_decision(interaction, self.nomination_id, True)  # type: ignore[attr-defined]
            await interaction.followup.send("Ta décision a été appliquée.", ephemeral=True)
        except Exception as error:
            await self.handle_error(interaction, error)

    async def refuse(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.client.ceremony_service.founder_decision(interaction, self.nomination_id, False)  # type: ignore[attr-defined]
            await interaction.followup.send("Ta décision a été appliquée.", ephemeral=True)
        except Exception as error:
            await self.handle_error(interaction, error)
