import 'package:connectivity_plus/connectivity_plus.dart';

/// Détecte les changements de connectivité pour déclencher la synchronisation
/// automatique dès que le réseau revient (cf. mode dégradé du CDCF).
class ConnectivityService {
  final Connectivity _connectivity = Connectivity();

  Stream<bool> get surChangementConnexion => _connectivity.onConnectivityChanged
      .map((results) => !results.contains(ConnectivityResult.none));

  Future<bool> estConnecte() async {
    final result = await _connectivity.checkConnectivity();
    return !result.contains(ConnectivityResult.none);
  }
}
