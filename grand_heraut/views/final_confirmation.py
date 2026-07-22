from __future__ import annotations

import discord

from .base import PersistentCeremonyView


class FinalConfirmationView(PersistentCeremonyView):
    def __init__(self, nomination_id: int) -> None:
        super().__init__()
        self.nomination_id = nomination_id
        confirm = discord.ui.Button(
            label="Je confirme mon engagement",
            emoji="⚔️",
            style=discord.ButtonStyle.success,
            custom_id=f"heraut:final:confirm:{nomination_id}",
        )
        renounce = discord.ui.Button(
            label="Je renonce à ma fonction",
            emoji="🚪",
            style=discord.ButtonStyle.danger,
            custom_id=f"heraut:final:renounce:{nomination_id}",
        )
        confirm.callback = self.confirm  # type: ignore[method-assign]
        renounce.callback = self.renounce  # type: ignore[method-assign]
        self.add_item(confirm)
        self.add_item(renounce)

    async def confirm(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.client.ceremony_service.confirm_final_engagement(interaction, self.nomination_id)  # type: ignore[attr-defined]
            await interaction.followup.send("Ton engagement final a été confirmé.", ephemeral=True)
        except Exception as error:
            await self.handle_error(interaction, error)

    async def renounce(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.client.ceremony_service.candidate_renounce(  # type: ignore[attr-defined]
                interaction,
                self.nomination_id,
                remove_future_role=True,
            )
            await interaction.followup.send("Ta décision a été enregistrée.", ephemeral=True)
        except Exception as error:
            await self.handle_error(interaction, error)
