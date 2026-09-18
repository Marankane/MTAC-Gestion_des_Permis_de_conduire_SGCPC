import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../models/permis_verification.dart';
import '../core/constants.dart';
import '../providers/auth_provider.dart';
import '../services/permis_service.dart';
import 'home_screen.dart';

const orangeNiger = Color(0xFFE05206);
const vertNiger = Color(0xFF1F5B3A);

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with TickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _usernameCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _cacherMotDePasse = true;
  int _imageIndex = 0;
  Timer? _timer;
  late final AnimationController _backgroundMotion;
  late final AnimationController _verificationPulse;

  static const _backgrounds = [
    'assets/img/aereport1.webp',
    'assets/img/aereport2.jpg',
    'assets/img/aereport3.jpg',
    'assets/img/aereport4.webp',
  ];

  @override
  void initState() {
    super.initState();
    _usernameCtrl.text = DemoConfig.username;
    _passwordCtrl.text = DemoConfig.password;
    _backgroundMotion = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 14),
    )..repeat(reverse: true);
    _verificationPulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);
    _timer = Timer.periodic(const Duration(seconds: 10), (_) {
      if (mounted) {
        setState(() => _imageIndex = (_imageIndex + 1) % _backgrounds.length);
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _backgroundMotion.dispose();
    _verificationPulse.dispose();
    _usernameCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _seConnecter() async {
    if (!_formKey.currentState!.validate()) return;
    final succes = await context
        .read<AuthProvider>()
        .connexion(_usernameCtrl.text.trim(), _passwordCtrl.text);
    if (succes && mounted) {
      Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const HomeScreen()));
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = context.watch<AuthProvider>();
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          AnimatedBuilder(
            animation: _backgroundMotion,
            builder: (context, child) {
              final movement = _backgroundMotion.value - 0.5;
              return Transform.translate(
                offset: Offset(movement * 18, movement * 10),
                child: Transform.scale(scale: 1.08, child: child),
              );
            },
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 900),
              child: SizedBox.expand(
                key: ValueKey(_imageIndex),
                child:
                    Image.asset(_backgrounds[_imageIndex], fit: BoxFit.cover),
              ),
            ),
          ),
          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding:
                    const EdgeInsets.symmetric(horizontal: 24, vertical: 28),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 430),
                  child: Column(
                    children: [
                      Image.asset('assets/img/armoirie1.png', height: 118),
                      const SizedBox(height: 12),
                      const Text('SGCPC',
                          style: TextStyle(
                              color: Colors.white,
                              fontSize: 30,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 1.5)),
                      const SizedBox(height: 4),
                      const Text('Système de gestion et de contrôle des permis',
                          textAlign: TextAlign.center,
                          style:
                              TextStyle(color: Colors.white70, fontSize: 13)),
                      const SizedBox(height: 26),
                      _glassPanel(
                        child: Form(
                          key: _formKey,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              const Text('Accès professionnel',
                                  style: TextStyle(
                                      fontSize: 19,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.white)),
                              const SizedBox(height: 16),
                              _field(_usernameCtrl, 'Identifiant',
                                  Icons.person_outline),
                              const SizedBox(height: 12),
                              TextFormField(
                                controller: _passwordCtrl,
                                obscureText: _cacherMotDePasse,
                                style: const TextStyle(color: Colors.white),
                                decoration: _decoration(
                                        'Mot de passe', Icons.lock_outline)
                                    .copyWith(
                                  suffixIcon: IconButton(
                                      icon: Icon(
                                          _cacherMotDePasse
                                              ? Icons.visibility_off
                                              : Icons.visibility,
                                          color: Colors.white70),
                                      onPressed: () => setState(() =>
                                          _cacherMotDePasse =
                                              !_cacherMotDePasse)),
                                ),
                                validator: (v) => (v == null || v.isEmpty)
                                    ? 'Champ requis'
                                    : null,
                                onFieldSubmitted: (_) => _seConnecter(),
                              ),
                              if (authProvider.erreur != null) ...[
                                const SizedBox(height: 10),
                                Text(authProvider.erreur!,
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(
                                        color: Color(0xFFFFB4AB))),
                              ],
                              const SizedBox(height: 18),
                              DecoratedBox(
                                decoration: const BoxDecoration(
                                    gradient: LinearGradient(
                                        colors: [orangeNiger, vertNiger]),
                                    borderRadius:
                                        BorderRadius.all(Radius.circular(12))),
                                child: ElevatedButton(
                                  style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.transparent,
                                      shadowColor: Colors.transparent,
                                      foregroundColor: Colors.white,
                                      padding: const EdgeInsets.symmetric(
                                          vertical: 15)),
                                  onPressed: authProvider.enCours
                                      ? null
                                      : _seConnecter,
                                  child: authProvider.enCours
                                      ? const SizedBox(
                                          width: 20,
                                          height: 20,
                                          child: CircularProgressIndicator(
                                              color: Colors.white,
                                              strokeWidth: 2))
                                      : const Text('Se connecter',
                                          style: TextStyle(
                                              fontWeight: FontWeight.bold)),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),
                      AnimatedBuilder(
                        animation: _verificationPulse,
                        builder: (context, child) {
                          final pulse = _verificationPulse.value;
                          return Transform.scale(
                            scale: 1 + (pulse * 0.025),
                            child: Container(
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(18),
                                boxShadow: [
                                  BoxShadow(
                                    color: orangeNiger.withValues(
                                        alpha: 0.35 + (pulse * 0.25)),
                                    blurRadius: 14 + (pulse * 8),
                                    spreadRadius: pulse * 2,
                                  ),
                                ],
                              ),
                              child: child,
                            ),
                          );
                        },
                        child: ElevatedButton.icon(
                          onPressed: () => showModalBottomSheet<void>(
                              context: context,
                              isScrollControlled: true,
                              backgroundColor: Colors.transparent,
                              builder: (_) => const _VerificationSheet()),
                          icon: const Icon(Icons.qr_code_scanner_rounded),
                          label: const Text('Vérifier un permis',
                              style: TextStyle(
                                  fontSize: 16, fontWeight: FontWeight.w800)),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: orangeNiger,
                            foregroundColor: Colors.white,
                            elevation: 0,
                            padding: const EdgeInsets.symmetric(
                                horizontal: 24, vertical: 15),
                            shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(18)),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _field(
          TextEditingController controller, String label, IconData icon) =>
      TextFormField(
        controller: controller,
        style: const TextStyle(color: Colors.white),
        decoration: _decoration(label, icon),
        validator: (v) =>
            (v == null || v.trim().isEmpty) ? 'Champ requis' : null,
        textInputAction: TextInputAction.next,
      );

  InputDecoration _decoration(String label, IconData icon) => InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: Colors.white70),
      prefixIcon: Icon(icon, color: Colors.white70),
      enabledBorder: const OutlineInputBorder(
          borderSide: BorderSide(color: Colors.white38)),
      focusedBorder:
          const OutlineInputBorder(borderSide: BorderSide(color: Colors.white)),
      border: const OutlineInputBorder());

  Widget _glassPanel({required Widget child}) => Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.36),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white24)),
      child: child);
}

