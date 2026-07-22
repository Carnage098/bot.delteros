from __future__ import annotations

from enum import StrEnum


class Rank(StrEnum):
    STAFF = "staff"
    MODERATOR = "moderator"
    ADMINISTRATOR = "administrator"

    @property
    def label(self) -> str:
        return {
            Rank.STAFF: "Staff",
            Rank.MODERATOR: "Modérateur",
            Rank.ADMINISTRATOR: "Administrateur",
        }[self]

    @property
    def future_label(self) -> str:
        return f"Futur {self.label}"


class NominationStatus(StrEnum):
    CONVOCATION = "convocation"
    COMMANDMENTS = "commandments"
    OATH = "oath"
    SUSPENDED = "suspended"
    NOMINATION_VOTE = "nomination_vote"
    WAITING_FOUNDER = "waiting_founder"
    PROBATION = "probation"
    FINAL_CONFIRMATION = "final_confirmation"
    ADOUBEMENT_VOTE = "adoubement_vote"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    RENOUNCED = "renounced"

    @property
    def label(self) -> str:
        return {
            NominationStatus.CONVOCATION: "Convocation du candidat",
            NominationStatus.COMMANDMENTS: "Lecture des commandements",
            NominationStatus.OATH: "Prestation du serment",
            NominationStatus.SUSPENDED: "Cérémonie suspendue",
            NominationStatus.NOMINATION_VOTE: "Vote de nomination",
            NominationStatus.WAITING_FOUNDER: "Décision du Fondateur requise",
            NominationStatus.PROBATION: "Période d'épreuve",
            NominationStatus.FINAL_CONFIRMATION: "Confirmation finale du candidat",
            NominationStatus.ADOUBEMENT_VOTE: "Vote d'adoubement",
            NominationStatus.PROMOTED: "Adoubement terminé",
            NominationStatus.REJECTED: "Candidature refusée",
            NominationStatus.CANCELLED: "Cérémonie annulée",
            NominationStatus.RENOUNCED: "Candidat ayant renoncé",
        }[self]


class VoteKind(StrEnum):
    NOMINATION = "nomination"
    ADOUBEMENT = "adoubement"


class VoteChoice(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class DecisionType(StrEnum):
    COUNCIL_MAJORITY = "council_majority"
    FOUNDER_TIEBREAK = "founder_tiebreak"
    FOUNDER_NO_QUORUM = "founder_no_quorum"
    FOUNDER_OVERRIDE = "founder_override"
