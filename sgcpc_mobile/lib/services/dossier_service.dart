import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';

import '../core/constants.dart';
import '../models/dossier.dart';
import 'api_client.dart';
import 'connectivity_service.dart';
import 'local_database.dart';

/// Résultat de la création d'un dossier, pour informer clairement l'agent
/// sur le terrain de ce qui s'est réellement passé.
class ResultatCreationDossier {
  final Dossier dossier;
  final bool synchroniseImmediatement;
  final String message;
  ResultatCreationDossier(
      this.dossier, this.synchroniseImmediatement, this.message);
}

/// Orchestre la création et la synchronisation des dossiers (Module 1).
///
/// Principe "offline-first" : un dossier est TOUJOURS écrit en local d'abord.
/// Si le réseau est disponible, on tente une synchronisation immédiate ;
/// sinon (ou en cas d'échec), il reste en file d'attente pour [synchroniserEnAttente].
class DossierService {
  final ApiClient _apiClient;
  final LocalDatabase _localDb;
  final ConnectivityService _connectivity;
  final _uuid = const Uuid();

  DossierService(this._apiClient, this._localDb, this._connectivity);

  Future<bool> get estSessionDemo => _apiClient.estSessionDemo;

  Future<ResultatCreationDossier> creerDossier(Dossier dossierSansId) async {
    final dossier = dossierSansId.copyWith();
    final avecLocalId = Dossier(
      localId: _uuid.v4(),
      dateIncident: dossier.dateIncident,
      ville: dossier.ville,
      quartier: dossier.quartier,
      latitude: dossier.latitude,
      longitude: dossier.longitude,
      typeIncident: dossier.typeIncident,
      vitesseExcessive: dossier.vitesseExcessive,
      alcool: dossier.alcool,
      stupefiants: dossier.stupefiants,
      feuRouge: dossier.feuRouge,
      autresCirconstances: dossier.autresCirconstances,
      nombreBlesses: dossier.nombreBlesses,
      nombreDeces: dossier.nombreDeces,
      gravite: dossier.gravite,
      conducteur: dossier.conducteur,
      vehicule: dossier.vehicule,
      statutSync: StatutSync.enAttente,
      creeLe: DateTime.now(),
      photosLocales: dossier.photosLocales,
    );

    // 1. Toujours écrire en local d'abord — c'est la garantie qu'aucune saisie
    //    n'est perdue, même en cas de coupure réseau ou d'électricité.
    await _localDb.enregistrer(avecLocalId);

    // 2. Tentative de synchronisation immédiate si le réseau est disponible.
    // En mode démo, le token local n'est pas envoyé au serveur : on garde
    // toujours la saisie locale sans la marquer comme une erreur réseau.
    if (!await _apiClient.estSessionDemo && await _connectivity.estConnecte()) {
      final resultat = await _synchroniserUnDossier(avecLocalId);
      if (resultat != null) {
        return ResultatCreationDossier(
          resultat,
          true,
          "Dossier ${resultat.numero} créé et transmis avec succès.",
        );
      }
    }

    return ResultatCreationDossier(
      avecLocalId,
      false,
      "Dossier enregistré localement. Il sera transmis automatiquement dès "
      "que la connexion réseau sera rétablie.",
    );
  }

  /// Tente de synchroniser un dossier précis. Retourne le dossier mis à jour
  /// (avec numéro officiel) en cas de succès, null sinon.
  Future<Dossier?> _synchroniserUnDossier(Dossier dossier) async {
    try {
      final response = await _apiClient.post(ApiConfig.dossiersEndpoint,
          body: dossier.toApiJson());

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        final synchronise = dossier.copyWith(
          serverId: data['id'],
          numero: data['numero'],
          uuid: data['uuid'],
          statutServeur: data['statut'],
          statutSync: StatutSync.synchronise,
        );
        await _localDb.enregistrer(synchronise);
        return synchronise;
      }

      // Erreur de validation serveur (400) : on la garde pour affichage à l'agent,
      // mais on NE PERD PAS le dossier localement.
      final echec = dossier.copyWith(
        statutSync: StatutSync.echec,
        erreurSync:
            'Erreur serveur (${response.statusCode}) : ${response.body}',
      );
      await _localDb.enregistrer(echec);
      return null;
    } on http.ClientException {
      return null; // pas de réseau : reste en file d'attente, ce n'est pas une erreur métier
    } on TimeoutException {
      // Connexion trop lente/instable (fréquent en zone rurale) : on traite ce
      // cas comme "pas de réseau exploitable" plutôt que comme un échec définitif,
      // pour que le dossier soit ré-essayé automatiquement plus tard sans
      // afficher un message d'erreur alarmant à l'agent.
      return null;
    } on SessionExpireeException {
      // Ne PAS avaler cette exception dans un statut "échec" du dossier : elle
      // doit remonter jusqu'à l'écran pour renvoyer l'agent à la connexion.
      rethrow;
    } catch (e) {
      final echec = dossier.copyWith(
          statutSync: StatutSync.echec, erreurSync: e.toString());
      await _localDb.enregistrer(echec);
      return null;
    }
  }

  /// À appeler au retour de connexion et/ou périodiquement en arrière-plan.
  /// Retourne le nombre de dossiers effectivement synchronisés.
  Future<int> synchroniserEnAttente() async {
    if (await _apiClient.estSessionDemo) return 0;
    final enAttente = await _localDb.enAttenteDeSynchronisation();
    var reussis = 0;
    for (final dossier in enAttente) {
      final resultat = await _synchroniserUnDossier(dossier);
      if (resultat != null) reussis++;
    }
    return reussis;
  }

  Future<List<Dossier>> listerDossiersLocaux() => _localDb.tousLesDossiers();

  Future<int> compterEnAttente() => _localDb.compterEnAttente();
}
