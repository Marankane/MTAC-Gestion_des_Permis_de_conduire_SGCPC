import 'dart:async';
import 'package:flutter/foundation.dart';

import '../models/dossier.dart';
import '../services/api_client.dart';
import '../services/connectivity_service.dart';
import '../services/dossier_service.dart';

class DossierProvider extends ChangeNotifier {
  final DossierService _dossierService;
  final ConnectivityService _connectivityService;

  DossierProvider(this._dossierService, this._connectivityService) {
    _ecouterConnectivite();
  }

  List<Dossier> dossiers = [];
  int enAttenteSync = 0;
  bool horsLigne = false;
  bool chargement = false;

  /// true si le refresh token a expiré ou été révoqué : l'écran doit renvoyer
  /// l'agent à la connexion. Les dossiers déjà en file d'attente locale restent
  /// intacts et seront transmis dès la reconnexion (cf. DossierService).
  bool sessionExpiree = false;

  StreamSubscription<bool>? _sub;

  void _ecouterConnectivite() {
    _sub = _connectivityService.surChangementConnexion.listen((connecte) async {
      horsLigne = !connecte;
      notifyListeners();
      if (connecte) {
        await synchroniser();
      }
    });
  }

  Future<void> charger() async {
    chargement = true;
    notifyListeners();
    dossiers = await _dossierService.listerDossiersLocaux();
    enAttenteSync = await _dossierService.compterEnAttente();
    horsLigne = !(await _connectivityService.estConnecte());
    chargement = false;
    notifyListeners();
  }

  Future<ResultatCreationDossier> creerDossier(Dossier dossier) async {
    try {
      final resultat = await _dossierService.creerDossier(dossier);
      await charger();
      return resultat;
    } on SessionExpireeException {
      sessionExpiree = true;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> synchroniser() async {
    try {
      await _dossierService.synchroniserEnAttente();
    } on SessionExpireeException {
      sessionExpiree = true;
      notifyListeners();
    }
    await charger();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }
}
