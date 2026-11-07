import 'package:google_mlkit_translation/google_mlkit_translation.dart';

/// Offline translation on the phone with Google ML Kit (on-device models, ~30 MB per language, downloaded once,
/// then no network and no server is needed). ML Kit's Chinese model writes Simplified characters only, so a
/// translation INTO Traditional Chinese is refused offline rather than shown in the wrong script.
class OfflineTranslator {
  OfflineTranslator._();

  static final _models = OnDeviceTranslatorModelManager();

  static TranslateLanguage _lang(String l) => switch (l) {
        'vi' => TranslateLanguage.vietnamese,
        'en' => TranslateLanguage.english,
        _ => TranslateLanguage.chinese,
      };

  static String? unsupported(String source, String target) =>
      target == 'zh-Hant' ? 'Dịch offline chỉ viết được chữ giản thể. Hãy chọn Online để dịch sang phồn thể.' : null;

  /// Whether both language packs are already on the phone (then it works without network).
  static Future<bool> ready(String source, String target) async =>
      await _models.isModelDownloaded(_lang(source).bcpCode) && await _models.isModelDownloaded(_lang(target).bcpCode);

  /// Translate on the phone; downloads the missing language packs first (that one time needs the network).
  static Future<String> translate(String text, String source, String target, {void Function()? onDownload}) async {
    final problem = unsupported(source, target);
    if (problem != null) throw OfflineTranslateException(problem);
    for (final l in {source, target}) {
      final code = _lang(l).bcpCode;
      if (!await _models.isModelDownloaded(code)) {
        onDownload?.call();
        final ok = await _models.downloadModel(code, isWifiRequired: false);
        if (!ok) throw OfflineTranslateException('Chưa tải được gói dịch offline. Kết nối mạng một lần để tải (~30 MB).');
      }
    }
    final translator = OnDeviceTranslator(sourceLanguage: _lang(source), targetLanguage: _lang(target));
    try {
      return await translator.translateText(text);
    } finally {
      await translator.close();
    }
  }
}

class OfflineTranslateException implements Exception {
  OfflineTranslateException(this.message);
  final String message;

  @override
  String toString() => message;
}