class _VerificationSheet extends StatefulWidget {
  const _VerificationSheet();

  @override
  State<_VerificationSheet> createState() => _VerificationSheetState();
}

class _VerificationSheetState extends State<_VerificationSheet> {
  final _formKey = GlobalKey<FormState>();
  final _numeroCtrl = TextEditingController();
  final _mentionCtrl = TextEditingController();
  PermisVerification? _permis;
  String? _erreur;
  bool _chargement = false;

  @override
  void initState() {
    super.initState();
    _numeroCtrl.text = DemoConfig.numeroPermis;
    _mentionCtrl.text = DemoConfig.mentionPermis;
  }

  @override
  void dispose() {
    _numeroCtrl.dispose();
    _mentionCtrl.dispose();
    super.dispose();
  }

  Future<void> _verifier() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _chargement = true;
      _erreur = null;
      _permis = null;
    });
    try {
      final permis = await context.read<PermisService>().verifier(
          numero: _numeroCtrl.text.trim(), mention: _mentionCtrl.text.trim());
      if (mounted) setState(() => _permis = permis);
    } catch (e) {
      if (mounted) setState(() => _erreur = e.toString());
    } finally {
      if (mounted) setState(() => _chargement = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.viewInsetsOf(context).bottom;
    return Padding(
      padding: EdgeInsets.only(top: 80, bottom: bottom),
      child: Container(
        constraints: const BoxConstraints(maxHeight: 720),
        decoration: const BoxDecoration(
            color: Color(0xFFF7F8F4),
            borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(22, 18, 22, 28),
          child: Form(
            key: _formKey,
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Center(
                      child: Container(
                          width: 42,
                          height: 4,
                          decoration: BoxDecoration(
                              color: Colors.black26,
                              borderRadius: BorderRadius.circular(4)))),
                  const SizedBox(height: 18),
                  const Text('Vérifier un permis',
                      style: TextStyle(
                          fontSize: 23,
                          fontWeight: FontWeight.bold,
                          color: vertNiger)),
                  const SizedBox(height: 5),
                  const Text(
                      'Saisissez le numéro et la mention inscrits sur le permis.',
                      style: TextStyle(color: Colors.black54)),
                  const SizedBox(height: 18),
                  TextFormField(
                      controller: _numeroCtrl,
                      decoration: const InputDecoration(
                          labelText: 'Numéro du permis',
                          prefixIcon: Icon(Icons.badge_outlined),
                          border: OutlineInputBorder()),
                      validator: _required),
                  const SizedBox(height: 12),
                  TextFormField(
                      controller: _mentionCtrl,
                      decoration: const InputDecoration(
                          labelText: 'Mention du permis',
                          prefixIcon: Icon(Icons.bookmark_outline),
                          border: OutlineInputBorder()),
                      validator: _required),
                  const SizedBox(height: 14),
                  ElevatedButton.icon(
                      onPressed: _chargement ? null : _verifier,
                      icon: _chargement
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.search),
                      label: const Text('Vérifier'),
                      style: ElevatedButton.styleFrom(
                          backgroundColor: vertNiger,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 14))),
                  if (_erreur != null)
                    Padding(
                        padding: const EdgeInsets.only(top: 14),
                        child: Text(_erreur!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.red))),
                  if (_permis != null) ...[
                    const SizedBox(height: 18),
                    _PermisCard(permis: _permis!),
                  ],
                ]),
          ),
        ),
      ),
    );
  }

  String? _required(String? value) =>
      value == null || value.trim().isEmpty ? 'Champ requis' : null;
}

