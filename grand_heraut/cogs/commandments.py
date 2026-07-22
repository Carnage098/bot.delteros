from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from constants.commandments import COMMANDMENTS


class CommandmentsCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command(name="commandements", description="Affiche les Douze Commandements du Conseil.")
    async def commandments(self, interaction: discord.Interaction) -> None:
        text = "\n\n".join(
            f"**{number}.** {commandment}"
            for number, commandment in enumerate(COMMANDMENTS, start=1)
        )
        embed = discord.Embed(
            title="📜 Les Douze Commandements du Conseil",
            description=text,
            color=0xD4AF37,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="aide_heraut", description="Affiche les principales commandes du Grand Héraut.")
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="🏰 Aide du Grand Héraut",
            description=(
                "`/ceremonie_configurer` — configuration initiale\n"
                "`/nomination` — ouvrir une cérémonie\n"
                "`/nomination_reprendre` — reprendre une cérémonie suspendue\n"
                "`/vote_clore` — clôturer le scrutin actif\n"
                "`/evaluation` — ajouter un avis privé\n"
                "`/adoubement` — ouvrir l'examen final\n"
                "`/nomination_statut` — voir une candidature\n"
                "`/candidatures_actives` — voir les procédures en cours\n"
                "`/commandements` — afficher les règles sacrées"
            ),
            color=0x5865F2,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot) -> None:
    await bot.add_cog(CommandmentsCog(bot))
