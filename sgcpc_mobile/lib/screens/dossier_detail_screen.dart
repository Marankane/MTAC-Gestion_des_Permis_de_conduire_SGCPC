import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../core/constants.dart';
import '../models/dossier.dart';
import '../widgets/app_background.dart';

const orangeNiger = Color(0xFFE05206);

class DossierDetailScreen extends StatelessWidget {
  final Dossier dossier;
  const DossierDetailScreen({super.key, required this.dossier});

  @override
  Widget build(BuildContext context) {
    final formatDate = DateFormat('dd/MM/yyyy HH:mm');

    return Scaffold(
      appBar: AppBar(
        title: Text(dossier.identifiantAffiche),
        backgroundColor: orangeNiger,
        foregroundColor: Colors.white,
      ),
      body: AppBackground(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (!dossier.estSynchronise)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: dossier.statutSync == StatutSync.echec
                      ? Colors.red.shade50
                      : Colors.orange.shade50,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      dossier.statutSync == StatutSync.echec
                          ? Icons.error_outline
                          : Icons.cloud_off,
                      color: dossier.statutSync == StatutSync.echec
                          ? Colors.red
                          : Colors.orange,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        dossier.statutSync == StatutSync.echec
                            ? "Échec de synchronisation : ${dossier.erreurSync ?? 'erreur inconnue'}"
                            : "Ce dossier n'est pas encore transmis au serveur. Il sera envoyé "
                                "automatiquement dès que la connexion sera disponible.",
                        style: const TextStyle(fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            _Carte(
              titre: "Conducteur",
              enfants: [
                _Ligne("Nom complet",
                    "${dossier.conducteur.prenom} ${dossier.conducteur.nom}"),
                _Ligne("N° de permis", dossier.conducteur.numeroPermis),
                _Ligne("Mention", dossier.conducteur.mentionPermis),
                _Ligne("Type", dossier.conducteur.typePermis),
                if (dossier.conducteur.codeQr.isNotEmpty)
                  _Ligne("Code QR", dossier.conducteur.codeQr),
                _Ligne("Téléphone", dossier.conducteur.telephone),
              ],
            ),
            _Carte(
              titre: "Véhicule",
              enfants: [
                _Ligne("Véhicule",
                    "${dossier.vehicule.marque} ${dossier.vehicule.modele}"),
                _Ligne("Plaque", dossier.vehicule.plaque),
                _Ligne(
                    "Type",
                    TypesVehicule.libelles[dossier.vehicule.typeVehicule] ??
                        dossier.vehicule.typeVehicule),
              ],
            ),
            _Carte(
              titre: "Circonstances",
              enfants: [
                _Ligne(
                    "Type d'incident",
                    TypesIncident.libelles[dossier.typeIncident] ??
                        dossier.typeIncident),
                _Ligne("Date", formatDate.format(dossier.dateIncident)),
                _Ligne("Lieu", "${dossier.ville} ${dossier.quartier}".trim()),
                _Ligne("Blessés / Décès",
                    "${dossier.nombreBlesses} / ${dossier.nombreDeces}"),
                if (dossier.autresCirconstances.isNotEmpty)
                  _Ligne("Détails", dossier.autresCirconstances),
                Wrap(spacing: 6, runSpacing: 6, children: [
                  if (dossier.alcool) const _Badge("Alcool"),
                  if (dossier.stupefiants) const _Badge("Stupéfiants"),
                  if (dossier.vitesseExcessive)
                    const _Badge("Vitesse excessive"),
                  if (dossier.feuRouge) const _Badge("Feu rouge"),
                ]),
              ],
            ),
            if (dossier.statutServeur != null)
              _Carte(
                titre: "Statut administratif",
                enfants: [_Ligne("Statut", dossier.statutServeur!)],
              ),
          ],
        ),
      ),
    );
  }
}

class _Carte extends StatelessWidget {
  final String titre;
  final List<Widget> enfants;
  const _Carte({required this.titre, required this.enfants});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(titre,
                style: const TextStyle(
                    fontWeight: FontWeight.bold, color: orangeNiger)),
            const SizedBox(height: 8),
            ...enfants,
          ],
        ),
      ),
    );
  }
}

class _Ligne extends StatelessWidget {
  final String label;
  final String valeur;
  const _Ligne(this.label, this.valeur);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
              width: 120,
              child: Text(label,
                  style: const TextStyle(color: Colors.grey, fontSize: 13))),
          Expanded(child: Text(valeur, style: const TextStyle(fontSize: 13))),
        ],
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  final String texte;
  const _Badge(this.texte);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
          color: Colors.red.shade50, borderRadius: BorderRadius.circular(12)),
      child: Text(texte,
          style: TextStyle(color: Colors.red.shade700, fontSize: 11)),
    );
  }
}
