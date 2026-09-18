import 'dart:convert';
import 'package:http/http.dart' as http;

import '../core/constants.dart';
import '../models/permis_verification.dart';

class PermisIntrouvableException implements Exception {
  final String message;
  PermisIntrouvableException(this.message);

  @override
  String toString() => message;
}

class PermisService {
  Future<PermisVerification> verifier(
      {required String numero, required String mention}) async {
    try {
      final uri = Uri.parse(ApiConfig.verificationPermisEndpoint).replace(
        queryParameters: {'numero_permis': numero, 'mention_permis': mention},
      );
      final response = await http.get(uri,
          headers: {'Accept': 'application/json'}).timeout(ApiConfig.timeout);
      if (response.statusCode == 200) {
        return PermisVerification.fromJson(jsonDecode(response.body));
      }
      final detail =
          (jsonDecode(response.body) as Map<String, dynamic>)['detail'];
      throw PermisIntrouvableException(detail ?? 'Permis introuvable.');
    } catch (error) {
      if (error is PermisIntrouvableException ||
          numero != DemoConfig.numeroPermis ||
          mention != DemoConfig.mentionPermis) {
        rethrow;
      }
      return PermisVerification.fromJson({
        'code_qr': 'demo-permis-NY9028247-APN403850',
        'nom': 'Demo',
        'prenom': 'Utilisateur',
        'date_naissance': '1990-01-01',
        'lieu_naissance': 'Niamey',
        'numero_permis': DemoConfig.numeroPermis,
        'mention_permis': DemoConfig.mentionPermis,
        'type_permis': 'BC',
        'statut_permis': 'ACTIF',
        'date_delivrance': '2024-01-15',
        'date_expiration': '2034-01-15',
        'date_suspension': null,
      });
    }
  }
}
