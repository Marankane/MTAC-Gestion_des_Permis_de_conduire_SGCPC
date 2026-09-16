class Conducteur {
  final String codeQr;
  final String nom;
  final String prenom;
  final String dateNaissance; // format ISO yyyy-MM-dd
  final String numeroPermis;
  final String mentionPermis;
  final String typePermis;
  final String telephone;
  final String email;
  final String adresse;

  Conducteur({
    this.codeQr = '',
    required this.nom,
    required this.prenom,
    required this.dateNaissance,
    required this.numeroPermis,
    required this.mentionPermis,
    required this.typePermis,
    required this.telephone,
    this.email = '',
    this.adresse = '',
  });

  Map<String, dynamic> toJson() => {
        'code_qr': codeQr.isEmpty ? null : codeQr,
        'nom': nom,
        'prenom': prenom,
        'date_naissance': dateNaissance,
        'numero_permis': numeroPermis,
        'mention_permis': mentionPermis,
        'type_permis': typePermis,
        'telephone': telephone,
        'email': email,
        'adresse': adresse,
      };

  factory Conducteur.fromJson(Map<String, dynamic> json) => Conducteur(
        codeQr: json['code_qr'] ?? '',
        nom: json['nom'] ?? '',
        prenom: json['prenom'] ?? '',
        dateNaissance: json['date_naissance'] ?? '',
        numeroPermis: json['numero_permis'] ?? '',
        mentionPermis: json['mention_permis'] ?? '',
        typePermis: json['type_permis'] ?? '',
        telephone: json['telephone'] ?? '',
        email: json['email'] ?? '',
        adresse: json['adresse'] ?? '',
      );
}
