import 'package:flutter/foundation.dart';

import '../models/utilisateur.dart';
import '../services/auth_service.dart';

enum EtatAuth { inconnu, connecte, deconnecte }

class AuthProvider extends ChangeNotifier {
  final AuthService _authService;
  AuthProvider(this._authService);

  EtatAuth etat = EtatAuth.inconnu;
  Utilisateur? utilisateur;
  String? erreur;
  bool enCours = false;

  Future<void> verifierSession() async {
    final connecte = await _authService.estConnecte();
    etat = connecte ? EtatAuth.connecte : EtatAuth.deconnecte;
    notifyListeners();
  }

  Future<bool> connexion(String username, String password) async {
    enCours = true;
    erreur = null;
    notifyListeners();
    try {
      utilisateur = await _authService.connexion(username, password);
      etat = EtatAuth.connecte;
      return true;
    } catch (e) {
      erreur = e.toString();
      return false;
    } finally {
      enCours = false;
      notifyListeners();
    }
  }

  Future<void> deconnexion() async {
    await _authService.deconnexion();
    utilisateur = null;
    etat = EtatAuth.deconnecte;
    notifyListeners();
  }
}
