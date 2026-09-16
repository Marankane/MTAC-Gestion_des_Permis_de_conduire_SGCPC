import 'dart:convert';

import 'conducteur.dart';
import 'vehicule.dart';
import '../core/constants.dart';

/// Représente un dossier de confiscation, qu'il soit :
/// - déjà synchronisé avec le serveur (id serveur + numéro officiel connus), ou
/// - encore local, en attente de connexion réseau (localId, pas encore de numéro).
class Dossier {
  final String localId; // UUID généré sur l'appareil, stable même hors-ligne
  final int? serverId; // id renvoyé par l'API une fois synchronisé
  final String? numero; // "Niger-2026-000123", null tant que non synchronisé
  final String? uuid; // uuid serveur (pour le QR code), null tant que non synchronisé

  final DateTime dateIncident;
  final String ville;
  final String quartier;
  final double? latitude;
  final double? longitude;
  final String typeIncident;

  final bool vitesseExcessive;
  final bool alcool;
  final bool stupefiants;
  final bool feuRouge;
  final String autresCirconstances;

  final int nombreBlesses;
  final int nombreDeces;
  final String gravite;

  final Conducteur conducteur;
  final Vehicule vehicule;

  final String? statutServeur; // "SAISI", "VERIFIE", etc. — connu seulement une fois synchronisé
  final String statutSync; // StatutSync.* — état LOCAL de synchronisation
  final String? erreurSync;
  final DateTime creeLe;

  /// Chemins locaux des photos prises sur le terrain, en attente d'upload.
  final List<String> photosLocales;

  Dossier({
    required this.localId,
    this.serverId,
    this.numero,
    this.uuid,
    required this.dateIncident,
    required this.ville,
    this.quartier = '',
    this.latitude,
    this.longitude,
    required this.typeIncident,
    this.vitesseExcessive = false,
    this.alcool = false,
    this.stupefiants = false,
    this.feuRouge = false,
    this.autresCirconstances = '',
    this.nombreBlesses = 0,
    this.nombreDeces = 0,
    this.gravite = '',
    required this.conducteur,
    required this.vehicule,
    this.statutServeur,
    this.statutSync = StatutSync.enAttente,
    this.erreurSync,
    required this.creeLe,
    this.photosLocales = const [],
  });

  bool get estSynchronise => statutSync == StatutSync.synchronise;

  String get identifiantAffiche => numero ?? '(en attente de synchronisation)';

  /// Payload exact attendu par POST /api/v1/dossiers/ (DossierCreateSerializer).
  Map<String, dynamic> toApiJson() => {
        'date_incident': dateIncident.toUtc().toIso8601String(),
        'ville': ville,
        'quartier': quartier,
        'latitude': latitude,
        'longitude': longitude,
        'type_incident': typeIncident,
        'vitesse_excessive': vitesseExcessive,
        'alcool': alcool,
        'stupefiants': stupefiants,
        'feu_rouge': feuRouge,
        'autres_circonstances': autresCirconstances,
        'nombre_blesses': nombreBlesses,
        'nombre_deces': nombreDeces,
        'gravite': gravite,
        'conducteur': conducteur.toJson(),
        'vehicule': vehicule.toJson(),
      };

  /// Sérialisation pour la table SQLite locale (file d'attente + cache).
  Map<String, dynamic> toDbMap() => {
        'local_id': localId,
        'server_id': serverId,
        'numero': numero,
        'uuid': uuid,
        'statut_serveur': statutServeur,
        'statut_sync': statutSync,
        'erreur_sync': erreurSync,
        'cree_le': creeLe.toIso8601String(),
        'photos_locales': jsonEncode(photosLocales),
        'payload_json': jsonEncode(toApiJson()),
      };

