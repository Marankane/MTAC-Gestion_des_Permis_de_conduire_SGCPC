import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'providers/auth_provider.dart';
import 'providers/dossier_provider.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'services/api_client.dart';
import 'services/auth_service.dart';
import 'services/connectivity_service.dart';
import 'services/dossier_service.dart';
import 'services/local_database.dart';
import 'services/permis_service.dart';
import 'services/token_storage.dart';
import 'widgets/inactivity_guard.dart';

final navigatorKey = GlobalKey<NavigatorState>();

void main() {
  runApp(const SgcpcApp());
}

class SgcpcApp extends StatelessWidget {
  const SgcpcApp({super.key});

  @override
  Widget build(BuildContext context) {
    // Injection de dépendances simple, sans package supplémentaire :
    // chaque service est construit une fois et partagé via Provider.
    final tokenStorage = TokenStorage();
    final apiClient = ApiClient(tokenStorage);
    final localDatabase = LocalDatabase();
    final connectivityService = ConnectivityService();

    return MultiProvider(
      providers: [
        Provider<AuthService>(create: (_) => AuthService(tokenStorage)),
        Provider<PermisService>(create: (_) => PermisService()),
        Provider<DossierService>(
          create: (_) =>
              DossierService(apiClient, localDatabase, connectivityService),
        ),
        ChangeNotifierProvider<AuthProvider>(
          create: (context) => AuthProvider(context.read<AuthService>()),
        ),
        ChangeNotifierProvider<DossierProvider>(
          create: (context) => DossierProvider(
              context.read<DossierService>(), connectivityService),
        ),
      ],
      child: MaterialApp(
        navigatorKey: navigatorKey,
        builder: (context, child) => InactivityGuard(
          navigatorKey: navigatorKey,
          child: child ?? const SizedBox.shrink(),
        ),
        title: 'SGCPC',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorSchemeSeed: const Color(0xFFE05206),
          scaffoldBackgroundColor: const Color(0xFFF9FAFB),
          appBarTheme: const AppBarTheme(centerTitle: false),
          cardTheme: CardThemeData(
            color: Color.fromRGBO(255, 255, 255, 0.30),
            surfaceTintColor: Colors.transparent,
            elevation: 3,
            margin: EdgeInsets.zero,
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: Color.fromRGBO(255, 255, 255, 0.30),
            labelStyle: TextStyle(color: Colors.black87),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12)),
              borderSide: BorderSide(color: Colors.white70),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12)),
              borderSide: BorderSide(color: Colors.white70),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.all(Radius.circular(12)),
              borderSide: BorderSide(color: Color(0xFFE05206), width: 2),
            ),
          ),
        ),
        home: const _DemarrageScreen(),
      ),
    );
  }
}

/// Écran transitoire : vérifie s'il existe déjà une session valide (token
/// stocké) avant d'afficher soit l'accueil, soit l'écran de connexion.
class _DemarrageScreen extends StatefulWidget {
  const _DemarrageScreen();

  @override
  State<_DemarrageScreen> createState() => _DemarrageScreenState();
}

class _DemarrageScreenState extends State<_DemarrageScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await context.read<AuthProvider>().verifierSession();
      if (!mounted) return;
      final etat = context.read<AuthProvider>().etat;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => etat == EtatAuth.connecte
              ? const HomeScreen()
              : const LoginScreen(),
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: Center(child: CircularProgressIndicator()));
  }
}
