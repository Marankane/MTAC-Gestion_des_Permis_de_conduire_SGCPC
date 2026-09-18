import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import '../screens/login_screen.dart';

class InactivityGuard extends StatefulWidget {
  final Widget child;
  final GlobalKey<NavigatorState> navigatorKey;

  const InactivityGuard({
    super.key,
    required this.child,
    required this.navigatorKey,
  });

  @override
  State<InactivityGuard> createState() => _InactivityGuardState();
}

class _InactivityGuardState extends State<InactivityGuard> {
  static const _delaiInactivite = Duration(minutes: 10);
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _redemarrerMinuteur();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _redemarrerMinuteur() {
    _timer?.cancel();
    _timer = Timer(_delaiInactivite, _deconnecterPourInactivite);
  }

  Future<void> _deconnecterPourInactivite() async {
    if (!mounted) return;
    final auth = context.read<AuthProvider>();
    if (auth.etat != EtatAuth.connecte) return;
    await auth.deconnexion();
    if (!mounted) return;
    widget.navigatorKey.currentState?.pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Listener(
      behavior: HitTestBehavior.translucent,
      onPointerDown: (_) => _redemarrerMinuteur(),
      onPointerMove: (_) => _redemarrerMinuteur(),
      onPointerSignal: (_) => _redemarrerMinuteur(),
      child: widget.child,
    );
  }
}
