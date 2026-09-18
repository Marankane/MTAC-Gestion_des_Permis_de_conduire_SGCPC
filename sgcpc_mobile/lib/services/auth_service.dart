import 'dart:convert';
import 'package:http/http.dart' as http;

import '../core/constants.dart';
import '../models/utilisateur.dart';
import 'token_storage.dart';

class EchecConnexionException implements Exception {
  final String message;
  EchecConnexionException(this.message);

  @override
  String toString() => message;
}

class AuthService {
  final TokenStorage _tokenStorage;
  AuthService(this._tokenStorage);

  /// Connexion : récupère les tokens JWT + le profil utilisateur en un seul appel
  /// (le token custom SGCPC embarque déjà le profil, cf. SGCPCTokenObtainPairSerializer).
  Future<Utilisateur> connexion(String username, String password) async {
    try {
      final response = await http
          .post(
            Uri.parse(ApiConfig.tokenEndpoint),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'username': username, 'password': password}),
          )
          .timeout(ApiConfig.timeout);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await _tokenStorage.sauvegarder(
            access: data['access'], refresh: data['refresh']);
        return Utilisateur.fromJson(data['utilisateur']);
      }
      if (response.statusCode == 401) {
        throw EchecConnexionException("Identifiant ou mot de passe incorrect.");
      }
      throw EchecConnexionException(
          "Erreur de connexion (code ${response.statusCode}).");
    } catch (error) {
      if (error is EchecConnexionException) rethrow;
      if (username == DemoConfig.username && password == DemoConfig.password) {
        await _tokenStorage.sauvegarder(
          access: 'demo-access-token',
          refresh: 'demo-refresh-token',
        );
        return Utilisateur(
          id: 0,
          username: DemoConfig.username,
          firstName: 'Utilisateur',
          lastName: 'Demo',
          role: Roles.agentPolice,
          roleDisplay: 'Agent de Police (démo hors-ligne)',
          region: 'Niamey',
          telephone: '',
        );
      }
      throw EchecConnexionException(
          "Impossible de joindre le serveur. Vérifiez votre connexion réseau.");
    }
  }

  Future<void> deconnexion() => _tokenStorage.effacer();

  Future<bool> estConnecte() async =>
      (await _tokenStorage.lireAccess()) != null;
}
