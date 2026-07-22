from __future__ import annotations

import discord

from models.enums import VoteChoice, VoteKind
from .base import PersistentCeremonyView


class CouncilVoteView(PersistentCeremonyView):
    def __init__(self, nomination_id: int, vote_kind: VoteKind) -> None:
        super().__init__()
        self.nomination_id = nomination_id
        self.vote_kind = vote_kind
        choices = (
            ("Approuver", "✅", discord.ButtonStyle.success, VoteChoice.APPROVE),
            ("Refuser", "❌", discord.ButtonStyle.danger, VoteChoice.REJECT),
            ("S’abstenir", "⚪", discord.ButtonStyle.secondary, VoteChoice.ABSTAIN),
        )
        for label, emoji, style, choice in choices:
            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=style,
                custom_id=f"heraut:vote:{vote_kind.value}:{choice.value}:{nomination_id}",
            )
            button.callback = self._callback_for(choice)  # type: ignore[method-assign]
            self.add_item(button)

    def _callback_for(self, choice: VoteChoice):
        async def callback(interaction: discord.Interaction) -> None:
            try:
                await interaction.response.defer(ephemeral=True)
                await interaction.client.ceremony_service.cast_vote(  # type: ignore[attr-defined]
                    interaction,
                    self.nomination_id,
                    self.vote_kind,
                    choice,
                )
                labels = {
                    VoteChoice.APPROVE: "favorable",
                    VoteChoice.REJECT: "défavorable",
                    VoteChoice.ABSTAIN: "abstention",
                }
                await interaction.followup.send(
                    f"Ton vote **{labels[choice]}** a été enregistré. Tu peux le modifier tant que le scrutin reste ouvert.",
                    ephemeral=True,
                )
            except Exception as error:
                await self.handle_error(interaction, error)
        return callback
