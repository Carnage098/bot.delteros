from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .enums import DecisionType, NominationStatus, Rank


@dataclass(slots=True)
class GuildConfig:
    guild_id: int
    founder_id: int
    ceremony_channel_id: int
    log_channel_id: int | None
    admin_role_id: int
    staff_role_id: int
    moderator_role_id: int
    future_admin_role_id: int
    future_staff_role_id: int
    future_moderator_role_id: int
    quorum_percentage: int = 50


@dataclass(slots=True)
class Nomination:
    id: int
    guild_id: int
    candidate_id: int
    nominated_by_id: int
    rank: Rank
    reason: str | None
    status: NominationStatus
    current_commandment: int
    ceremony_channel_id: int
    ceremony_message_id: int | None
    vote_message_id: int | None
    pending_vote_kind: str | None
    pending_founder_reason: str | None
    decision_type: DecisionType | None
    decision_by_id: int | None
    created_at: datetime
    probation_started_at: datetime | None
    promoted_at: datetime | None
    closed_at: datetime | None


@dataclass(frozen=True, slots=True)
class VoteSummary:
    approve: int
    reject: int
    abstain: int
    participants: int
    eligible: int
    required_for_quorum: int
    quorum_reached: bool

    @property
    def is_tie(self) -> bool:
        return self.approve == self.reject

    @property
    def accepted(self) -> bool:
        return self.approve > self.reject
