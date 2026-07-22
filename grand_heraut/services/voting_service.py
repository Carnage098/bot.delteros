from __future__ import annotations

from models.records import VoteSummary
from repositories.vote_repository import VoteRepository
from models.enums import VoteKind
from services.permission_service import PermissionService


class VotingService:
    def __init__(
        self,
        vote_repository: VoteRepository,
        permission_service: PermissionService,
    ) -> None:
        self.vote_repository = vote_repository
        self.permission_service = permission_service

    async def summarize(self, nomination_id: int, vote_kind: VoteKind, guild, config) -> VoteSummary:
        eligible_ids = await self.permission_service.eligible_council_ids(guild, config)
        rows = await self.vote_repository.list_votes(nomination_id, vote_kind)
        valid_rows = [row for row in rows if row["voter_id"] in eligible_ids]
        counts = {"approve": 0, "reject": 0, "abstain": 0}
        for row in valid_rows:
            counts[row["choice"]] += 1

        required = self.permission_service.required_quorum(
            len(eligible_ids),
            config.quorum_percentage,
        )
        return VoteSummary(
            approve=counts["approve"],
            reject=counts["reject"],
            abstain=counts["abstain"],
            participants=len(valid_rows),
            eligible=len(eligible_ids),
            required_for_quorum=required,
            quorum_reached=len(valid_rows) >= required,
        )
