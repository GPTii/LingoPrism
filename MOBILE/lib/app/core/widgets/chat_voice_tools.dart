import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../network/api_client.dart';
import '../theme/app_colors.dart';

const _langs = <(String, String, String)>[
  ('vi', 'Tiếng Việt', 'vi_VN'),
  ('en', 'Tiếng Anh', 'en_US'),
  ('zh-Hans', 'Tiếng Trung giản thể', 'zh_CN'),
  ('zh-Hant', 'Tiếng Trung phồn thể', 'zh_TW'),
];
String _label(String l) => _langs.firstWhere((x) => x.$1 == l).$2;

/// Above a chat box (same as the web ChatVoiceTools): speak instead of typing – the words land in the box –
/// and turn what is in the box into another language before sending it (machine translation, marked as such,
/// with pinyin for the sender).
class ChatVoiceTools extends StatefulWidget {
  const ChatVoiceTools({super.key, required this.controller});

  final TextEditingController controller;

  @override
  State<ChatVoiceTools> createState() => _ChatVoiceToolsState();
}

class _ChatVoiceToolsState extends State<ChatVoiceTools> {
  static final SpeechToText _stt = SpeechToText();
  static bool? _sttReady;
  static Future<bool>? _canTranslate;
  static String _micLang = 'vi'; // kept for the app run
  static String _lastTarget = 'en';

  bool _listening = false;
  bool _busy = false;
  // the last translation, so it can be undone; forgotten as soon as the box no longer holds it
  ({String original, String result, String target, String reading})? _done;

  TextEditingController get _box => widget.controller;

  @override
  void initState() {
    super.initState();
    _canTranslate ??= ApiClient.to
        .get<dynamic>('/ai/status/')
        .then((d) => d is Map && d['translate'] == true)
        .catchError((_) => false);
    _box.addListener(_changed);
  }

  @override
  void dispose() {
    _box.removeListener(_changed);
    if (_listening) _stt.cancel();
    super.dispose();
  }

  void _changed() {
    if (mounted) setState(() {});
  }

  void _tell(String text) => Get.snackbar('Chat', text, snackPosition: SnackPosition.BOTTOM);

  Future<void> _talk() async {
    if (_listening) {
      await _stt.stop();
      return;
    }
    _sttReady ??= await _stt.initialize(onError: (e) {
      if (!mounted) return;
      setState(() => _listening = false);
      _tell(e.errorMsg.contains('no_match') || e.errorMsg.contains('speech_timeout')
          ? 'Chưa nghe rõ. Bấm mic rồi nói to, rõ hơn nhé.'
          : 'Không nhận dạng được giọng nói, thử lại nhé.');
    });
    if (_sttReady != true) {
      _tell('Điện thoại chưa cho phép dùng micro hoặc chưa có nhận dạng giọng nói.');
      return;
    }
    final before = _box.text.trim();
    setState(() => _listening = true);
    await _stt.listen(
      listenOptions: SpeechListenOptions(
        localeId: _langs.firstWhere((x) => x.$1 == _micLang).$3,
        listenFor: const Duration(seconds: 20),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
        cancelOnError: true,
      ),
      onResult: (SpeechRecognitionResult r) {
        if (!mounted) return;
        final heard = r.recognizedWords.trim();
        final text = before.isEmpty ? heard : '$before $heard';
        _box.value = TextEditingValue(text: text, selection: TextSelection.collapsed(offset: text.length));
        if (r.finalResult) setState(() => _listening = false);
      },
    );
  }

