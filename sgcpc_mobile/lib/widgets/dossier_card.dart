import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../core/constants.dart';
import '../models/dossier.dart';

class DossierCard extends StatelessWidget {
  final Dossier dossier;
  final VoidCallback? onTap;

  const DossierCard({super.key, required this.dossier, this.onTap});

  @override
  Widget build(BuildContext context) {
    final formatDate = DateFormat('dd/MM/yyyy HH:mm');
    final (couleurStatut, texteStatut, icone) = switch (dossier.statutSync) {
      StatutSync.synchronise => (
          Colors.green,
          dossier.statutServeur ?? 'Synchronisé',
          Icons.check_circle
        ),
      StatutSync.echec => (Colors.red, 'Échec de synchronisation', Icons.error),
      _ => (Colors.orange, 'En attente de synchronisation', Icons.schedule),
    };

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: couleurStatut.withValues(alpha: 0.15),
          child: Icon(icone, color: couleurStatut, size: 20),
        ),
        title: Text(
          dossier.identifiantAffiche,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${dossier.conducteur.prenom} ${dossier.conducteur.nom}'),
            Text(
              '${TypesIncident.libelles[dossier.typeIncident] ?? dossier.typeIncident} · ${formatDate.format(dossier.dateIncident)}',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
            if (!dossier.estSynchronise)
              Text(
                texteStatut,
                style: TextStyle(
                    fontSize: 11,
                    color: couleurStatut,
                    fontWeight: FontWeight.w600),
              ),
          ],
        ),
        trailing: Icon(Icons.chevron_right, color: Colors.grey.shade400),
        isThreeLine: true,
      ),
    );
  }
}
