# Le Grand Héraut — Bot de cérémonies pour Fun Row

Bot Discord en Python qui organise des nominations solennelles de **Futurs Staffs**, **Futurs Modérateurs** et **Futurs Administrateurs**.

Le bot gère toute la procédure :

- convocation du candidat ;
- lecture des Douze Commandements ;
- serment ;
- vote du Conseil ;
- contrôle du quorum ;
- voix prépondérante du Fondateur en cas d’égalité ;
- décision exclusive du Fondateur si le quorum est insuffisant ;
- période d’épreuve sans durée automatique ;
- évaluations privées ;
- vote d’adoubement ;
- attribution et retrait des rôles ;
- journalisation PostgreSQL ;
- restauration des boutons après un redémarrage.

## 1. Prérequis

- Python 3.12 ou 3.13 ;
- un bot créé dans le Discord Developer Portal ;
- une base PostgreSQL ;
- un serveur Discord dans lequel tu peux gérer les rôles et les salons.

## 2. Intents Discord

Dans le Discord Developer Portal, ouvre la page du bot puis active :

- **Server Members Intent**.

Le bot n’a pas besoin du Message Content Intent car il utilise des commandes slash et des boutons.

## 3. Permissions du bot

Lors de l’invitation, accorde au minimum :

- Voir les salons ;
- Envoyer des messages ;
- Intégrer des liens ;
- Lire l’historique des messages ;
- Gérer les rôles ;
- Utiliser les commandes de l’application.

Le rôle principal du bot doit être placé **au-dessus** de tous les rôles qu’il devra attribuer ou retirer.

## 4. Rôles à créer dans Fun Row

Crée ou sélectionne les rôles suivants :

- Administrateur ;
- Staff ;
- Modérateur ;
- Futur Administrateur ;
- Futur Staff ;
- Futur Modérateur.

Les noms peuvent être différents : le bot utilise les identifiants Discord enregistrés pendant la configuration.

## 5. Installation locale

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS ou Linux

```bash
source .venv/bin/activate
```

Installe ensuite les dépendances :

```bash
pip install -r requirements.txt
```

Copie `.env.example` vers `.env`, puis remplis les variables :

```env
DISCORD_TOKEN=token_du_bot
DATABASE_URL=postgresql://user:password@host:5432/database
GUILD_ID=id_du_serveur_fun_row
LOG_LEVEL=INFO
```

`GUILD_ID` est recommandé pendant le développement afin que les commandes soient synchronisées immédiatement sur Fun Row.

Lance le bot :

```bash
python bot.py
```

## 6. Déploiement Railway

1. Envoie le dossier sur GitHub.
2. Crée un projet Railway depuis le dépôt.
3. Ajoute un service PostgreSQL au projet.
4. Ajoute les variables `DISCORD_TOKEN`, `DATABASE_URL`, `GUILD_ID` et `LOG_LEVEL`.
5. Railway utilisera la commande `python bot.py` définie dans `railway.json`.

Les migrations SQL sont exécutées automatiquement au démarrage.

## 7. Première configuration Discord

La première configuration doit être réalisée par le propriétaire Discord du serveur.

Utilise :

```text
/ceremonie_configurer
```

Tu devras choisir :

- le salon de cérémonie ;
- le salon des logs, facultatif ;
- le Fondateur ;
- les trois rôles définitifs ;
- les trois rôles provisoires ;
- le pourcentage du quorum.

Par la suite, seul le Fondateur configuré pourra modifier cette configuration.

## 8. Déroulement complet

### Nomination

```text
/nomination candidat:@Membre rang:Futur Modérateur raison:...
```

Le candidat doit ensuite :

1. s’avancer devant le Conseil ;
2. accepter les Douze Commandements ;
3. prêter serment.

Le bot ouvre alors le vote du Conseil.

### Vote

Chaque membre du Conseil peut :

- approuver ;
- refuser ;
- s’abstenir ;
- modifier son vote avant la clôture.

La clôture se fait avec :

```text
/vote_clore candidat:@Membre
```

Si le quorum est insuffisant ou si les voix sont à égalité, le bot demande automatiquement la décision du Fondateur.

### Période d’épreuve

Lorsque la nomination est acceptée, le rôle provisoire est attribué. La période d’épreuve n’a aucune date de fin automatique.

Le Conseil peut enregistrer des observations privées :

```text
/evaluation candidat:@Membre avis:Positive commentaire:...
```

### Adoubement

Lorsque le Conseil estime que le candidat est prêt :

```text
/adoubement candidat:@Membre
```

Le candidat confirme son engagement, puis un nouveau vote est ouvert. Utilise de nouveau `/vote_clore` pour appliquer la décision.

En cas d’acceptation, le bot retire le rôle provisoire et attribue le rôle définitif.

## 9. Commandes principales

| Commande | Fonction |
|---|---|
| `/ceremonie_configurer` | Configure le bot |
| `/ceremonie_configuration` | Affiche la configuration |
| `/nomination` | Commence une cérémonie |
| `/nomination_annuler` | Annule une candidature |
| `/nomination_reprendre` | Reprend une cérémonie suspendue |
| `/nomination_statut` | Affiche une candidature |
| `/candidatures_actives` | Liste les procédures actives |
| `/vote_clore` | Clôture le vote actif |
| `/evaluation` | Ajoute une évaluation privée |
| `/evaluations_consulter` | Consulte les évaluations |
| `/adoubement` | Lance l’examen final |
| `/historique_nominations` | Affiche l’historique |
| `/commandements` | Affiche les Douze Commandements |
| `/aide_heraut` | Affiche l’aide rapide |

## 10. Structure du projet

```text
grand_heraut/
├── bot.py
├── config.py
├── database.py
├── cogs/
├── constants/
├── embeds/
├── migrations/
├── models/
├── repositories/
├── services/
├── tests/
├── utils/
└── views/
```

## 11. Sécurité intégrée

- vérification des identifiants de rôles plutôt que de leurs noms ;
- impossibilité de se nommer soi-même ;
- un candidat ne peut pas voter sur sa propre candidature ;
- seuls les membres du Conseil peuvent nommer, voter, évaluer et clôturer ;
- seule la personne enregistrée comme Fondateur peut exercer la voix prépondérante ;
- vérification de la hiérarchie des rôles ;
- aucune promotion automatique après une durée déterminée ;
- une seule candidature active par membre ;
- votes uniques mais modifiables ;
- boutons persistants après redémarrage ;
- historique enregistré dans PostgreSQL.

## 12. Vérifications avant lancement

- le bot possède la permission Gérer les rôles ;
- le rôle du bot est placé au-dessus des six rôles configurés ;
- Server Members Intent est activé ;
- `DATABASE_URL` pointe vers PostgreSQL ;
- `GUILD_ID` correspond à Fun Row ;
- le bot peut écrire dans le salon de cérémonie et le salon des logs.
