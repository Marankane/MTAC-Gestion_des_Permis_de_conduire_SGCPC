import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

import '../core/constants.dart';
import '../models/dossier.dart';

/// Base locale SQLite : cache des dossiers + file d'attente de synchronisation.
/// C'est le cœur de la parade au risque "Coupures d'électricité/internet"
/// identifié dans le CDCF (section 8) : chaque dossier est TOUJOURS écrit ici
/// en premier, que le réseau soit disponible ou non.
class LocalDatabase {
  static Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final path = join(await getDatabasesPath(), 'sgcpc_local.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE dossiers (
            local_id TEXT PRIMARY KEY,
            server_id INTEGER,
            numero TEXT,
            uuid TEXT,
            statut_serveur TEXT,
            statut_sync TEXT NOT NULL,
            erreur_sync TEXT,
            cree_le TEXT NOT NULL,
            photos_locales TEXT NOT NULL,
            payload_json TEXT NOT NULL
          )
        ''');
      },
    );
  }

  Future<void> enregistrer(Dossier dossier) async {
    final db = await database;
    await db.insert(
      'dossiers',
      dossier.toDbMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Dossier>> tousLesDossiers() async {
    final db = await database;
    final rows = await db.query('dossiers', orderBy: 'cree_le DESC');
    return rows.map((r) => Dossier.fromDbMap(r)).toList();
  }

  Future<List<Dossier>> enAttenteDeSynchronisation() async {
    final db = await database;
    final rows = await db.query(
      'dossiers',
      where: 'statut_sync IN (?, ?)',
      whereArgs: [StatutSync.enAttente, StatutSync.echec],
      orderBy: 'cree_le ASC',
    );
    return rows.map((r) => Dossier.fromDbMap(r)).toList();
  }

  Future<int> compterEnAttente() async {
    final db = await database;
    final result = Sqflite.firstIntValue(await db.rawQuery(
      'SELECT COUNT(*) FROM dossiers WHERE statut_sync IN (?, ?)',
      [StatutSync.enAttente, StatutSync.echec],
    ));
    return result ?? 0;
  }
}
