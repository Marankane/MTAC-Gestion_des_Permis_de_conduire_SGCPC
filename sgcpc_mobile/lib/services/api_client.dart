import 'dart:convert';
import 'package:http/http.dart' as http;

import '../core/constants.dart';
import 'token_storage.dart';

/// Exception levée quand le refresh token lui-même a expiré : il faut
/// renvoyer l'utilisateur à l'écran de connexion.
class SessionExpireeException implements Exception {}

/// Client HTTP centralisé : ajoute automatiquement le Bearer token et
/// tente un rafraîchissement transparent en cas de 401.
class ApiClient {
  final TokenStorage _tokenStorage;
  ApiClient(this._tokenStorage);

  Future<bool> get estSessionDemo async =>
      (await _tokenStorage.lireAccess()) == 'demo-access-token';

  Future<Map<String, String>> _headers({bool json = true}) async {
    final access = await _tokenStorage.lireAccess();
    return {
      if (json) 'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (access != null) 'Authorization': 'Bearer $access',
    };
  }

  Future<bool> _rafraichirToken() async {
    final refresh = await _tokenStorage.lireRefresh();
    if (refresh == null) return false;
    try {
      final response = await http
          .post(
            Uri.parse(ApiConfig.tokenRefreshEndpoint),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'refresh': refresh}),
          )
          .timeout(ApiConfig.timeout);
      // Une réponse a bien été reçue du serveur : qu'elle soit 200 ou 401,
      // ce n'est PAS un problème réseau — le serveur a tranché.
      _dernierRefreshAEchoueReseauSeul = false;
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        await _tokenStorage.mettreAJourAccess(data['access']);
        return true;
      }
    } catch (_) {
      // Aucune réponse reçue (pas de réseau, timeout...) : on ne peut pas
      // conclure que la session a expiré, seulement qu'on est hors-ligne.
      _dernierRefreshAEchoueReseauSeul = true;
    }
    return false;
  }

  /// Effectue une requête avec retry automatique après rafraîchissement du token
  /// en cas de 401. Lance [SessionExpireeException] si le rafraîchissement échoue
  /// alors qu'un token existe (refresh expiré ou révoqué) — l'appelant doit alors
  /// renvoyer l'utilisateur à l'écran de connexion. En l'absence totale de token
  /// (jamais connecté), ou en cas d'échec réseau pendant le refresh, la réponse
  /// 401 d'origine est simplement retournée telle quelle.
  Future<http.Response> _avecRetry(
      Future<http.Response> Function() requete) async {
    var response = await requete();
    if (response.statusCode == 401) {
      final avaitUnRefresh = await _tokenStorage.lireRefresh() != null;
      final rafraichi = await _rafraichirToken();
      if (rafraichi) {
        response = await requete();
      } else if (avaitUnRefresh) {
        // Un refresh token existait mais n'a pas permis de rafraîchir l'accès :
        // soit il a expiré (7 jours), soit il a été révoqué côté serveur.
        // On ne peut pas distinguer ce cas d'une simple coupure réseau ici,
        // donc on ne lève PAS l'exception si aucun réseau n'est disponible —
        // seul un 401 explicite du serveur de refresh (pas une exception réseau)
        // signale une vraie expiration. Voir _rafraichirToken.
        if (_dernierRefreshAEchoueReseauSeul != true) {
          throw SessionExpireeException();
        }
      }
    }
    return response;
  }

  /// true si le dernier appel à [_rafraichirToken] a échoué uniquement par
  /// absence de réseau (donc pas une vraie expiration de session).
  bool? _dernierRefreshAEchoueReseauSeul;

  Future<http.Response> get(String url) {
    return _avecRetry(() async {
      final headers = await _headers();
      return http
          .get(Uri.parse(url), headers: headers)
          .timeout(ApiConfig.timeout);
    });
  }

  Future<http.Response> post(String url, {Map<String, dynamic>? body}) {
    return _avecRetry(() async {
      final headers = await _headers();
      return http
          .post(Uri.parse(url),
              headers: headers, body: body != null ? jsonEncode(body) : null)
          .timeout(ApiConfig.timeout);
    });
  }

  /// Upload multipart (photos, PDF...).
  Future<http.StreamedResponse> uploadFichier(
    String url, {
    required String champFichier,
    required String cheminFichier,
    Map<String, String>? champs,
  }) async {
    final access = await _tokenStorage.lireAccess();
    final request = http.MultipartRequest('POST', Uri.parse(url));
    if (access != null) request.headers['Authorization'] = 'Bearer $access';
    if (champs != null) request.fields.addAll(champs);
    request.files
        .add(await http.MultipartFile.fromPath(champFichier, cheminFichier));
    return request.send();
  }
}
