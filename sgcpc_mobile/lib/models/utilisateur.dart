class Utilisateur {
  final int id;
  final String username;
  final String firstName;
  final String lastName;
  final String role;
  final String roleDisplay;
  final String region;
  final String telephone;

  Utilisateur({
    required this.id,
    required this.username,
    required this.firstName,
    required this.lastName,
    required this.role,
    required this.roleDisplay,
    required this.region,
    required this.telephone,
  });

  String get nomComplet =>
      (firstName.isNotEmpty || lastName.isNotEmpty) ? '$firstName $lastName'.trim() : username;

  factory Utilisateur.fromJson(Map<String, dynamic> json) {
    return Utilisateur(
      id: json['id'],
      username: json['username'] ?? '',
      firstName: json['first_name'] ?? '',
      lastName: json['last_name'] ?? '',
      role: json['role'] ?? '',
      roleDisplay: json['role_display'] ?? '',
      region: json['region'] ?? '',
      telephone: json['telephone'] ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'username': username,
        'first_name': firstName,
        'last_name': lastName,
        'role': role,
        'role_display': roleDisplay,
        'region': region,
        'telephone': telephone,
      };
}