  factory Dossier.fromDbMap(Map<String, dynamic> map) {
    final payload = jsonDecode(map['payload_json'] as String) as Map<String, dynamic>;
    return Dossier(
      localId: map['local_id'] as String,
      serverId: map['server_id'] as int?,
      numero: map['numero'] as String?,
      uuid: map['uuid'] as String?,
      dateIncident: DateTime.parse(payload['date_incident']),
      ville: payload['ville'] ?? '',
      quartier: payload['quartier'] ?? '',
      latitude: (payload['latitude'] as num?)?.toDouble(),
      longitude: (payload['longitude'] as num?)?.toDouble(),
      typeIncident: payload['type_incident'] ?? '',
      vitesseExcessive: payload['vitesse_excessive'] ?? false,
      alcool: payload['alcool'] ?? false,
      stupefiants: payload['stupefiants'] ?? false,
      feuRouge: payload['feu_rouge'] ?? false,
      autresCirconstances: payload['autres_circonstances'] ?? '',
      nombreBlesses: payload['nombre_blesses'] ?? 0,
      nombreDeces: payload['nombre_deces'] ?? 0,
      gravite: payload['gravite'] ?? '',
      conducteur: Conducteur.fromJson(payload['conducteur']),
      vehicule: Vehicule.fromJson(payload['vehicule']),
      statutServeur: map['statut_serveur'] as String?,
      statutSync: map['statut_sync'] as String? ?? StatutSync.enAttente,
      erreurSync: map['erreur_sync'] as String?,
      creeLe: DateTime.parse(map['cree_le'] as String),
      photosLocales: (jsonDecode(map['photos_locales'] as String? ?? '[]') as List)
          .map((e) => e.toString())
          .toList(),
    );
  }

  factory Dossier.fromApiJson(Map<String, dynamic> json, {required String localId}) {
    return Dossier(
      localId: localId,
      serverId: json['id'],
      numero: json['numero'],
      uuid: json['uuid'],
      dateIncident: DateTime.parse(json['date_incident']),
      ville: json['ville'] ?? '',
      quartier: json['quartier'] ?? '',
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
      typeIncident: json['type_incident'] ?? '',
      vitesseExcessive: json['vitesse_excessive'] ?? false,
      alcool: json['alcool'] ?? false,
      stupefiants: json['stupefiants'] ?? false,
      feuRouge: json['feu_rouge'] ?? false,
      autresCirconstances: json['autres_circonstances'] ?? '',
      nombreBlesses: json['nombre_blesses'] ?? 0,
      nombreDeces: json['nombre_deces'] ?? 0,
      gravite: json['gravite'] ?? '',
      conducteur: Conducteur.fromJson(json['conducteur'] ?? {}),
      vehicule: Vehicule.fromJson(json['vehicule'] ?? {}),
      statutServeur: json['statut'],
      statutSync: StatutSync.synchronise,
      creeLe: DateTime.tryParse(json['date_saisie'] ?? '') ?? DateTime.now(),
    );
  }

  Dossier copyWith({
    int? serverId,
    String? numero,
    String? uuid,
    String? statutServeur,
    String? statutSync,
    String? erreurSync,
    List<String>? photosLocales,
  }) {
    return Dossier(
      localId: localId,
      serverId: serverId ?? this.serverId,
      numero: numero ?? this.numero,
      uuid: uuid ?? this.uuid,
      dateIncident: dateIncident,
      ville: ville,
      quartier: quartier,
      latitude: latitude,
      longitude: longitude,
      typeIncident: typeIncident,
      vitesseExcessive: vitesseExcessive,
      alcool: alcool,
      stupefiants: stupefiants,
      feuRouge: feuRouge,
      autresCirconstances: autresCirconstances,
      nombreBlesses: nombreBlesses,
      nombreDeces: nombreDeces,
      gravite: gravite,
      conducteur: conducteur,
      vehicule: vehicule,
      statutServeur: statutServeur ?? this.statutServeur,
      statutSync: statutSync ?? this.statutSync,
      erreurSync: erreurSync,
      creeLe: creeLe,
      photosLocales: photosLocales ?? this.photosLocales,
    );
  }
}
