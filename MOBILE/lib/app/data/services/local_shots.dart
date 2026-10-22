import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

/// Photos detected on the phone never reach the server, so the photo history keeps its own copy here
/// (app documents/shots/<detection id>.jpg). Server photos are shown from the server and not copied.
class LocalShots {
  static Directory? _dir;

  static Future<Directory> _folder() async {
    if (_dir != null) return _dir!;
    final d = Directory('${(await getApplicationDocumentsDirectory()).path}/shots');
    if (!await d.exists()) await d.create(recursive: true);
    return _dir = d;
  }

  static Future<void> keep(int detectionId, File photo) async {
    if (detectionId <= 0) return;
    try {
      await photo.copy('${(await _folder()).path}/$detectionId.jpg');
    } catch (e) {
      if (kDebugMode) debugPrint('[LocalShots] $e');
    }
  }

  /// The kept photo of [detectionId], or null.
  static Future<File?> fileFor(int detectionId) async {
    final f = File('${(await _folder()).path}/$detectionId.jpg');
    return await f.exists() ? f : null;
  }
}
