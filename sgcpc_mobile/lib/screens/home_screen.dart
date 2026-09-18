import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import '../providers/dossier_provider.dart';
import '../widgets/dossier_card.dart';
import '../widgets/sync_status_banner.dart';
import '../widgets/app_background.dart';
import 'login_screen.dart';
import 'nouveau_dossier_screen.dart';
import 'dossier_detail_screen.dart';

const orangeNiger = Color(0xFFE05206);

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DossierProvider>().charger();
    });
  }

  Future<void> _deconnexion() async {
    await context.read<AuthProvider>().deconnexion();
    if (mounted) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const LoginScreen()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    final dossierProvider = context.watch<DossierProvider>();

    // La session a expiré (refresh token périmé/révoqué) : on prévient l'agent
    // et on le renvoie à l'écran de connexion. Les dossiers non encore transmis
    // restent en sécurité dans la base locale et seront envoyés après reconnexion.
    if (dossierProvider.sessionExpiree) {
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        if (!context.mounted) return;
        dossierProvider.sessionExpiree = false;
        await context.read<AuthProvider>().deconnexion();
        if (!context.mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text(
            "Votre session a expiré. Reconnectez-vous — vos dossiers non "
            "transmis restent enregistrés sur l'appareil.",
          )),
        );
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const LoginScreen()),
          (route) => false,
        );
      });
    }

    return Scaffold(
      appBar: AppBar(
        backgroundColor: orangeNiger,
        foregroundColor: Colors.white,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Image.asset(
              'assets/img/armoirie1.png',
              height: 38,
              fit: BoxFit.contain,
            ),
            if (authProvider.utilisateur != null)
              Text(
                authProvider.utilisateur!.nomComplet,
                style: const TextStyle(
                    fontSize: 12, fontWeight: FontWeight.normal),
              ),
          ],
        ),
        actions: [
          IconButton(icon: const Icon(Icons.logout), onPressed: _deconnexion),
        ],
      ),
      body: AppBackground(
        child: Column(
          children: [
            SyncStatusBanner(
              horsLigne: dossierProvider.horsLigne,
              enAttente: dossierProvider.enAttenteSync,
              modeDemo: dossierProvider.modeDemo,
              onSynchroniserMaintenant: () => dossierProvider.synchroniser(),
            ),
            Expanded(
              child: dossierProvider.chargement
                  ? const Center(child: CircularProgressIndicator())
                  : dossierProvider.dossiers.isEmpty
                      ? _EtatVide()
                      : RefreshIndicator(
                          onRefresh: () => dossierProvider.charger(),
                          child: ListView.builder(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            itemCount: dossierProvider.dossiers.length,
                            itemBuilder: (context, index) {
                              final dossier = dossierProvider.dossiers[index];
                              return DossierCard(
                                dossier: dossier,
                                onTap: () => Navigator.of(context).push(
                                  MaterialPageRoute(
                                      builder: (_) => DossierDetailScreen(
                                          dossier: dossier)),
                                ),
                              );
                            },
                          ),
                        ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: orangeNiger,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add),
        label: const Text("Nouveau Dossier"),
        onPressed: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const NouveauDossierScreen()),
        ),
      ),
    );
  }
}

class _EtatVide extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.folder_open, size: 56, color: Colors.grey.shade300),
            const SizedBox(height: 12),
            const Text("Aucun dossier pour l'instant",
                style: TextStyle(color: Colors.grey)),
            const Text(
              "Appuyez sur \"Nouveau Dossier\" pour enregistrer un accident.",
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}
