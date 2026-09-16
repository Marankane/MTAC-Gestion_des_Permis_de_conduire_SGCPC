import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../core/constants.dart';
import '../models/conducteur.dart';
import '../models/dossier.dart';
import '../models/vehicule.dart';
import '../providers/dossier_provider.dart';
import '../services/api_client.dart';
import '../services/dossier_service.dart';

const orangeNiger = Color(0xFFE05206);

/// Module 1 du CDCF : saisie d'un accident/incident par la Police/Gendarmerie.
/// Conçu pour fonctionner immédiatement, réseau ou pas : la validation et
/// l'enregistrement local se font sans jamais dépendre d'un appel réseau.
class NouveauDossierScreen extends StatefulWidget {
  const NouveauDossierScreen({super.key});

  @override
  State<NouveauDossierScreen> createState() => _NouveauDossierScreenState();
}

class _NouveauDossierScreenState extends State<NouveauDossierScreen> {
  final _formKey = GlobalKey<FormState>();
  final _picker = ImagePicker();

  // Conducteur
  final _nomCtrl = TextEditingController();
  final _prenomCtrl = TextEditingController();
  final _permisCtrl = TextEditingController();
  final _mentionPermisCtrl = TextEditingController();
  final _telephoneCtrl = TextEditingController();
  DateTime? _dateNaissance;
  String _typePermis = TypesPermis.a;

  // Véhicule
  final _marqueCtrl = TextEditingController();
  final _modeleCtrl = TextEditingController();
  final _plaqueCtrl = TextEditingController();
  String _typeVehicule = TypesVehicule.voiture;

  // Incident
  DateTime _dateIncident = DateTime.now();
  final _villeCtrl = TextEditingController();
  final _quartierCtrl = TextEditingController();
  String _typeIncident = TypesIncident.corporel;
  bool _vitesseExcessive = false;
  bool _alcool = false;
  bool _stupefiants = false;
  bool _feuRouge = false;
  final _circonstancesCtrl = TextEditingController();
  final _blessesCtrl = TextEditingController(text: '0');
  final _decesCtrl = TextEditingController(text: '0');

  final List<XFile> _photos = [];
  bool _enregistrement = false;

  @override
  void dispose() {
    for (final c in [
      _nomCtrl,
      _prenomCtrl,
      _permisCtrl,
      _mentionPermisCtrl,
      _telephoneCtrl,
      _marqueCtrl,
      _modeleCtrl,
      _plaqueCtrl,
      _villeCtrl,
      _quartierCtrl,
      _circonstancesCtrl,
      _blessesCtrl,
      _decesCtrl,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _prendrePhoto() async {
    final image =
        await _picker.pickImage(source: ImageSource.camera, imageQuality: 80);
    if (image != null) setState(() => _photos.add(image));
  }

  Future<void> _choisirDateNaissance() async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime(1990),
      firstDate: DateTime(1920),
      lastDate: DateTime.now(),
    );
    if (date != null) setState(() => _dateNaissance = date);
  }

  Future<void> _enregistrer() async {
    if (!_formKey.currentState!.validate()) return;
    if (_dateNaissance == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text(
                "Veuillez renseigner la date de naissance du conducteur.")),
      );
      return;
    }

    setState(() => _enregistrement = true);

    final dossier = Dossier(
      localId: '', // remplacé par le service
      dateIncident: _dateIncident,
      ville: _villeCtrl.text.trim(),
      quartier: _quartierCtrl.text.trim(),
      typeIncident: _typeIncident,
      vitesseExcessive: _vitesseExcessive,
      alcool: _alcool,
      stupefiants: _stupefiants,
      feuRouge: _feuRouge,
      autresCirconstances: _circonstancesCtrl.text.trim(),
      nombreBlesses: int.tryParse(_blessesCtrl.text) ?? 0,
      nombreDeces: int.tryParse(_decesCtrl.text) ?? 0,
      conducteur: Conducteur(
        nom: _nomCtrl.text.trim(),
        prenom: _prenomCtrl.text.trim(),
        dateNaissance:
            '${_dateNaissance!.year.toString().padLeft(4, '0')}-${_dateNaissance!.month.toString().padLeft(2, '0')}-${_dateNaissance!.day.toString().padLeft(2, '0')}',
        numeroPermis: _permisCtrl.text.trim(),
        mentionPermis: _mentionPermisCtrl.text.trim(),
        typePermis: _typePermis,
        telephone: _telephoneCtrl.text.trim(),
      ),
      vehicule: Vehicule(
        marque: _marqueCtrl.text.trim(),
        modele: _modeleCtrl.text.trim(),
        plaque: _plaqueCtrl.text.trim(),
        typeVehicule: _typeVehicule,
      ),
      creeLe: DateTime.now(),
      photosLocales: _photos.map((p) => p.path).toList(),
    );

