import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Stockage sécurisé des tokens JWT (chiffré : Keystore Android / Keychain iOS).
class TokenStorage {
  static const _storage = FlutterSecureStorage();
  static const _keyAccess = 'sgcpc_access_token';
  static const _keyRefresh = 'sgcpc_refresh_token';

  Future<void> sauvegarder({required String access, required String refresh}) async {
    await _storage.write(key: _keyAccess, value: access);
    await _storage.write(key: _keyRefresh, value: refresh);
  }

  Future<void> mettreAJourAccess(String access) async {
    await _storage.write(key: _keyAccess, value: access);
  }

  Future<String?> lireAccess() => _storage.read(key: _keyAccess);
  Future<String?> lireRefresh() => _storage.read(key: _keyRefresh);

  Future<void> effacer() async {
    await _storage.delete(key: _keyAccess);
    await _storage.delete(key: _keyRefresh);
  }
}
