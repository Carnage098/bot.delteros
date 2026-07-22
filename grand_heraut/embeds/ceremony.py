from __future__ import annotations

import discord

from constants.commandments import COMMANDMENTS
from constants.texts import OATH_TEXT
from models.enums import Rank, VoteKind
from models.records import Nomination, VoteSummary

GOLD = 0xD4AF37
BLUE = 0x5865F2
GREEN = 0x57F287
RED = 0xED4245
PURPLE = 0x9B59B6


def nomination_invitation(candidate: discord.Member, nominator: discord.Member, rank: Rank, reason: str | None) -> discord.Embed:
    description = (
        "En ce jour, le Conseil de **Fun Row** porte son regard sur "
        f"{candidate.mention}.\n\n"
        f"Sur proposition de {nominator.mention}, il lui est offert de se présenter "
        f"devant le Conseil afin de prétendre au rang de **{rank.future_label}**.\n\n"
        "Que le candidat s’avance devant l’assemblée et déclare s’il accepte "
        "de participer à cette cérémonie."
    )
    if reason:
        description += f"\n\n**Motif de la proposition :**\n{reason}"
    return discord.Embed(
        title="🔔 Que les portes de la Grande Salle soient fermées !",
        description=description,
        color=GOLD,
    )


def commandment(number: int) -> discord.Embed:
    return discord.Embed(
        title=f"📜 Commandement {number} sur {len(COMMANDMENTS)}",
        description=(
            f"**{COMMANDMENTS[number - 1]}**\n\n"
            "Acceptes-tu de respecter ce commandement dans l’exercice de tes fonctions ?"
        ),
        color=PURPLE,
    )


def oath(candidate: discord.Member) -> discord.Embed:
    return discord.Embed(
        title="🛡️ Le serment du candidat",
        description=OATH_TEXT.format(candidate_name=candidate.display_name),
        color=GOLD,
    )


def vote_open(candidate: discord.Member, rank: Rank, vote_kind: VoteKind) -> discord.Embed:
    if vote_kind is VoteKind.NOMINATION:
        title = "📜 Le Conseil est appelé à se prononcer"
        text = (
            f"{candidate.mention} a entendu les Douze Commandements, les a acceptés "
            "et a prêté serment devant l’assemblée.\n\n"
            f"Le Conseil doit décider s’il peut commencer sa période d’épreuve "
            f"comme **{rank.future_label}**."
        )
    else:
        title = "👑 Le Conseil examine l’adoubement"
        text = (
            f"{candidate.mention} a confirmé sa volonté de continuer à servir Fun Row.\n\n"
            f"Le Conseil doit décider s’il peut désormais recevoir le rôle définitif "
            f"de **{rank.label}**."
        )
    return discord.Embed(title=title, description=text, color=BLUE)


def vote_result(candidate: discord.Member, rank: Rank, summary: VoteSummary, accepted: bool, vote_kind: VoteKind) -> discord.Embed:
    if vote_kind is VoteKind.NOMINATION:
        action = "commencer sa période d’épreuve" if accepted else "voir sa candidature retenue"
    else:
        action = "recevoir son rôle définitif" if accepted else "être adoubé"
    title = "🔔 Le Conseil a rendu son jugement"
    verdict = "acceptée" if accepted else "refusée"
    description = (
        f"La décision concernant {candidate.mention} a été **{verdict}**.\n\n"
        f"Le candidat {'peut' if accepted else 'ne peut pas'} {action}.\n\n"
        f"✅ Favorables : **{summary.approve}**\n"
        f"❌ Défavorables : **{summary.reject}**\n"
        f"⚪ Abstentions : **{summary.abstain}**\n"
        f"👥 Participants : **{summary.participants}**"
    )
    return discord.Embed(title=title, description=description, color=GREEN if accepted else RED)


def founder_required(candidate: discord.Member, reason: str) -> discord.Embed:
    if reason == "tie":
        text = (
            "Les suffrages favorables et défavorables sont à égalité. "
            "Conformément aux règles de Fun Row, la voix prépondérante du Fondateur est requise."
        )
    else:
        text = (
            "Le quorum du Conseil n’a pas été atteint. Conformément aux règles de Fun Row, "
            "le Fondateur doit accepter ou refuser seul la candidature."
        )
    return discord.Embed(
        title="👑 Décision du Fondateur requise",
        description=f"{candidate.mention}\n\n{text}\n\nLa procédure reste en attente jusqu’à sa décision.",
        color=GOLD,
    )


def probation_started(candidate: discord.Member, rank: Rank) -> discord.Embed:
    return discord.Embed(
        title="⚔️ Que tous soient témoins de la décision du Conseil !",
        description=(
            f"À compter de ce jour, {candidate.mention} portera le titre de :\n\n"
            f"🛡️ **{rank.future_label} de Fun Row**\n\n"
            "Il entre dans une période d’épreuve d’une durée indéterminée. "
            "Le Conseil décidera librement du moment où sa candidature pourra être "
            "examinée pour un adoubement définitif."
        ),
        color=GREEN,
    )


def final_confirmation(candidate: discord.Member, rank: Rank) -> discord.Embed:
    return discord.Embed(
        title="🛡️ Dernière déclaration du candidat",
        description=(
            f"{candidate.mention}, le Conseil souhaite examiner ton adoubement au rang de "
            f"**{rank.label}**.\n\n"
            "Confirmes-tu ta volonté de servir Fun Row et de continuer à respecter "
            "les Douze Commandements ?"
        ),
        color=GOLD,
    )


def promoted(candidate: discord.Member, rank: Rank) -> discord.Embed:
    return discord.Embed(
        title="👑 Que tous ici présents soient témoins !",
        description=(
            f"{candidate.mention} s’est avancé devant le Conseil, a entendu et accepté "
            "les Douze Commandements, a prêté serment et a reçu l’approbation nécessaire "
            "à son élévation.\n\n"
            "Après avoir accompli sa période d’épreuve avec sérieux et dignité, "
            "il est désormais reconnu comme :\n\n"
            f"⚔️ **{rank.label} du Royaume de Fun Row !**\n\n"
            "Qu’il reçoive son rôle et ses responsabilités, et qu’il les exerce de la "
            "manière la plus raisonnable et la plus juste possible."
        ),
        color=GOLD,
    )


def status_embed(nomination: Nomination, candidate: discord.Member | None) -> discord.Embed:
    candidate_text = candidate.mention if candidate else f"<@{nomination.candidate_id}>"
    embed = discord.Embed(
        title=f"📋 Candidature n°{nomination.id}",
        color=BLUE,
    )
    embed.add_field(name="Candidat", value=candidate_text, inline=True)
    embed.add_field(name="Rang visé", value=nomination.rank.label, inline=True)
    embed.add_field(name="État", value=nomination.status.label, inline=False)
    embed.add_field(
        name="Commandements acceptés",
        value=f"{nomination.current_commandment}/12",
        inline=True,
    )
    if nomination.probation_started_at:
        embed.add_field(
            name="Début de l’épreuve",
            value=discord.utils.format_dt(nomination.probation_started_at, "F"),
            inline=False,
        )
    if nomination.reason:
        embed.add_field(name="Motif initial", value=nomination.reason[:1024], inline=False)
    return embed
