class PermisVerification {
  final String codeQr;
  final String nom;
  final String prenom;
  final String dateNaissance;
  final String lieuNaissance;
  final String numeroPermis;
  final String mentionPermis;
  final String typePermis;
  final String statutPermis;
  final String? dateDelivrance;
  final String? dateExpiration;
  final String? dateSuspension;

  PermisVerification.fromJson(Map<String, dynamic> json)
      : codeQr = json['code_qr'] ?? '',
        nom = json['nom'] ?? '',
        prenom = json['prenom'] ?? '',
        dateNaissance = json['date_naissance'] ?? '',
        lieuNaissance = json['lieu_naissance'] ?? '',
        numeroPermis = json['numero_permis'] ?? '',
        mentionPermis = json['mention_permis'] ?? '',
        typePermis = json['type_permis'] ?? '',
        statutPermis = json['statut_permis'] ?? '',
        dateDelivrance = json['date_delivrance'],
        dateExpiration = json['date_expiration'],
        dateSuspension = json['date_suspension'];
}
