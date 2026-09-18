import 'package:flutter/material.dart';

/// Bannière visible en permanence indiquant si l'agent est hors-ligne et/ou
/// combien de dossiers restent à synchroniser. Essentiel pour la confiance
/// de l'agent terrain : il doit toujours savoir si sa saisie est "en sécurité"
/// localement ou déjà transmise à l'administration.
class SyncStatusBanner extends StatelessWidget {
  final bool horsLigne;
  final int enAttente;
  final bool modeDemo;
  final VoidCallback? onSynchroniserMaintenant;

  const SyncStatusBanner({
    super.key,
    required this.horsLigne,
    required this.enAttente,
    this.modeDemo = false,
    this.onSynchroniserMaintenant,
  });

  @override
  Widget build(BuildContext context) {
    final couleur = horsLigne
        ? Colors.red.shade50
        : enAttente > 0
            ? Colors.orange.shade50
            : Colors.green.shade50;
    final couleurTexte = horsLigne
        ? Colors.red.shade800
        : enAttente > 0
            ? Colors.orange.shade800
            : Colors.green.shade800;
    final icone = horsLigne
        ? Icons.cloud_off
        : enAttente > 0
            ? Icons.sync
            : Icons.cloud_done;

    final message = modeDemo
        ? (enAttente > 0
            ? "Mode démonstration — $enAttente dossier(s) sont enregistrés localement."
            : "Mode démonstration — les dossiers sont enregistrés localement.")
        : horsLigne
            ? (enAttente > 0
                ? "Hors ligne — $enAttente dossier(s) seront envoyés dès que la connexion sera rétablie."
                : "Hors ligne — les nouveaux dossiers seront enregistrés localement.")
            : enAttente > 0
                ? "Connexion rétablie — $enAttente dossier(s) en attente de synchronisation."
                : "Connexion rétablie — tous les dossiers sont synchronisés.";

    return Material(
      color: couleur,
      child: InkWell(
        onTap: (!horsLigne && enAttente > 0) ? onSynchroniserMaintenant : null,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          child: Row(
            children: [
              Icon(icone, size: 18, color: couleurTexte),
              const SizedBox(width: 8),
              Expanded(
                child: Text(message,
                    style: TextStyle(color: couleurTexte, fontSize: 13)),
              ),
              if (!horsLigne && enAttente > 0)
                Text("Synchroniser",
                    style: TextStyle(
                        color: couleurTexte,
                        fontWeight: FontWeight.bold,
                        fontSize: 13)),
            ],
          ),
        ),
      ),
    );
  }
}