  Future<void> _translate(String target) async {
    _lastTarget = target;
    final original = _box.text.trim();
    if (original.isEmpty) {
      _tell('Nhập hoặc nói một câu trước rồi hãy dịch.');
      return;
    }
    setState(() => _busy = true);
    try {
      final d = Map<String, dynamic>.from(await ApiClient.to
          .post<dynamic>('/translate/', data: {'text': original, 'source': 'auto', 'target': target}) as Map);
      final result = d['translation'] as String? ?? '';
      _box.value = TextEditingValue(text: result, selection: TextSelection.collapsed(offset: result.length));
      _done = (original: original, result: result, target: target, reading: d['reading'] as String? ?? '');
    } catch (e) {
      _tell(ApiClient.toApiException(e).message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: _canTranslate,
      builder: (context, snap) {
        final canTranslate = snap.data == true;
        final done = _done != null && _done!.result == _box.text ? _done : null;
        final small = TextStyle(fontSize: 12.sp, color: AppColors.textSecondary);
        return Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
          if (done != null)
            Padding(
              padding: EdgeInsets.only(bottom: 2.h),
              child: Wrap(crossAxisAlignment: WrapCrossAlignment.center, spacing: 6.w, children: [
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 2.h),
                  decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(4.r),
                      border: Border.all(color: AppColors.line)),
                  child: Text('Bản dịch máy', style: small.copyWith(fontWeight: FontWeight.w700)),
                ),
                Text('sang ${_label(done.target)}', style: small),
                if (done.reading.isNotEmpty)
                  Text('· ${done.reading}', style: small.copyWith(color: AppColors.textPrimary)),
                InkWell(
                  onTap: () {
                    _box.text = done.original;
                    setState(() => _done = null);
                  },
                  child: Text('Hoàn tác', style: small.copyWith(color: AppColors.primary, fontWeight: FontWeight.w700)),
                ),
              ]),
            ),
          Row(children: [
            TextButton.icon(
              onPressed: _talk,
              style: TextButton.styleFrom(
                foregroundColor: _listening ? AppColors.beamCoral : AppColors.primary,
                visualDensity: VisualDensity.compact,
              ),
              icon: Icon(_listening ? Icons.graphic_eq_rounded : Icons.mic_rounded, size: 18.sp),
              label: Text(_listening ? 'Đang nghe…' : 'Nói'),
            ),
            PopupMenuButton<String>(
              enabled: !_listening,
              tooltip: 'Chọn ngôn ngữ nói',
              initialValue: _micLang,
              onSelected: (v) => setState(() => _micLang = v),
              itemBuilder: (_) => [for (final l in _langs) PopupMenuItem(value: l.$1, child: Text('Nói bằng ${l.$2}'))],
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 2.w, vertical: 6.h),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Text(
                      _micLang == 'vi'
                          ? 'VI'
                          : _micLang == 'en'
                              ? 'EN'
                              : _micLang == 'zh-Hans'
                                  ? '简'
                                  : '繁',
                      style: small.copyWith(fontWeight: FontWeight.w700)),
                  Icon(Icons.arrow_drop_down_rounded, size: 18.sp, color: AppColors.textSecondary),
                ]),
              ),
            ),
            if (canTranslate) ...[
              SizedBox(width: 6.w),
              PopupMenuButton<String>(
                enabled: !_busy && _box.text.trim().isNotEmpty,
                tooltip: 'Dịch tin nhắn trước khi gửi',
                initialValue: _lastTarget,
                onSelected: _translate,
                itemBuilder: (_) =>
                    [for (final l in _langs) PopupMenuItem(value: l.$1, child: Text('Dịch sang ${l.$2}'))],
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 6.h),
                  child: Row(mainAxisSize: MainAxisSize.min, children: [
                    _busy
                        ? SizedBox(width: 14.w, height: 14.w, child: const CircularProgressIndicator(strokeWidth: 2))
                        : Icon(Icons.translate_rounded,
                            size: 18.sp, color: _box.text.trim().isEmpty ? AppColors.textHint : AppColors.primary),
                    SizedBox(width: 4.w),
                    Text('Dịch',
                        style: TextStyle(
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w600,
                            color: _box.text.trim().isEmpty ? AppColors.textHint : AppColors.primary)),
                  ]),
                ),
              ),
            ],
          ]),
        ]);
      },
    );
  }
}
