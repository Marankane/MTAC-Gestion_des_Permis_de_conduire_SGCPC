/// Configuration de l'application — SGCPC mobile.
class ApiConfig {
  /// URL de base de l'API Django.
  /// En développement, l'émulateur Android utilise 10.0.2.2 pour joindre le
  /// "localhost" de la machine hôte ; un appareil physique doit utiliser
  /// l'adresse IP du serveur sur le réseau local ou l'URL de production.
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  static const String tokenEndpoint = '$baseUrl/auth/token/';
  static const String tokenRefreshEndpoint = '$baseUrl/auth/token/refresh/';
  static const String profilEndpoint = '$baseUrl/auth/profil/';
  static const String dossiersEndpoint = '$baseUrl/dossiers/';
  static const String verificationPermisEndpoint = '$baseUrl/permis/verifier/';

  static const Duration timeout = Duration(seconds: 15);
}

/// Rôles métier — doivent rester synchronisés avec comptes/models.py (Django).
class Roles {
  static const agentPolice = 'AGENT_POLICE';
  static const gendarme = 'GENDARME';
  static const adminRegional = 'ADMIN_REGIONAL';
  static const secretaireCommission = 'SECRETAIRE_COMMISSION';
  static const membreCommission = 'MEMBRE_COMMISSION';
  static const adminSysteme = 'ADMIN_SYSTEME';

  static bool estForceDeLOrdre(String? role) =>
      role == agentPolice || role == gendarme;
}

class TypesIncident {
  static const corporel = 'CORPOREL';
  static const materiel = 'MATERIEL';
  static const delitFuite = 'DELIT_FUITE';
  static const autre = 'AUTRE';

  static const Map<String, String> libelles = {
    corporel: 'Accident corporel',
    materiel: 'Accident matériel',
    delitFuite: 'Délit de fuite',
    autre: 'Autre infraction grave',
  };
}

class TypesVehicule {
  static const voiture = 'VOITURE';
  static const camion = 'CAMION';
  static const moto = 'MOTO';
  static const autre = 'AUTRE';

  static const Map<String, String> libelles = {
    voiture: 'Voiture',
    camion: 'Camion',
    moto: 'Moto',
    autre: 'Autre',
  };
}

class TypesPermis {
  static const a = 'A';
  static const bc = 'BC';
  static const d = 'D';
  static const e = 'E';
  static const f = 'F';

  static const Map<String, String> libelles = {
    a: 'A',
    bc: 'BC',
    d: 'D',
    e: 'E',
    f: 'F',
  };
}

/// Statut de synchronisation d'un dossier créé localement.
class StatutSync {
  static const enAttente = 'EN_ATTENTE';
  static const enCours = 'EN_COURS';
  static const synchronise = 'SYNCHRONISE';
  static const echec = 'ECHEC';
}