class _PermisCard extends StatelessWidget {
  final PermisVerification permis;
  const _PermisCard({required this.permis});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: vertNiger.withValues(alpha: 0.2)),
          boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 12)]),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Icon(Icons.verified, color: vertNiger),
          const SizedBox(width: 8),
          const Text('Permis vérifié',
              style: TextStyle(color: vertNiger, fontWeight: FontWeight.bold)),
          const Spacer(),
          _StatusBadge(permis.statutPermis)
        ]),
        const Divider(height: 22),
        Center(
            child: QrImageView(
                data: permis.codeQr,
                size: 115,
                eyeStyle: const QrEyeStyle(
                    eyeShape: QrEyeShape.square, color: vertNiger))),
        const SizedBox(height: 12),
        _line('Nom', permis.nom),
        _line('Prénom', permis.prenom),
        _line('Date de naissance', permis.dateNaissance),
        _line('Lieu de naissance', permis.lieuNaissance),
        _line('Numéro', permis.numeroPermis),
        _line('Mention', permis.mentionPermis),
        _line('Type', permis.typePermis),
        _line('Délivré le', permis.dateDelivrance ?? 'Non renseignée'),
        _line('Expire le', permis.dateExpiration ?? 'Non renseignée'),
        if (permis.dateSuspension != null)
          _line('Suspendu le', permis.dateSuspension!),
      ]),
    );
  }

  Widget _line(String label, String value) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        SizedBox(
            width: 132,
            child: Text(label,
                style: const TextStyle(color: Colors.black54, fontSize: 12))),
        Expanded(
            child: Text(value,
                style: const TextStyle(fontWeight: FontWeight.w600)))
      ]));
}

class _StatusBadge extends StatelessWidget {
  final String value;
  const _StatusBadge(this.value);

  @override
  Widget build(BuildContext context) {
    final actif = value == 'ACTIF';
    return Container(
        padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
        decoration: BoxDecoration(
            color:
                (actif ? Colors.green : Colors.orange).withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(20)),
        child: Text(value,
            style: TextStyle(
                color: actif ? Colors.green.shade800 : Colors.orange.shade800,
                fontSize: 11,
                fontWeight: FontWeight.bold)));
  }
}
