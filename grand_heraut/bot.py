from __future__ import annotations

import logging

import discord
from discord.ext import commands

from config import Settings
from database import Database
from models.enums import NominationStatus, VoteKind
from repositories import (
    ConfigRepository,
    EvaluationRepository,
    LogRepository,
    NominationRepository,
    VoteRepository,
)
from services import CeremonyService, PermissionService, RoleService, VotingService
from views import (
    CommandmentsView,
    CouncilVoteView,
    FinalConfirmationView,
    FounderDecisionView,
    NominationInvitationView,
    OathView,
)

COGS = (
    "cogs.configuration",
    "cogs.nomination",
    "cogs.voting",
    "cogs.probation",
    "cogs.adoubement",
    "cogs.status",
    "cogs.commandments",
)


class HerautBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                roles=False,
                users=True,
                replied_user=False,
            ),
        )
        self.settings = settings
        self.database = Database(settings.database_url)

    async def setup_hook(self) -> None:
        await self.database.connect()
        await self.database.run_migrations()
        pool = self.database.require_pool()

        self.config_repository = ConfigRepository(pool)
        self.nomination_repository = NominationRepository(pool)
        self.vote_repository = VoteRepository(pool)
        self.evaluation_repository = EvaluationRepository(pool)
        self.log_repository = LogRepository(pool)

        self.permission_service = PermissionService(self.config_repository)
        self.role_service = RoleService()
        self.voting_service = VotingService(self.vote_repository, self.permission_service)
        self.ceremony_service = CeremonyService(
            self,
            self.config_repository,
            self.nomination_repository,
            self.vote_repository,
            self.evaluation_repository,
            self.log_repository,
            self.permission_service,
            self.role_service,
            self.voting_service,
        )

        for extension in COGS:
            await self.load_extension(extension)

        await self.restore_persistent_views()

        if self.settings.guild_id:
            guild_object = discord.Object(id=self.settings.guild_id)
            self.tree.copy_global_to(guild=guild_object)
            synced = await self.tree.sync(guild=guild_object)
            logging.getLogger(__name__).info(
                "%d commande(s) synchronisée(s) sur le serveur configuré.", len(synced)
            )
        else:
            synced = await self.tree.sync()
            logging.getLogger(__name__).info("%d commande(s) globale(s) synchronisée(s).", len(synced))

    async def restore_persistent_views(self) -> None:
        nominations = await self.nomination_repository.list_all_active()
        restored = 0
        for nomination in nominations:
            view = None
            message_id = nomination.ceremony_message_id
            if nomination.status is NominationStatus.CONVOCATION:
                view = NominationInvitationView(nomination.id)
            elif nomination.status is NominationStatus.COMMANDMENTS:
                view = CommandmentsView(nomination.id)
            elif nomination.status is NominationStatus.OATH:
                view = OathView(nomination.id)
            elif nomination.status is NominationStatus.NOMINATION_VOTE:
                view = CouncilVoteView(nomination.id, VoteKind.NOMINATION)
                message_id = nomination.vote_message_id
            elif nomination.status is NominationStatus.FINAL_CONFIRMATION:
                view = FinalConfirmationView(nomination.id)
            elif nomination.status is NominationStatus.ADOUBEMENT_VOTE:
                view = CouncilVoteView(nomination.id, VoteKind.ADOUBEMENT)
                message_id = nomination.vote_message_id
            elif nomination.status is NominationStatus.WAITING_FOUNDER:
                view = FounderDecisionView(nomination.id)
                message_id = nomination.vote_message_id

            if view is not None and message_id is not None:
                self.add_view(view, message_id=message_id)
                restored += 1
        logging.getLogger(__name__).info("%d vue(s) persistante(s) restaurée(s).", restored)

    async def on_ready(self) -> None:
        logging.getLogger(__name__).info(
            "Connecté comme %s (%s)", self.user, self.user.id if self.user else "inconnu"
        )

    async def close(self) -> None:
        await self.database.close()
        await super().close()


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    )
    bot = HerautBot(settings)
    bot.run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
