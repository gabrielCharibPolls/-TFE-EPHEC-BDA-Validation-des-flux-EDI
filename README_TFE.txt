================================================================================
TFE EPHEC BDA — Gabriel Charib — Validation des flux EDI (Scabel)
================================================================================

SUJET (contrat) : Optimisation de la surveillance des flux EDI et détection
proactive des erreurs.

Ce dépôt contient :
- in/                    Fichiers commandes ORDERS (extension .ORO, XML ISO-8859-15)
- validator/             Service Python de validation (10 règles métier)
- sql/init.sql           Schéma PostgreSQL (historique des validations)
- docker-compose.yml     Base PostgreSQL 16 + exécution du validateur
- anonymize_oro_orders.py Anonymisation RGPD (hors Docker, optionnel)
- FIL_CONDUCTEUR_TFE.md  Fil conducteur objectifs / architecture
- JOURNAL_IMPLEMENTATION_TFE.md  Historique des choix techniques (à recopier dans le mémoire)

Chaque évolution importante du code est résumée dans JOURNAL_IMPLEMENTATION_TFE.md pour que tu
puisses la reporter dans ton document de TFE (Word / LaTeX / PDF) sans relire tout le code.

--------------------------------------------------------------------------------
STACK CONSEILLÉE (pour le mémoire)
--------------------------------------------------------------------------------

- OS conteneur : Debian bookworm-slim (image officielle, support long terme,
  facile à justifier face à Alpine si besoin de libc standard / débogage).

- Langage métier : Python 3 (bibliothèque standard xml.etree pour l’EDIFACT
  XMLisé, même famille que le script d’anonymisation).

- Base de données : PostgreSQL 16 (open source, adapté aux KPI / Power BI,
  embarqué en local via Docker pour la démo et la reproductibilité jury).

- Orchestration : Docker Compose (un service db + un service validator batch).

Alternatives à critiquer dans le mémoire : exécution sur AWS RDS au lieu de
Postgres local ; runtime Alpine plus léger mais moins confortable pour les
dépendances système ; validation uniquement XSD sans règles Python.

--------------------------------------------------------------------------------
PRÉREQUIS
--------------------------------------------------------------------------------

- Docker Desktop ou Docker Engine + plugin Compose v2
- Dossier in/ rempli avec des fichiers .ORO

--------------------------------------------------------------------------------
LANCER LA BASE DE DONNÉES
--------------------------------------------------------------------------------

À la racine du projet TFE :

  docker compose up -d db

Attendre que le healthcheck soit vert (quelques secondes). Le script sql/init.sql
crée les tables validation_runs et validation_errors au premier démarrage.

--------------------------------------------------------------------------------
LANCER LE SERVICE DE VALIDATION (UNE FOIS)
--------------------------------------------------------------------------------

  docker compose run --rm validator

Le conteneur lit tous les *.ORO dans in/ (monté en /data/in en lecture seule),
applique les 10 règles, écrit une ligne par fichier dans validation_runs et
le détail des anomalies dans validation_errors.

Pour limiter le nombre de fichiers (test rapide), éditer docker-compose.yml
section validator / environment et décommenter par exemple :

  VALIDATOR_MAX_FILES: "50"

--------------------------------------------------------------------------------
CONNEXION QLIK SENSE / CLIENT SQL (Docker local)
--------------------------------------------------------------------------------

Hôte : localhost
Port : 5433
Base : edi_validation
Utilisateur : edi
Mot de passe : edi

(Railway : voir .env.railway pour Qlik Cloud — hors Git.)

--------------------------------------------------------------------------------
ALERTES (Teams / e-mail)
--------------------------------------------------------------------------------

Sur KO ou PARSE_ERROR, si configuré dans .env (voir env.example) :
  TEAMS_WEBHOOK_URL=https://...
  SMTP_HOST=... SMTP_TO=... (et SMTP_USER/SMTP_PASSWORD si auth)

Désactiver pour un batch de test : python -m app.main --no-alert ...

--------------------------------------------------------------------------------
LOGS
--------------------------------------------------------------------------------

Sortie JSON sur stdout (une ligne par événement). Exemple :
  {"ts":"...","level":"INFO","message":"validation","filename":"x.ORO","status":"KO"}

--------------------------------------------------------------------------------
TESTS
--------------------------------------------------------------------------------

  make test
  # ou : cd validator && . .venv/bin/activate && python -m pytest tests/ -v

--------------------------------------------------------------------------------
VALIDATION SANS DOCKER (OPTIONNEL)
--------------------------------------------------------------------------------

  cd validator
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  export DATABASE_URL=postgresql://edi:edi@localhost:5432/edi_validation
  python -m app.main --input-dir ../in --skip-db

--skip-db : valide seulement, sans PostgreSQL.

--------------------------------------------------------------------------------
LES 10 RÈGLES (identifiants R01–R10)
--------------------------------------------------------------------------------

Implémentées dans validator/app/rules.py — à citer tel quel dans le rapport :

R01  Enveloppe XML : racine Envelope et présence Body/ORDERS
R02  UNB : émetteur, destinataire, référence d’échange renseignés
R03  UNH : message ORDERS version 96A
R04  Cohérence BGM/e01_1004 avec UNH/e01_0062
R05  Présence d’une date document DTM qualificateur 137
R06  Présence NAD acheteur (BY) avec GLN
R07  Présence NAD fournisseur (SU) avec GLN et nom
R08  Cohérence UNB/e01_0020 et UNZ/e02_0020
R09  Chaque ligne g025 : LIN avec GTIN numérique longueur 8–14
R10  Chaque PRI : montant e02_5118 numérique ; les zéros sont acceptés (gratuit/promo), les négatifs refusés

--------------------------------------------------------------------------------
FICHIERS UTILES AU JURY
--------------------------------------------------------------------------------

- FIL_CONDUCTEUR_TFE.md   Fil conducteur objectifs / architecture
- PLANNING_SUIVI_30MAI.md  Planning mercredi → vendredi
- guides/GUIDE_COLLAGE_WORD_30MAI.md   Journée Word
- guides/GUIDE_FIGURES_JEUDI.md        Journée figures + Qlik
- guides/GUIDE_DEPOT_MOODLE_VENDREDI.md Journée PDF Moodle
- MEMOIRE_COLLAGE_29MAI.md   Textes à coller dans le Word (remise 30 mai)
- livrables/DECLARATION_*.md Modèles non-plagiat et IA
- NOTES_ALIGNEMENT_MEMOIRE.md   Checklist mémoire ↔ code
- REMISE_MOODLE_CHECKLIST.md   Dépôt PDF Moodle
- PREP_SOUTENANCE_ORAL.md   Script 10 min + Q&R jury
- figures/*.png   Aperçus (remplacer figure3/4 par captures Qlik Cloud)
- requirements-oro-anonymize.txt   Dépendances script anonymisation (stdlib)
- validator/requirements.txt     Dépendances service (psycopg2)

================================================================================
Fin du README TFE (texte brut)
================================================================================
