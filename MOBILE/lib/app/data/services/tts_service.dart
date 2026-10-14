import 'package:flutter/foundation.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:get/get.dart';

/// Text-to-speech that only speaks with the exact locale of the word (vi-VN, en-US, zh-CN, zh-TW).
/// If the device has no voice for that locale it reports it instead of reading with a wrong accent.
class TtsService extends GetxService {
  static TtsService get to => Get.find<TtsService>();

  final FlutterTts _tts = FlutterTts();
  final Map<String, bool> _available = {};

  @override
  void onInit() {
    super.onInit();
    _tts.setSpeechRate(0.45);
    _tts.setPitch(1.0);
  }

  Future<bool> _hasLocale(String locale) async {
    if (_available.containsKey(locale)) return _available[locale]!;
    bool ok = false;
    try {
      ok = (await _tts.isLanguageAvailable(locale)) == true;
    } catch (e) {
      if (kDebugMode) debugPrint('[TTS] $e');
    }
    _available[locale] = ok;
    return ok;
  }

  /// Returns false when no voice exists for [locale].
  Future<bool> speak(String text, String locale) async {
    if (text.trim().isEmpty) return false;
    if (!await _hasLocale(locale)) {
      Get.snackbar('Chưa có giọng đọc $locale',
          'Hãy cài thêm giọng đọc trong Cài đặt > Chuyển văn bản thành giọng nói của điện thoại.',
          snackPosition: SnackPosition.BOTTOM);
      return false;
    }
    await _tts.stop();
    await _tts.setLanguage(locale);
    await _tts.speak(text);
    return true;
  }

  Future<void> stop() => _tts.stop();
}
