from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from constants.commandments import COMMANDMENTS
from embeds import ceremony as embeds
from models.enums import DecisionType, NominationStatus, Rank, VoteChoice, VoteKind
from models.records import GuildConfig, Nomination, VoteSummary
from repositories import (
    ConfigRepository,
    EvaluationRepository,
    LogRepository,
    NominationRepository,
    VoteRepository,
)
from services.permission_service import PermissionService
from services.role_service import RoleService
from services.voting_service import VotingService
from utils.errors import CeremonyError

if TYPE_CHECKING:
    from bot import HerautBot

LOGGER = logging.getLogger(__name__)


class CeremonyService:
    def __init__(
        self,
        bot: "HerautBot",
        config_repository: ConfigRepository,
        nomination_repository: NominationRepository,
        vote_repository: VoteRepository,
        evaluation_repository: EvaluationRepository,
        log_repository: LogRepository,
        permission_service: PermissionService,
        role_service: RoleService,
        voting_service: VotingService,
    ) -> None:
        self.bot = bot
        self.config_repository = config_repository
        self.nominations = nomination_repository
        self.votes = vote_repository
        self.evaluations = evaluation_repository
        self.logs = log_repository
        self.permissions = permission_service
        self.roles = role_service
        self.voting = voting_service

    async def get_member(self, guild: discord.Guild, member_id: int) -> discord.Member:
        member = guild.get_member(member_id)
        if member is not None:
            return member
        try:
            return await guild.fetch_member(member_id)
        except discord.NotFound as exc:
            raise CeremonyError("Le membre concerné n'est plus présent sur le serveur.") from exc

    async def ceremony_channel(self, guild: discord.Guild, config: GuildConfig):
        channel = guild.get_channel(config.ceremony_channel_id)
        if channel is None:
            try:
                channel = await guild.fetch_channel(config.ceremony_channel_id)
            except discord.HTTPException as exc:
                raise CeremonyError("Le salon de cérémonie configuré est introuvable.") from exc
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            raise CeremonyError("Le salon de cérémonie doit être un salon textuel ou un fil.")
        return channel

    async def log_event(
        self,
        *,
        guild: discord.Guild,
        event_type: str,
        nomination: Nomination | None = None,
        actor_id: int | None = None,
        details: dict | None = None,
    ) -> None:
        await self.logs.add(
            guild_id=guild.id,
            event_type=event_type,
            nomination_id=nomination.id if nomination else None,
            actor_id=actor_id,
            details=details,
        )
        config = await self.config_repository.get(guild.id)
        if config is None or config.log_channel_id is None:
            return
        channel = guild.get_channel(config.log_channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        description = f"**Événement :** `{event_type}`"
        if nomination:
            description += f"\n**Candidature :** `{nomination.id}`\n**Candidat :** <@{nomination.candidate_id}>"
        if actor_id:
            description += f"\n**Auteur :** <@{actor_id}>"
        if details:
            rendered = "\n".join(f"• **{key}** : {value}" for key, value in details.items())
            description += f"\n\n{rendered[:2500]}"
        try:
            await channel.send(embed=discord.Embed(title="📚 Journal du Grand Héraut", description=description))
        except discord.HTTPException:
            LOGGER.exception("Impossible d'envoyer le journal Discord.")

    async def create_nomination(
        self,
        *,
        guild: discord.Guild,
        candidate: discord.Member,
        nominator: discord.Member,
        rank: Rank,
        reason: str | None,
    ) -> Nomination:
        config = await self.permissions.require_council(nominator)
        if candidate.bot:
            raise CeremonyError("Un bot ne peut pas être candidat.")
        if candidate.id == nominator.id:
            raise CeremonyError("Tu ne peux pas te nommer toi-même.")
        if await self.nominations.get_active_for_candidate(guild.id, candidate.id):
            raise CeremonyError("Ce membre possède déjà une candidature active.")

        final_role = self.roles.get_role(guild, config, rank, future=False)
        future_role = self.roles.get_role(guild, config, rank, future=True)
        if final_role in candidate.roles:
            raise CeremonyError(f"Ce membre possède déjà le rôle **{rank.label}**.")
        if future_role in candidate.roles:
            raise CeremonyError(f"Ce membre possède déjà le rôle **{rank.future_label}**.")

        channel = await self.ceremony_channel(guild, config)
        nomination = await self.nominations.create(
            guild_id=guild.id,
            candidate_id=candidate.id,
            nominated_by_id=nominator.id,
            rank=rank,
            reason=reason,
            ceremony_channel_id=channel.id,
        )
        from views.invitation import NominationInvitationView

        message = await channel.send(
            content=candidate.mention,
            embed=embeds.nomination_invitation(candidate, nominator, rank, reason),
            view=NominationInvitationView(nomination.id),
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
        await self.nominations.set_message_ids(nomination.id, ceremony_message_id=message.id)
        await self.log_event(
            guild=guild,
            event_type="nomination_created",
            nomination=nomination,
            actor_id=nominator.id,
            details={"rank": rank.value, "reason": reason or "Aucun"},
        )
        return nomination

    async def candidate_accept_invitation(self, interaction: discord.Interaction, nomination_id: int) -> None:
        guild, member, nomination = await self._candidate_context(interaction, nomination_id)
        if nomination.status is not NominationStatus.CONVOCATION:
            raise CeremonyError("Cette convocation n'est plus active.")
        await self.nominations.set_status(nomination.id, NominationStatus.COMMANDMENTS)
        if interaction.message:
            await interaction.message.edit(view=None)
        channel = interaction.channel
        if channel is None:
            raise CeremonyError("Le salon de la cérémonie est introuvable.")
        from views.commandments import CommandmentsView

        message = await channel.send(
            content=member.mention,
            embed=embeds.commandment(1),
            view=CommandmentsView(nomination.id),
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
        await self.nominations.set_message_ids(nomination.id, ceremony_message_id=message.id)
        await self.log_event(
            guild=guild,
            event_type="candidate_entered",
            nomination=nomination,
            actor_id=member.id,
        )

    async def candidate_renounce(
        self,
        interaction: discord.Interaction,
        nomination_id: int,
        *,
        remove_future_role: bool = False,
    ) -> None:
        guild, member, nomination = await self._candidate_context(interaction, nomination_id)
        if remove_future_role:
            config = await self.permissions.require_config(guild.id)
            await self.roles.remove_future_role(member, config, nomination.rank)
        await self.nominations.set_status(nomination.id, NominationStatus.RENOUNCED, close=True)
        if interaction.message:
            await interaction.message.edit(view=None)
        if interaction.channel:
            await interaction.channel.send(
                embed=discord.Embed(
                    title="🚪 Le candidat renonce à la cérémonie",
                    description=(
                        f"{member.mention} a choisi de ne pas poursuivre sa candidature. "
                        "La procédure est désormais close."
                    ),
                    color=0xED4245,
                )
            )
        await self.log_event(
            guild=guild,
            event_type="candidate_renounced",
            nomination=nomination,
            actor_id=member.id,
        )

    async def accept_next_commandment(self, interaction: discord.Interaction, nomination_id: int) -> None:
        guild, member, nomination = await self._candidate_context(interaction, nomination_id)
        if nomination.status is not NominationStatus.COMMANDMENTS:
            raise CeremonyError("La lecture des commandements n'est pas active.")
        number = nomination.current_commandment + 1
        if not 1 <= number <= len(COMMANDMENTS):
            raise CeremonyError("La progression des commandements est incohérente.")
        await self.nominations.accept_commandment(nomination.id, number)
        if interaction.message:
            await interaction.message.edit(view=None)
        await self.log_event(
            guild=guild,
            event_type="commandment_accepted",
            nomination=nomination,
            actor_id=member.id,
            details={"number": number},
        )

        if number == len(COMMANDMENTS):
            await self.nominations.set_status(nomination.id, NominationStatus.OATH)
            from views.oath import OathView

            message = await interaction.channel.send(
                content=member.mention,
                embed=embeds.oath(member),
                view=OathView(nomination.id),
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
        else:
            from views.commandments import CommandmentsView

            message = await interaction.channel.send(
                content=member.mention,
                embed=embeds.commandment(number + 1),
                view=CommandmentsView(nomination.id),
                allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
            )
        await self.nominations.set_message_ids(nomination.id, ceremony_message_id=message.id)

    async def refuse_commandment(self, interaction: discord.Interaction, nomination_id: int) -> None:
        guild, member, nomination = await self._candidate_context(interaction, nomination_id)
        if nomination.status is not NominationStatus.COMMANDMENTS:
            raise CeremonyError("La lecture des commandements n'est pas active.")
        refused_number = nomination.current_commandment + 1
        await self.nominations.set_status(nomination.id, NominationStatus.SUSPENDED)
        if interaction.message:
            await interaction.message.edit(view=None)
        if interaction.channel:
            await interaction.channel.send(
                embed=discord.Embed(
                    title="⚠️ La cérémonie est suspendue",
                    description=(
                        f"{member.mention} n’a pas accepté le commandement n°{refused_number}.\n\n"
                        "Le Conseil pourra discuter avec le candidat, reprendre la cérémonie "
                        "ou l’annuler."
                    ),
                    color=0xFEE75C,
                )
            )
        await self.log_event(
            guild=guild,
            event_type="commandment_refused",
            nomination=nomination,
            actor_id=member.id,
            details={"number": refused_number},
        )

    async def resume_nomination(self, guild: discord.Guild, actor: discord.Member, nomination: Nomination) -> None:
        await self.permissions.require_council(actor)
        if nomination.status is not NominationStatus.SUSPENDED:
            raise CeremonyError("Cette cérémonie n'est pas suspendue.")
        candidate = await self.get_member(guild, nomination.candidate_id)
        await self.nominations.set_status(nomination.id, NominationStatus.COMMANDMENTS)
        channel = await self.ceremony_channel(guild, await self.permissions.require_config(guild.id))
        from views.commandments import CommandmentsView

        message = await channel.send(
            content=candidate.mention,
            embed=embeds.commandment(nomination.current_commandment + 1),
            view=CommandmentsView(nomination.id),
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
        await self.nominations.set_message_ids(nomination.id, ceremony_message_id=message.id)
        await self.log_event(
            guild=guild,
            event_type="ceremony_resumed",
            nomination=nomination,
            actor_id=actor.id,
        )

    async def accept_oath(self, interaction: discord.Interaction, nomination_id: int) -> None:
        guild, member, nomination = await self._candidate_context(interaction, nomination_id)
        if nomination.status is not NominationStatus.OATH:
            raise CeremonyError("Le serment n'est pas actuellement attendu.")
        if interaction.message:
            await interaction.message.edit(view=None)
        await self.open_vote(guild, nomination, VoteKind.NOMINATION, channel=interaction.channel)
        await self.log_event(
            guild=guild,
            event_type="oath_accepted",
            nomination=nomination,
            actor_id=member.id,
        )

    async def open_vote(
        self,
        guild: discord.Guild,
        nomination: Nomination,
        vote_kind: VoteKind,
        *,
        channel=None,
    ) -> None:
        config = await self.permissions.require_config(guild.id)
        candidate = await self.get_member(guild, nomination.candidate_id)
        channel = channel or await self.ceremony_channel(guild, config)
        await self.nominations.clear_votes_and_open(nomination.id, vote_kind.value)
        from views.council_vote import CouncilVoteView

        message = await channel.send(
            embed=embeds.vote_open(candidate, nomination.rank, vote_kind),
            view=CouncilVoteView(nomination.id, vote_kind),
        )
        await self.nominations.set_message_ids(nomination.id, vote_message_id=message.id)

    async def cast_vote(
        self,
        interaction: discord.Interaction,
        nomination_id: int,
        vote_kind: VoteKind,
        choice: VoteChoice,
    ) -> None:
        guild = self._require_guild(interaction)
        voter = self._require_member(interaction)
        nomination = await self._require_nomination(nomination_id, guild.id)
        await self.permissions.require_council(voter)
        if voter.id == nomination.candidate_id:
            raise CeremonyError("Un candidat ne peut pas voter sur sa propre candidature.")
        expected = (
            NominationStatus.NOMINATION_VOTE
            if vote_kind is VoteKind.NOMINATION
            else NominationStatus.ADOUBEMENT_VOTE
        )
        if nomination.status is not expected:
            raise CeremonyError("Ce scrutin n'est plus ouvert.")
        await self.votes.upsert(nomination.id, vote_kind, voter.id, choice)
        await self.log_event(
            guild=guild,
            event_type="vote_recorded",
            nomination=nomination,
            actor_id=voter.id,
            details={"vote_kind": vote_kind.value, "choice": choice.value},
        )

    async def close_vote(
        self,
        *,
        guild: discord.Guild,
        actor: discord.Member,
        nomination: Nomination,
        vote_kind: VoteKind,
        channel=None,
    ) -> VoteSummary:
        config = await self.permissions.require_council(actor)
        expected = (
            NominationStatus.NOMINATION_VOTE
            if vote_kind is VoteKind.NOMINATION
            else NominationStatus.ADOUBEMENT_VOTE
        )
        if nomination.status is not expected:
            raise CeremonyError("Ce scrutin n'est pas ouvert.")
        summary = await self.voting.summarize(nomination.id, vote_kind, guild, config)
        candidate = await self.get_member(guild, nomination.candidate_id)
        channel = channel or await self.ceremony_channel(guild, config)
        await self._disable_message_view(channel, nomination.vote_message_id)

        if not summary.quorum_reached:
            await self._request_founder_decision(
                guild, nomination, candidate, vote_kind, "no_quorum", channel
            )
            return summary
        if summary.is_tie:
            await self._request_founder_decision(
                guild, nomination, candidate, vote_kind, "tie", channel
            )
            return summary

        accepted = summary.accepted
        if accepted:
            await self._accept_decision(
                guild,
                nomination,
                candidate,
                config,
                vote_kind,
                DecisionType.COUNCIL_MAJORITY,
                actor.id,
                summary,
                channel,
            )
        else:
            await self._reject_decision(
                guild,
                nomination,
                candidate,
                config,
                vote_kind,
                DecisionType.COUNCIL_MAJORITY,
                actor.id,
                summary,
                channel,
            )
        return summary

    async def _request_founder_decision(
        self,
        guild: discord.Guild,
        nomination: Nomination,
        candidate: discord.Member,
        vote_kind: VoteKind,
        reason: str,
        channel,
    ) -> None:
        await self.nominations.wait_for_founder(nomination.id, vote_kind.value, reason)
        from views.founder_decision import FounderDecisionView

        message = await channel.send(
            content=f"<@{(await self.permissions.require_config(guild.id)).founder_id}>",
            embed=embeds.founder_required(candidate, reason),
            view=FounderDecisionView(nomination.id),
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
        await self.nominations.set_message_ids(nomination.id, vote_message_id=message.id)
        await self.log_event(
            guild=guild,
            event_type="founder_decision_required",
            nomination=nomination,
            details={"vote_kind": vote_kind.value, "reason": reason},
        )

    async def founder_decision(
        self,
        interaction: discord.Interaction,
        nomination_id: int,
        accepted: bool,
    ) -> None:
        guild = self._require_guild(interaction)
        founder = self._require_member(interaction)
        config = await self.permissions.require_founder(founder)
        nomination = await self._require_nomination(nomination_id, guild.id)
        if nomination.status is not NominationStatus.WAITING_FOUNDER:
            raise CeremonyError("La décision du Fondateur n'est pas requise pour cette candidature.")
        if not nomination.pending_vote_kind or not nomination.pending_founder_reason:
            raise CeremonyError("Les informations du vote en attente sont incomplètes.")
        vote_kind = VoteKind(nomination.pending_vote_kind)
        summary = await self.voting.summarize(nomination.id, vote_kind, guild, config)
        candidate = await self.get_member(guild, nomination.candidate_id)
        decision_type = (
            DecisionType.FOUNDER_TIEBREAK
            if nomination.pending_founder_reason == "tie"
            else DecisionType.FOUNDER_NO_QUORUM
        )
        if interaction.message:
            await interaction.message.edit(view=None)
        if accepted:
            await self._accept_decision(
                guild,
                nomination,
                candidate,
                config,
                vote_kind,
                decision_type,
                founder.id,
                summary,
                interaction.channel,
            )
        else:
            await self._reject_decision(
                guild,
                nomination,
                candidate,
                config,
                vote_kind,
                decision_type,
                founder.id,
                summary,
                interaction.channel,
            )

    async def _accept_decision(
        self,
        guild: discord.Guild,
        nomination: Nomination,
        candidate: discord.Member,
        config: GuildConfig,
        vote_kind: VoteKind,
        decision_type: DecisionType,
        actor_id: int | None,
        summary: VoteSummary,
        channel,
    ) -> None:
        if vote_kind is VoteKind.NOMINATION:
            await self.roles.assign_future_role(candidate, config, nomination.rank)
            await self.nominations.start_probation(nomination.id, decision_type, actor_id)
            await channel.send(embed=embeds.vote_result(candidate, nomination.rank, summary, True, vote_kind))
            await channel.send(embed=embeds.probation_started(candidate, nomination.rank))
            event = "probation_started"
        else:
            await self.roles.promote(candidate, config, nomination.rank)
            await self.nominations.mark_promoted(nomination.id, decision_type, actor_id)
            await channel.send(embed=embeds.vote_result(candidate, nomination.rank, summary, True, vote_kind))
            await channel.send(embed=embeds.promoted(candidate, nomination.rank))
            event = "candidate_promoted"
        await self.log_event(
            guild=guild,
            event_type=event,
            nomination=nomination,
            actor_id=actor_id,
            details={"decision_type": decision_type.value},
        )

    async def _reject_decision(
        self,
        guild: discord.Guild,
        nomination: Nomination,
        candidate: discord.Member,
        config: GuildConfig,
        vote_kind: VoteKind,
        decision_type: DecisionType,
        actor_id: int | None,
        summary: VoteSummary,
        channel,
    ) -> None:
        if vote_kind is VoteKind.ADOUBEMENT:
            await self.roles.remove_future_role(candidate, config, nomination.rank)
        await self.nominations.set_status(nomination.id, NominationStatus.REJECTED, close=True)
        await channel.send(embed=embeds.vote_result(candidate, nomination.rank, summary, False, vote_kind))
        await self.log_event(
            guild=guild,
            event_type="candidate_rejected",
            nomination=nomination,
            actor_id=actor_id,
            details={"decision_type": decision_type.value, "vote_kind": vote_kind.value},
        )

    async def start_adoubement(
        self,
        *,
        guild: discord.Guild,
        actor: discord.Member,
        nomination: Nomination,
    ) -> None:
        config = await self.permissions.require_council(actor)
        if nomination.status is not NominationStatus.PROBATION:
            raise CeremonyError("Ce candidat n'est pas actuellement en période d'épreuve.")
        candidate = await self.get_member(guild, nomination.candidate_id)
        future_role = self.roles.get_role(guild, config, nomination.rank, future=True)
        if future_role not in candidate.roles:
            raise CeremonyError("Le candidat ne possède plus son rôle provisoire.")
        await self.nominations.set_final_confirmation(nomination.id)
        channel = await self.ceremony_channel(guild, config)
        from views.final_confirmation import FinalConfirmationView

        message = await channel.send(
            content=candidate.mention,
            embed=embeds.final_confirmation(candidate, nomination.rank),
            view=FinalConfirmationView(nomination.id),
            allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False),
        )
        await self.nominations.set_message_ids(nomination.id, ceremony_message_id=message.id)
        await self.log_event(
            guild=guild,
            event_type="adoubement_started",
            nomination=nomination,
            actor_id=actor.id,
        )

    async def confirm_final_engagement(self, interaction: discord.Interaction, nomination_id: int) -> None:
        guild, member, nomination = await self._candidate_context(interaction, nomination_id)
        if nomination.status is not NominationStatus.FINAL_CONFIRMATION:
            raise CeremonyError("Cette confirmation finale n'est plus active.")
        if interaction.message:
            await interaction.message.edit(view=None)
        await self.open_vote(guild, nomination, VoteKind.ADOUBEMENT, channel=interaction.channel)
        await self.log_event(
            guild=guild,
            event_type="final_engagement_confirmed",
            nomination=nomination,
            actor_id=member.id,
        )

    async def add_evaluation(
        self,
        *,
        guild: discord.Guild,
        author: discord.Member,
        nomination: Nomination,
        verdict: str,
        comment: str,
    ) -> None:
        await self.permissions.require_council(author)
        if nomination.status is not NominationStatus.PROBATION:
            raise CeremonyError("Les évaluations sont réservées aux périodes d'épreuve actives.")
        await self.evaluations.create(nomination.id, author.id, verdict, comment)
        await self.log_event(
            guild=guild,
            event_type="evaluation_added",
            nomination=nomination,
            actor_id=author.id,
            details={"verdict": verdict, "comment": comment[:500]},
        )

    async def cancel_nomination(
        self,
        *,
        guild: discord.Guild,
        actor: discord.Member,
        nomination: Nomination,
        reason: str,
    ) -> None:
        config = await self.permissions.require_council(actor)
        if nomination.status in {
            NominationStatus.PROMOTED,
            NominationStatus.REJECTED,
            NominationStatus.CANCELLED,
            NominationStatus.RENOUNCED,
        }:
            raise CeremonyError("Cette candidature est déjà close.")
        candidate = await self.get_member(guild, nomination.candidate_id)
        if nomination.status in {
            NominationStatus.PROBATION,
            NominationStatus.FINAL_CONFIRMATION,
            NominationStatus.ADOUBEMENT_VOTE,
            NominationStatus.WAITING_FOUNDER,
        }:
            future_role = self.roles.get_role(guild, config, nomination.rank, future=True)
            if future_role in candidate.roles:
                await self.roles.remove_future_role(candidate, config, nomination.rank)
        await self.nominations.set_status(nomination.id, NominationStatus.CANCELLED, close=True)
        channel = await self.ceremony_channel(guild, config)
        await channel.send(
            embed=discord.Embed(
                title="❌ Cérémonie annulée par le Conseil",
                description=f"La candidature de {candidate.mention} est close.\n\n**Motif :** {reason}",
                color=0xED4245,
            )
        )
        await self.log_event(
            guild=guild,
            event_type="nomination_cancelled",
            nomination=nomination,
            actor_id=actor.id,
            details={"reason": reason},
        )

    @staticmethod
    async def _disable_message_view(channel, message_id: int | None) -> None:
        if message_id is None or not hasattr(channel, "fetch_message"):
            return
        try:
            message = await channel.fetch_message(message_id)
            await message.edit(view=None)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            LOGGER.warning("Impossible de désactiver les anciens boutons du scrutin %s.", message_id)

    async def _candidate_context(
        self,
        interaction: discord.Interaction,
        nomination_id: int,
    ) -> tuple[discord.Guild, discord.Member, Nomination]:
        guild = self._require_guild(interaction)
        member = self._require_member(interaction)
        nomination = await self._require_nomination(nomination_id, guild.id)
        if member.id != nomination.candidate_id:
            raise CeremonyError("Seul le candidat concerné peut utiliser ce bouton.")
        return guild, member, nomination

    @staticmethod
    def _require_guild(interaction: discord.Interaction) -> discord.Guild:
        if interaction.guild is None:
            raise CeremonyError("Cette action doit être effectuée dans un serveur Discord.")
        return interaction.guild

    @staticmethod
    def _require_member(interaction: discord.Interaction) -> discord.Member:
        if not isinstance(interaction.user, discord.Member):
            raise CeremonyError("Impossible d'identifier ton rôle sur ce serveur.")
        return interaction.user

    async def _require_nomination(self, nomination_id: int, guild_id: int) -> Nomination:
        nomination = await self.nominations.get(nomination_id)
        if nomination is None or nomination.guild_id != guild_id:
            raise CeremonyError("Cette candidature est introuvable.")
        return nomination
