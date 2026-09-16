class Vehicule {
  final String marque;
  final String modele;
  final String plaque;
  final String typeVehicule;

  Vehicule({
    required this.marque,
    required this.modele,
    required this.plaque,
    required this.typeVehicule,
  });

  Map<String, dynamic> toJson() => {
        'marque': marque,
        'modele': modele,
        'plaque': plaque,
        'type_vehicule': typeVehicule,
      };

  factory Vehicule.fromJson(Map<String, dynamic> json) => Vehicule(
        marque: json['marque'] ?? '',
        modele: json['modele'] ?? '',
        plaque: json['plaque'] ?? '',
        typeVehicule: json['type_vehicule'] ?? '',
      );
}