    ResultatCreationDossier resultat;
    try {
      resultat = await context.read<DossierProvider>().creerDossier(dossier);
    } on SessionExpireeException {
      // Le dossier a déjà été écrit en local par DossierService AVANT la
      // tentative de synchronisation qui a révélé l'expiration : rien n'est
      // perdu. On informe simplement l'agent et on revient à l'accueil, où
      // HomeScreen se charge de la redirection vers la connexion.
      if (!mounted) return;
      setState(() => _enregistrement = false);
      await showDialog(
        context: context,
        builder: (_) => AlertDialog(
          icon: const Icon(Icons.cloud_off, color: Colors.orange, size: 40),
          title: const Text("Enregistré localement"),
          content: const Text(
            "Le dossier a bien été enregistré sur l'appareil, mais votre "
            "session a expiré. Reconnectez-vous pour qu'il soit transmis.",
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text("OK")),
          ],
        ),
      );
      if (!mounted) return;
      Navigator.of(context).pop();
      return;
    }

    if (!mounted) return;
    setState(() => _enregistrement = false);

    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        icon: Icon(
          resultat.synchroniseImmediatement
              ? Icons.check_circle
              : Icons.cloud_off,
          color:
              resultat.synchroniseImmediatement ? Colors.green : Colors.orange,
          size: 40,
        ),
        title: Text(resultat.synchroniseImmediatement
            ? "Dossier transmis"
            : "Enregistré localement"),
        content: Text(resultat.message),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(); // ferme le dialogue
              Navigator.of(context).pop(); // retourne à la liste
            },
            child: const Text("OK"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Nouvelle saisie"),
        backgroundColor: orangeNiger,
        foregroundColor: Colors.white,
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const _SectionTitre("1. Conducteur"),
            TextFormField(
              controller: _nomCtrl,
              decoration: const InputDecoration(
                  labelText: "Nom", border: OutlineInputBorder()),
              validator: _requis,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _prenomCtrl,
              decoration: const InputDecoration(
                  labelText: "Prénom", border: OutlineInputBorder()),
              validator: _requis,
            ),
            const SizedBox(height: 12),
            InkWell(
              onTap: _choisirDateNaissance,
              child: InputDecorator(
                decoration: const InputDecoration(
                    labelText: "Date de naissance",
                    border: OutlineInputBorder()),
                child: Text(_dateNaissance == null
                    ? "Sélectionner..."
                    : "${_dateNaissance!.day}/${_dateNaissance!.month}/${_dateNaissance!.year}"),
              ),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _permisCtrl,
              decoration: const InputDecoration(
                  labelText: "N° de permis", border: OutlineInputBorder()),
              validator: _requis,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _mentionPermisCtrl,
              decoration: const InputDecoration(
                  labelText: "Mention du permis", border: OutlineInputBorder()),
              validator: _requis,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _typePermis,
              decoration: const InputDecoration(
                  labelText: "Type de permis", border: OutlineInputBorder()),
              items: TypesPermis.libelles.entries
                  .map((e) =>
                      DropdownMenuItem(value: e.key, child: Text(e.value)))
                  .toList(),
              onChanged: (v) => setState(() => _typePermis = v!),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _telephoneCtrl,
              decoration: const InputDecoration(
                  labelText: "Téléphone", border: OutlineInputBorder()),
              keyboardType: TextInputType.phone,
              validator: _requis,
            ),
            const SizedBox(height: 24),
            const _SectionTitre("2. Véhicule"),
            Row(children: [
              Expanded(
                child: TextFormField(
                  controller: _marqueCtrl,
                  decoration: const InputDecoration(
                      labelText: "Marque", border: OutlineInputBorder()),
                  validator: _requis,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _modeleCtrl,
                  decoration: const InputDecoration(
                      labelText: "Modèle", border: OutlineInputBorder()),
                  validator: _requis,
                ),
              ),
            ]),
            const SizedBox(height: 12),
            TextFormField(
              controller: _plaqueCtrl,
              decoration: const InputDecoration(
                  labelText: "Plaque d'immatriculation",
                  border: OutlineInputBorder()),
              validator: _requis,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _typeVehicule,
              decoration: const InputDecoration(
                  labelText: "Type de véhicule", border: OutlineInputBorder()),
              items: TypesVehicule.libelles.entries
                  .map((e) =>
                      DropdownMenuItem(value: e.key, child: Text(e.value)))
                  .toList(),
              onChanged: (v) => setState(() => _typeVehicule = v!),
            ),
            const SizedBox(height: 24),
            const _SectionTitre("3. Circonstances"),
            InkWell(
              onTap: () async {
                final date = await showDatePicker(
                  context: context,
                  initialDate: _dateIncident,
                  firstDate: DateTime(2020),
                  lastDate: DateTime.now(),
                );
                if (date == null) return;
                if (!context.mounted) return;
                final heure = await showTimePicker(
                  context: context,
                  initialTime: TimeOfDay.fromDateTime(_dateIncident),
                );
                setState(() {
                  _dateIncident = DateTime(
                    date.year,
                    date.month,
                    date.day,
                    heure?.hour ?? _dateIncident.hour,
                    heure?.minute ?? _dateIncident.minute,
                  );
                });
              },
              child: InputDecorator(
                decoration: const InputDecoration(
                    labelText: "Date et heure de l'incident",
                    border: OutlineInputBorder()),
                child: Text(
                  "${_dateIncident.day}/${_dateIncident.month}/${_dateIncident.year} ${_dateIncident.hour.toString().padLeft(2, '0')}:${_dateIncident.minute.toString().padLeft(2, '0')}",
                ),
              ),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _villeCtrl,
              decoration: const InputDecoration(
                  labelText: "Ville", border: OutlineInputBorder()),
              validator: _requis,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _quartierCtrl,
              decoration: const InputDecoration(
                  labelText: "Quartier (optionnel)",
                  border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _typeIncident,
              decoration: const InputDecoration(
                  labelText: "Type d'incident", border: OutlineInputBorder()),
              items: TypesIncident.libelles.entries
                  .map((e) =>
                      DropdownMenuItem(value: e.key, child: Text(e.value)))
                  .toList(),
              onChanged: (v) => setState(() => _typeIncident = v!),
            ),
            const SizedBox(height: 8),
            Wrap(spacing: 8, children: [
              FilterChip(
                  label: const Text("Alcool"),
                  selected: _alcool,
                  onSelected: (v) => setState(() => _alcool = v)),
              FilterChip(
                  label: const Text("Stupéfiants"),
                  selected: _stupefiants,
                  onSelected: (v) => setState(() => _stupefiants = v)),
              FilterChip(
                  label: const Text("Vitesse excessive"),
                  selected: _vitesseExcessive,
                  onSelected: (v) => setState(() => _vitesseExcessive = v)),
              FilterChip(
                  label: const Text("Feu rouge"),
                  selected: _feuRouge,
                  onSelected: (v) => setState(() => _feuRouge = v)),
            ]),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(
                child: TextFormField(
                  controller: _blessesCtrl,
                  decoration: const InputDecoration(
                      labelText: "Nb blessés", border: OutlineInputBorder()),
                  keyboardType: TextInputType.number,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _decesCtrl,
                  decoration: const InputDecoration(
                      labelText: "Nb décès", border: OutlineInputBorder()),
                  keyboardType: TextInputType.number,
                ),
              ),
            ]),
            const SizedBox(height: 12),
            TextFormField(
              controller: _circonstancesCtrl,
              decoration: const InputDecoration(
                  labelText: "Autres circonstances",
                  border: OutlineInputBorder()),
              maxLines: 3,
            ),
            const SizedBox(height: 24),
            const _SectionTitre("4. Photos (permis, carte grise, dégâts...)"),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ..._photos.map((p) => ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.file(File(p.path),
                          width: 80, height: 80, fit: BoxFit.cover),
                    )),
                InkWell(
                  onTap: _prendrePhoto,
                  child: Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.grey.shade400),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.add_a_photo_outlined,
                        color: Colors.grey),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              icon: _enregistrement
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.save),
              label: Text(_enregistrement
                  ? "Enregistrement..."
                  : "Enregistrer et confisquer le permis"),
              style: ElevatedButton.styleFrom(
                backgroundColor: orangeNiger,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              onPressed: _enregistrement ? null : _enregistrer,
            ),
            const SizedBox(height: 8),
            const Text(
              "Ce dossier sera enregistré même sans connexion réseau, puis transmis "
              "automatiquement dès que possible.",
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  String? _requis(String? v) =>
      (v == null || v.trim().isEmpty) ? "Champ requis" : null;
}

class _SectionTitre extends StatelessWidget {
  final String texte;
  const _SectionTitre(this.texte);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        texte,
        style: const TextStyle(
            fontSize: 16, fontWeight: FontWeight.bold, color: orangeNiger),
      ),
    );
  }
}
