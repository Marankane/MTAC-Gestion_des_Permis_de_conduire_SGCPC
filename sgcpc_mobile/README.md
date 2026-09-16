# SGCPC Mobile — Application terrain (Flutter)

Application mobile pour la saisie d'accidents/incidents par la Police et la
Gendarmerie (Module 1 du CDCF), avec **mode hors-ligne complet**.

## ⚠️ Étape indispensable avant utilisation

Ce dossier contient le **code Dart** (`lib/`, `pubspec.yaml`) et un
`AndroidManifest.xml` de référence, mais **pas** le squelette natif complet
Android/iOS (fichiers Gradle, Xcode, icônes...), qui ne peut être généré que
par l'outil `flutter create` — non exécutable dans l'environnement où ce
projet a été rédigé (pas d'accès à `pub.dev` ni au SDK Flutter, vérifié à
nouveau, y compris via `apt`).

**Pour démarrer**, sur une machine avec Flutter installé :

```bash
# 1. Générer un projet Flutter vierge à côté de celui-ci
flutter create sgcpc_mobile_scaffold

# 2. Copier le code métier dans le projet généré
cp -r sgcpc_mobile/lib/*        sgcpc_mobile_scaffold/lib/
cp    sgcpc_mobile/pubspec.yaml sgcpc_mobile_scaffold/pubspec.yaml
# Fusionner les permissions de sgcpc_mobile/android/app/src/main/AndroidManifest.xml
# dans celui généré par `flutter create` (ne pas écraser, juste ajouter les
# balises <uses-permission> et les attributs de <application>)

cd sgcpc_mobile_scaffold
flutter pub get
flutter run
```

### Ce qui a été fait pour compenser l'absence de compilateur

N'ayant pas accès à `flutter analyze` ni `flutter run`, une **relecture
manuelle complète, fichier par fichier**, a été effectuée : vérification de
la cohérence des accolades/parenthèses sur les 20 fichiers, et surtout
croisement systématique des signatures entre modèles, services, providers et
écrans. Cette relecture a permis de trouver et corriger 4 bugs réels :

1. **Message d'erreur de connexion illisible** — `EchecConnexionException`
   n'avait pas de `toString()`, donc tout échec de connexion aurait affiché
   littéralement `"Instance of 'EchecConnexionException'"` à l'agent au lieu
   du message utile ("Identifiant ou mot de passe incorrect").
