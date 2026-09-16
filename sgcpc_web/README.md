# SGCPC — Système de Gestion de la Confiscation des Permis de Conduire

Application web Django + Tailwind CSS pour le Ministère des Transports du Niger,
conforme au cahier des charges fonctionnel et technique v1.0 (7 septembre 2026).

## Interface

Design moderne à sidebar (navigation latérale par catégorie : Opérations,
Commission, Pilotage), police Inter, palette de couleurs cohérente (orange
institutionnel + gris ardoise), cartes arrondies avec ombres douces, badges de
statut colorés, graphiques Chart.js sur le tableau de bord. Responsive :
sidebar fixe en desktop, barre de navigation basse en mobile.

**Note sur le rendu** : Tailwind CSS et la police Inter sont chargés depuis
un CDN (`cdn.tailwindcss.com`, `fonts.googleapis.com`) directement dans le
navigateur de l'utilisateur final — cela fonctionne normalement pour vous,
même si ces domaines étaient bloqués dans l'environnement où ce projet a été
développé (d'où l'absence de captures d'écran stylées dans les échanges de
développement ; la structure HTML et les données ont été vérifiées par ce
biais, le rendu visuel Tailwind par lecture du code).

## État d'avancement

| Module CDCF | Statut | Détail |
|---|---|---|
| Module 1 — Saisie accident | ✅ Fonctionnel | Formulaire complet, génération auto du n° dossier, bordereau PDF + QR code |
| Module 2 — Vérification | ✅ Fonctionnel | Tableau de bord, valider/rejeter/complément |
| Module 3 — Gestion commissions | ✅ Fonctionnel | Sessions, convocations PDF, présence |
| Module 4 — Audition & décision | ✅ Fonctionnel | Audition, décision motivée, arrêté PDF |
| Module 5 — Restitution | ✅ Fonctionnel | Restitution, clôture et archivage du dossier |
| Module 6 — Portail citoyen | ⏳ Non démarré | Prévu Phase 2 (optionnel dans le CDCF) |
| Module 7 — Reporting/stats | ✅ Fonctionnel | Dashboard graphique, exports CSV/PDF, alertes — testés |
| Tests automatisés | ✅ 37 tests | `pytest-django` — modèles, API, RBAC, workflow complet, régressions |
| API REST (mobile Flutter) | ✅ Fonctionnel | JWT + endpoints Modules 1-5, testés de bout en bout |
| OTP SMS réel | ⏳ Simulé | Les envois SMS/email sont actuellement simulés (flag booléen) |

Le workflow complet (saisie → vérification → commission → audition → décision →
restitution → clôture) a été testé de bout en bout, **à la fois en web et via l'API REST**,
et fonctionne.

## API REST (pour l'app mobile Flutter)

Base : `/api/v1/`. Authentification par JWT (Bearer token).

### Authentification

```
POST /api/v1/auth/token/            {"username": "...", "password": "..."}
                                     -> {"access": "...", "refresh": "...", "utilisateur": {...}}
POST /api/v1/auth/token/refresh/    {"refresh": "..."} -> {"access": "..."}
GET  /api/v1/auth/profil/           (Bearer token) -> profil de l'utilisateur connecté
```

Le token d'accès contient le `role` de l'utilisateur, directement exploitable côté
Flutter pour adapter l'interface sans appel réseau supplémentaire.
Durée de vie : access token 8h, refresh token 7 jours (adapté à la connectivité
intermittente sur le terrain — cf. risques du CDCF).

### Module 1 & 2 — Dossiers

```
GET    /api/v1/dossiers/                    Liste (paginée, filtrable par ?statut=&type_incident=&ville=&search=)
POST   /api/v1/dossiers/                    Créer un dossier (conducteur + véhicule imbriqués) — rôle Police/Gendarmerie
GET    /api/v1/dossiers/{id}/               Détail complet (pièces, historique inclus)
GET    /api/v1/dossiers/{id}/bordereau/     Télécharger le bordereau PDF
POST   /api/v1/dossiers/{id}/pieces/        Upload d'une pièce jointe (multipart/form-data)
POST   /api/v1/dossiers/{id}/valider/       Valider (Module 2) — rôle Admin régional/système
POST   /api/v1/dossiers/{id}/rejeter/       Rejeter, {"motif": "..."} obligatoire
POST   /api/v1/dossiers/{id}/complement/    Demander un complément, {"motif": "..."}
GET    /api/v1/conducteurs/?search=...      Recherche conducteur par n° permis/nom
GET    /api/v1/vehicules/?search=...        Recherche véhicule par plaque
```

### Module 3 & 4 — Commissions, auditions, décisions

```
GET/POST  /api/v1/commissions/sessions/                        Sessions de commission
POST      /api/v1/commissions/sessions/{id}/programmer/{dossier_id}/   Convoquer un dossier
GET       /api/v1/commissions/convocations/                    Liste des convocations
GET       /api/v1/commissions/convocations/{id}/lettre_pdf/    Lettre de convocation PDF
POST      /api/v1/commissions/convocations/{id}/presence/      {"statut": "present"|"absent"}
GET/POST  /api/v1/commissions/auditions/                       Enregistrer une audition
GET/POST  /api/v1/decisions/                                   Rendre une décision
GET       /api/v1/decisions/{id}/arrete_pdf/                   Arrêté de décision PDF
```

