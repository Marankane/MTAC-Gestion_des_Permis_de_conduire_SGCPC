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
  }
}
