from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from models.records import GuildConfig
from utils.errors import CeremonyError
from utils.respond import respond_ephemeral
from .common import handle_command_error, require_guild_member


class ConfigurationCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="ceremonie_configurer",
        description="Configure les salons, les rôles, le Fondateur et le quorum du Grand Héraut.",
    )
    @app_commands.default_permissions(administrator=True)
    async def configure(
        self,
        interaction: discord.Interaction,
        salon_ceremonie: discord.TextChannel,
        role_admin: discord.Role,
        role_staff: discord.Role,
        role_moderateur: discord.Role,
        role_futur_admin: discord.Role,
        role_futur_staff: discord.Role,
        role_futur_moderateur: discord.Role,
        fondateur: discord.Member | None = None,
        salon_logs: discord.TextChannel | None = None,
        quorum_pourcentage: app_commands.Range[int, 1, 100] = 50,
    ) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            existing = await self.bot.config_repository.get(guild.id)
            if existing is None:
                if actor.id != guild.owner_id:
                    raise CeremonyError(
                        "La première configuration doit être effectuée par le propriétaire Discord du serveur."
                    )
            elif actor.id != existing.founder_id:
                raise CeremonyError("Seul le Fondateur configuré peut modifier cette configuration.")

            for role in (
                role_admin,
                role_staff,
                role_moderateur,
                role_futur_admin,
                role_futur_staff,
                role_futur_moderateur,
            ):
                self.bot.role_service.ensure_manageable(guild, role)

            chosen_founder = fondateur or actor
            if chosen_founder is None:
                raise CeremonyError("Le Fondateur sélectionné est introuvable.")

            config = GuildConfig(
                guild_id=guild.id,
                founder_id=chosen_founder.id,
                ceremony_channel_id=salon_ceremonie.id,
                log_channel_id=salon_logs.id if salon_logs else None,
                admin_role_id=role_admin.id,
                staff_role_id=role_staff.id,
                moderator_role_id=role_moderateur.id,
                future_admin_role_id=role_futur_admin.id,
                future_staff_role_id=role_futur_staff.id,
                future_moderator_role_id=role_futur_moderateur.id,
                quorum_percentage=int(quorum_pourcentage),
            )
            await self.bot.config_repository.upsert(config)
            await respond_ephemeral(
                interaction,
                "✅ Configuration enregistrée. Le Fondateur est "
                f"{chosen_founder.mention}, la cérémonie se déroulera dans "
                f"{salon_ceremonie.mention}, avec un quorum de **{quorum_pourcentage} %**.",
            )
        except Exception as error:
            await handle_command_error(interaction, error)

    @app_commands.command(
        name="ceremonie_configuration",
        description="Affiche la configuration actuelle du Grand Héraut.",
    )
    async def show_config(self, interaction: discord.Interaction) -> None:
        try:
            guild, actor = require_guild_member(interaction)
            config = await self.bot.permission_service.require_council(actor)
            text = (
                f"👑 **Fondateur :** <@{config.founder_id}>\n"
                f"🏰 **Salon de cérémonie :** <#{config.ceremony_channel_id}>\n"
                f"📚 **Salon des logs :** {f'<#{config.log_channel_id}>' if config.log_channel_id else 'Non configuré'}\n"
                f"⚖️ **Quorum :** {config.quorum_percentage} %\n\n"
                f"**Rôles définitifs**\n"
                f"• Administrateur : <@&{config.admin_role_id}>\n"
                f"• Staff : <@&{config.staff_role_id}>\n"
                f"• Modérateur : <@&{config.moderator_role_id}>\n\n"
                f"**Rôles provisoires**\n"
                f"• Futur Administrateur : <@&{config.future_admin_role_id}>\n"
                f"• Futur Staff : <@&{config.future_staff_role_id}>\n"
                f"• Futur Modérateur : <@&{config.future_moderator_role_id}>"
            )
            await respond_ephemeral(interaction, text)
        except Exception as error:
            await handle_command_error(interaction, error)


async def setup(bot) -> None:
    await bot.add_cog(ConfigurationCog(bot))