### Module 5 — Restitution

```
GET   /api/v1/restitutions/?en_attente=true    Dossiers en attente de restitution
POST  /api/v1/restitutions/{id}/restituer/     {"piece_identite_verifiee": true}
```

### Module 7 — Statistiques et reporting

```
GET  /api/v1/stats/tableau-de-bord/    Toutes les statistiques en un appel
GET  /api/v1/stats/alertes/            Dossiers en retard + sessions surbookées
```

Côté web, le tableau de bord complet (graphiques Chart.js) est sur `/stats/`,
avec exports `/stats/export/csv/` et `/stats/export/pdf/`, et le détail des
alertes sur `/stats/alertes/`.

## Tests automatisés

```bash
python -m pytest tests/ -v
```

37 tests couvrant :
- **Modèles** : numérotation séquentielle des dossiers, délais métier (24h de
  modification libre, 30 jours avant alerte de retard)
- **API Module 1/2** : création, réutilisation d'un conducteur déjà connu,
  génération automatique du bordereau, traçabilité, validation/rejet
- **RBAC** : un agent ne voit que ses propres dossiers, ne peut pas valider un
  dossier ni rendre une décision ; la lecture reste ouverte à tout authentifié
- **Workflow complet** : test d'intégration bout-en-bout reproduisant les 7
  étapes du CDCF (saisie → vérification → commission → audition → décision →
  restitution → clôture), y compris le cas particulier du retrait définitif
  (transmission au tribunal)
- **Module 7** : détection des alertes (retard, surbooking), export CSV avec
  vérification explicite de l'encodage UTF-8, export PDF, API de statistiques

Deux bugs réels ont été détectés et corrigés grâce à cette suite : l'un sur
l'encodage CSV (voir plus haut), l'autre sur la création d'un dossier pour un
conducteur déjà enregistré (le validateur d'unicité automatique de DRF
entrait en conflit avec la logique métier de réutilisation du conducteur).

### Permissions par rôle (RBAC)

| Action | Rôle requis |
|---|---|
| Créer un dossier | Agent de Police / Gendarme |
| Valider/rejeter un dossier | Administrateur régional / système |
| Créer une session, auditionner, décider | Membre / Secrétaire de commission |
| Lecture (GET) | Tout utilisateur authentifié (filtré selon son rôle pour les dossiers) |

Un agent de terrain ne voit que les dossiers qu'il a lui-même saisis dans les listes.


## Installation

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Accès :
- Application : http://localhost:8000/
- Admin Django : http://localhost:8000/admin/

## Créer des utilisateurs de test

```bash
python manage.py shell
```

```python
from comptes.models import Utilisateur, Role
Utilisateur.objects.create_user("agent1", password="...", role=Role.AGENT_POLICE, first_name="...", last_name="...")
Utilisateur.objects.create_user("president1", password="...", role=Role.MEMBRE_COMMISSION, first_name="...", last_name="...")
```

Rôles disponibles : `AGENT_POLICE`, `GENDARME`, `ADMIN_REGIONAL`, `SECRETAIRE_COMMISSION`,
`MEMBRE_COMMISSION`, `ADMIN_SYSTEME`.

## Structure du projet

```
config/             Paramètres Django, urls racine
comptes/             Utilisateurs, rôles RBAC, authentification
dossiers/            Modules 1 & 2 — saisie et vérification
commissions/         Module 3 & audition (Module 4) — sessions, convocations
decisions/           Module 4 — décision de la commission, arrêté PDF
restitution/         Module 5 — restitution et clôture
reporting_stats/     Module 7 (squelette, à développer)
templates/           Templates Tailwind CSS (via CDN pour le développement)
```

## Prochaines étapes recommandées

1. **Application Flutter** : consommer l'API REST ci-dessus (déjà écrite dans le
   projet `sgcpc_mobile`, à compiler et tester avec le SDK Flutter).
2. **Module 6 (Portail citoyen)** : consultation par le conducteur (Phase 2, optionnel).
3. **RBAC affiné** : la restriction par rôle est en place sur les actions sensibles ;
   affiner encore pour la restitution (actuellement ouverte à tout authentifié).
4. **Production** : passer de SQLite à PostgreSQL (config déjà prête en commentaire dans
   `settings.py`), remplacer le Tailwind CDN par un build compilé, intégrer un vrai
   fournisseur SMS (Twilio/Orange/Moov), chiffrement des documents sensibles.

## Notes techniques

- Base de données : SQLite en développement (fichier `db.sqlite3`, non versionné)
- PDF générés avec `reportlab`, QR codes avec `qrcode`
- Frontend : Tailwind CSS via CDN (à remplacer par un build npm en production pour
  optimiser la taille et éviter la dépendance à un CDN externe)
- Django 5.2 LTS, Python 3.12
