import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:sgcpc_mobile/screens/login_screen.dart';
import 'package:sgcpc_mobile/providers/auth_provider.dart';
import 'package:sgcpc_mobile/services/auth_service.dart';
import 'package:sgcpc_mobile/services/permis_service.dart';
import 'package:sgcpc_mobile/services/token_storage.dart';

void main() {
  testWidgets('affiche la connexion et la vérification de permis',
      (tester) async {
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          Provider<AuthService>(create: (_) => AuthService(TokenStorage())),
          ChangeNotifierProvider<AuthProvider>(
            create: (context) => AuthProvider(context.read<AuthService>()),
          ),
          Provider<PermisService>(create: (_) => PermisService()),
        ],
        child: const MaterialApp(home: LoginScreen()),
      ),
    );

    expect(find.text('SGCPC'), findsOneWidget);
    expect(find.text('Se connecter'), findsOneWidget);
    expect(find.text('Vérifier un permis'), findsOneWidget);
  });
}