2. **Session expirée jamais détectée** — la classe `SessionExpireeException`
   était déclarée et documentée, mais jamais réellement levée. Un agent dont
   le refresh token expire après 7 jours de terrain n'aurait eu aucune
   indication qu'il doit se reconnecter ; l'app aurait simplement cessé de
   synchroniser silencieusement. Le circuit complet a été implémenté :
   distinction entre "refresh échoué par coupure réseau" (on ne déconnecte
   pas) et "refresh explicitement rejeté par le serveur" (on déconnecte et
   redirige vers l'écran de connexion), avec gestion dans les deux écrans
   concernés sans perte du dossier en cours de saisie.
3. **Timeout réseau mal classé** — un dépassement du délai de 15s (fréquent
   en zone rurale à connectivité instable, exactement le scénario du CDCF)
   était traité comme un échec définitif de synchronisation plutôt que comme
   une simple absence de réseau à réessayer automatiquement.
4. **Statut de synchronisation calculé mais jamais affiché** — la carte de
   liste des dossiers calculait un texte de statut ("En attente de
   synchronisation", "Échec"...) sans jamais l'afficher à l'écran.

Un point vérifié par recherche externe plutôt que par mémoire : l'usage de
`DropdownButtonFormField(initialValue: ...)` plutôt que l'ancien paramètre
`value` — confirmé correct pour Flutter ≥ 3.35 (le paramètre `value` est
déprécié mais reste fonctionnel en dessous de cette version).

**Il reste malgré tout un risque réel de petites erreurs de compilation**
(imports, typos) qu'une relecture humaine ne peut pas garantir à 100% —
contrairement au backend Django, testé en direct sur un vrai serveur.

## Configuration de l'URL du serveur

Par défaut, l'app pointe vers `http://10.0.2.2:8000/api/v1` (10.0.2.2 = alias
de `localhost` de votre machine depuis un émulateur Android). À adapter :

```bash
# Appareil physique sur le même réseau que le serveur Django
flutter run --dart-define=API_BASE_URL=http://192.168.1.X:8000/api/v1

# Serveur de production
flutter run --dart-define=API_BASE_URL=https://sgcpc.transports.gouv.ne/api/v1
```

## Architecture — mode hors-ligne ("offline-first")

C'est la pièce centrale de cette application, en réponse directe au risque
« Coupures d'électricité/internet » identifié dans le CDCF (section 8) :

```
Saisie de l'agent
      │
      ▼
┌─────────────────────────┐
│  1. Écriture LOCALE      │  ← TOUJOURS, avant même de vérifier le réseau
│     (SQLite, table       │     (local_database.dart)
│      "dossiers")         │
└─────────────────────────┘
      │
      ▼
┌─────────────────────────┐
│  2. Réseau disponible ?  │
└─────────────────────────┘
      │ oui                          │ non
      ▼                              ▼
┌─────────────────┐          ┌──────────────────────┐
│ Tentative        │          │ Reste en file        │
│ d'envoi immédiat │          │ d'attente locale      │
│ à l'API          │          │ (statut "EN_ATTENTE") │
└─────────────────┘          └──────────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────────┐
                          │ ConnectivityService détecte  │
                          │ le retour du réseau           │
                          │  → synchronisation automatique│
                          │    de TOUS les dossiers en    │
                          │    attente                    │
                          └─────────────────────────────┘
```

L'agent voit à tout moment, via la bannière en haut de l'écran, s'il est
hors-ligne et combien de dossiers restent à transmettre. **Aucune saisie
n'est jamais perdue**, même en cas de coupure au milieu de la saisie (le
formulaire n'écrit qu'à la validation finale, mais l'écriture SQLite est
atomique et ne dépend d'aucun appel réseau).

## Structure du projet

```
lib/
  core/constants.dart            Config API, rôles, types (miroir du backend Django)
  models/                        Dossier, Conducteur, Vehicule, Utilisateur
  services/
    token_storage.dart           Stockage sécurisé JWT (Keystore/Keychain)
    api_client.dart              Client HTTP + refresh automatique du token
    auth_service.dart            Connexion / déconnexion
    local_database.dart          SQLite : cache + file d'attente hors-ligne
    connectivity_service.dart    Détection réseau
    dossier_service.dart         Orchestration création + synchronisation
  providers/                     État de l'app (package provider)
  screens/
    login_screen.dart
    home_screen.dart             Liste des dossiers + bannière de statut
    nouveau_dossier_screen.dart  Formulaire de saisie terrain (Module 1)
    dossier_detail_screen.dart
  widgets/                       Composants réutilisables
```

## Fonctionnalités couvertes

- ✅ Connexion JWT (rôle embarqué dans le token, pas d'appel réseau superflu)
- ✅ Saisie complète Module 1 (conducteur, véhicule, circonstances, photos)
- ✅ Fonctionnement 100% hors-ligne avec file d'attente et synchronisation auto
- ✅ Liste des dossiers avec indicateur de statut de synchronisation
- ✅ Détail d'un dossier

## Ce qu'il reste à faire

1. **Corriger les erreurs de compilation** résiduelles (voir avertissement ci-dessus)
2. **Upload des photos** : le formulaire les capture et les garde en local
   (`photosLocales`), mais l'appel `POST /dossiers/{id}/pieces/` pour les
   envoyer réellement au serveur après création du dossier n'est pas encore
   branché — à faire dans `dossier_service.dart`
3. **Écrans Modules 2-5** pour les rôles Administration/Commission (vérification,
   auditions, décisions, restitution) — non prioritaires sur mobile selon le
   CDCF, qui les situe plutôt côté web, mais possibles si besoin
4. **Icônes et splash screen** (générés par `flutter create`, à personnaliser)
5. **Tests** : `flutter test` (widget tests) et tests d'intégration
6. **Build de production** : `flutter build apk --release` /
   `flutter build ios --release`, signature de l'application

## Comptes de test (backend Django)

Utiliser les mêmes comptes que pour l'application web — voir le README du
projet `sgcpc` (backend), section "Créer des utilisateurs de test". Un
compte `AGENT_POLICE` ou `GENDARME` est nécessaire pour créer un dossier.
