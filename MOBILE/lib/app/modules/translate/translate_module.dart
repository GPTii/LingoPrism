import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/target_word.dart';
import '../../data/services/auth_service.dart';
import '../../data/services/tts_service.dart';

const _langs = <(String, String, String)>[
  ('vi', 'Tiếng Việt', 'vi-VN'),
  ('en', 'Tiếng Anh', 'en-US'),
  ('zh-Hans', 'Tiếng Trung giản thể', 'zh-CN'),
  ('zh-Hant', 'Tiếng Trung phồn thể', 'zh-TW'),
];
const _max = 500;

String _locale(String l) => _langs.firstWhere((x) => x.$1 == l).$3;
String _label(String l) => _langs.firstWhere((x) => x.$1 == l).$2;
bool _zh(String l) => l.startsWith('zh');

/// "Dịch" (same as the web /dich): type or speak a sentence, get a machine translation that can be heard,
/// and save the verified words found in it. The translation itself is never learning data.
class TranslateView extends StatefulWidget {
  const TranslateView({super.key});

  @override
  State<TranslateView> createState() => _TranslateViewState();
}

class _TranslateViewState extends State<TranslateView> {
  static final SpeechToText _stt = SpeechToText();
  static bool? _sttReady;

  final _text = TextEditingController();
  late String _learning;
  late String _source;
  late String _target;
  bool _listening = false;
  bool _busy = false;
  String _error = '';
  Map<String, dynamic>? _out;
  final Set<int> _saved = {};
  late final Future<bool> _available = _checkAvailable();

  @override
  void initState() {
    super.initState();
    final user = AuthService.to.currentUser;
    // the language being learned (English for those learning Vietnamese itself)
    _learning = user?.activeLanguage == 'zh' ? user!.targetCode : 'en';
    _source = user?.activeLanguage == 'vi' ? 'en' : 'vi';
    _target = user?.activeLanguage == 'vi' ? 'vi' : _learning;
  }

  @override
  void dispose() {
    if (_listening) _stt.cancel();
    _text.dispose();
    super.dispose();
  }

  Future<bool> _checkAvailable() async {
    try {
      final d = await ApiClient.to.get<dynamic>('/ai/status/');
      return d is Map && d['translate'] == true;
    } catch (_) {
      return false;
    }
  }

  Future<void> _translate([String? text, String? source, String? target]) async {
    final t = (text ?? _text.text).trim();
    if (t.isEmpty || _busy) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _busy = true;
      _error = '';
    });
    try {
      final d =
          await ApiClient.to.post<dynamic>('/translate/', data: {'text': t, 'source': source ?? _source, 'target': target ?? _target});
      if (mounted) setState(() => _out = Map<String, dynamic>.from(d as Map));
    } catch (e) {
      if (mounted) setState(() => _error = ApiClient.toApiException(e).message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// A mic on each side: speaking the other side's language flips the direction, so two people can take turns.
  Future<void> _talk(bool otherSide) async {
    if (_listening) {
      await _stt.stop();
      return;
    }
    if (otherSide) {
      setState(() {
        final s = _source;
        _source = _target;
        _target = s;
      });
    }
    _sttReady ??= await _stt.initialize(onError: (e) {
      if (!mounted) return;
      setState(() {
        _listening = false;
        _error = e.errorMsg.contains('no_match') || e.errorMsg.contains('speech_timeout')
            ? 'Chưa nghe rõ. Bấm mic rồi nói to, rõ hơn nhé.'
            : 'Không nhận dạng được giọng nói, thử lại nhé.';
      });
    });
    if (_sttReady != true) {
      setState(() => _error = 'Điện thoại chưa cho phép dùng micro hoặc chưa có nhận dạng giọng nói.');
      return;
    }
    final source = _source, target = _target;
    setState(() {
      _listening = true;
      _error = '';
      _text.clear();
    });
    await _stt.listen(
      listenOptions: SpeechListenOptions(
        localeId: _locale(source).replaceAll('-', '_'),
        listenFor: const Duration(seconds: 20),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
        cancelOnError: true,
      ),
      onResult: (SpeechRecognitionResult r) {
        if (!mounted) return;
        setState(() => _text.text = r.recognizedWords);
        if (!r.finalResult) return;
        setState(() => _listening = false);
        _translate(r.recognizedWords, source, target);
      },
    );
  }

  void _swap() {
    final out = _out;
    setState(() {
      final s = _source;
      _source = _target;
      _target = s;
    });
    if (out != null && out['source'] == _target) {
      _text.text = out['translation'] as String? ?? '';
      _translate();
    }
  }

  void _pick(bool isSource, String v) {
    setState(() {
      if (isSource) {
        _source = v;
        // giản ↔ phồn is not a translation (the words differ by region), so the two are never paired
        if (v == _target || (_zh(v) && _zh(_target))) _target = v == 'vi' ? _learning : 'vi';
      } else {
        _target = v;
        if (v == _source || (_zh(v) && _zh(_source))) _source = v == 'vi' ? _learning : 'vi';
      }
    });
  }

  Future<void> _save(Map w) async {
    try {
      await ApiClient.to.post<dynamic>('/my-words/',
          data: {'word': w['word_id'], 'source': 'manual'},
          query: {'lang': w['lang'], 'script': (w['script'] as String? ?? '').isEmpty ? null : w['script']});
      setState(() => _saved.add(w['word_id'] as int));
      Get.snackbar('Đã lưu', '“${w['text']}” đã vào Từ của tôi', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Không lưu được', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  void _say(String text, String language) {
    if (Get.isRegistered<TtsService>()) TtsService.to.speak(text, _locale(language));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Dịch')),
      body: FutureBuilder<bool>(
        future: _available,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snap.data != true) {
            return Center(
              child: Padding(
                padding: EdgeInsets.all(24.w),
                child: Text('Tính năng dịch chưa được bật trên máy chủ. Bạn quay lại sau nhé.',
                    textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary, fontSize: 15.sp)),
              ),
            );
          }
          return ListView(
            padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 32.h),
            children: [
              Row(children: [
                Expanded(child: _picker(true)),
                IconButton(onPressed: _swap, tooltip: 'Đổi chiều', icon: const Icon(Icons.swap_horiz_rounded)),
                Expanded(child: _picker(false)),
              ]),
              SizedBox(height: 12.h),
              _sourceCard(),
              SizedBox(height: 12.h),
              _resultCard(),
              if (_out != null) ...[
                SizedBox(height: 10.h),
                Text(
                    'Bản dịch do AI viết, có thể chưa chính xác và không được dùng làm bài học. '
                    'Chỉ những từ đã kiểm duyệt bên dưới mới lưu được vào thẻ học.',
                    style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
                ..._words(),
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _picker(bool isSource) {
    final value = isSource ? _source : _target;
    final other = isSource ? _target : _source;
    return DropdownButtonFormField<String>(
      initialValue: value,
      key: ValueKey('$isSource$value'),
      isExpanded: true,
      decoration: InputDecoration(
        labelText: isSource ? 'Dịch từ' : 'Sang',
        isDense: true,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12.r)),
      ),
      items: [
        for (final l in _langs)
          DropdownMenuItem(
            value: l.$1,
            enabled: l.$1 != other && !(_zh(l.$1) && _zh(other)),
            child: Text(l.$2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: l.$1 != other && !(_zh(l.$1) && _zh(other)) ? null : AppColors.textSecondary)),
          ),
      ],
      onChanged: (v) => v == null ? null : _pick(isSource, v),
    );
  }

  BoxDecoration _box([Color? color]) => BoxDecoration(
      color: color ?? AppColors.surface, borderRadius: BorderRadius.circular(16.r), border: Border.all(color: AppColors.line));

  Widget _sourceCard() {
    final out = _out;
    final reading = out != null && out['text'] == _text.text.trim() ? out['source_reading'] as String? ?? '' : '';
    return Container(
      padding: EdgeInsets.fromLTRB(14.w, 6.h, 10.w, 10.h),
      decoration: _box(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        TextField(
          controller: _text,
          maxLength: _max,
          minLines: 3,
          maxLines: 8,
          textInputAction: TextInputAction.done,
          onSubmitted: (_) => _translate(),
          onChanged: (_) => setState(() {}),
          style: TextStyle(fontSize: 18.sp, locale: localeFor(_source)),
          decoration: InputDecoration(
            border: InputBorder.none,
            hintText: _listening ? 'Đang nghe…' : 'Nhập hoặc bấm mic để nói',
          ),
        ),
        if (reading.isNotEmpty) Text(reading, style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
        Row(children: [
          IconButton.filled(
            onPressed: () => _talk(false),
            style: IconButton.styleFrom(backgroundColor: _listening ? AppColors.beamCoral : AppColors.primary),
            tooltip: _listening ? 'Dừng nghe' : 'Nói bằng ${_label(_source)}',
            icon: Icon(_listening ? Icons.graphic_eq_rounded : Icons.mic_rounded),
          ),
          if (_text.text.trim().isNotEmpty)
            IconButton(onPressed: () => _say(_text.text, _source), tooltip: 'Nghe câu gốc', icon: const Icon(Icons.volume_up_rounded)),
          const Spacer(),
          FilledButton(
            onPressed: _busy || _text.text.trim().isEmpty ? null : () => _translate(),
            child: _busy
                ? SizedBox(width: 18.w, height: 18.w, child: const CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Dịch'),
          ),
        ]),
      ]),
    );
  }

  Widget _resultCard() {
    final out = _out;
    final translation = out?['translation'] as String? ?? '';
    final reading = out?['reading'] as String? ?? '';
    final language = out?['target'] as String? ?? _target;
    return Container(
      constraints: BoxConstraints(minHeight: 120.h),
      padding: EdgeInsets.fromLTRB(14.w, 12.h, 10.w, 10.h),
      decoration: _box(AppColors.primary.withValues(alpha: 0.06)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        if (_error.isNotEmpty)
          Text(_error, style: TextStyle(color: AppColors.error, fontSize: 14.sp))
        else if (out == null)
          Text('Bản dịch', style: TextStyle(color: AppColors.textSecondary, fontSize: 18.sp))
        else ...[
          SelectableText(translation, style: TextStyle(fontSize: 18.sp, color: AppColors.textPrimary, locale: localeFor(language))),
          if (reading.isNotEmpty) ...[
            SizedBox(height: 4.h),
            Text(reading, style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
          ],
        ],
        SizedBox(height: 8.h),
        Row(children: [
          IconButton.outlined(
            onPressed: () => _talk(true),
            tooltip: 'Người kia nói bằng ${_label(_target)}',
            icon: const Icon(Icons.mic_none_rounded),
          ),
          if (out != null) ...[
            IconButton(onPressed: () => _say(translation, language), tooltip: 'Nghe bản dịch', icon: const Icon(Icons.volume_up_rounded)),
            IconButton(
              onPressed: () {
                Clipboard.setData(ClipboardData(text: translation));
                Get.snackbar('Đã chép', translation, snackPosition: SnackPosition.BOTTOM);
              },
              tooltip: 'Chép bản dịch',
              icon: const Icon(Icons.copy_rounded),
            ),
            const Spacer(),
            Container(
              padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
              decoration: BoxDecoration(
                  color: AppColors.surface, borderRadius: BorderRadius.circular(6.r), border: Border.all(color: AppColors.line)),
              child: Text('Bản dịch máy', style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w700, color: AppColors.textSecondary)),
            ),
          ],
        ]),
      ]),
    );
  }

  List<Widget> _words() {
    final words = (_out?['words'] as List? ?? const []).cast<Map>();
    if (words.isEmpty) return const [];
    return [
      SizedBox(height: 16.h),
      Text('Từ đã kiểm duyệt trong câu', style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
      SizedBox(height: 8.h),
      for (final w in words)
        Container(
          margin: EdgeInsets.only(bottom: 8.h),
          padding: EdgeInsets.fromLTRB(14.w, 8.h, 8.w, 8.h),
          decoration: _box(),
          child: Row(children: [
            Expanded(
              child: InkWell(
                onTap: () => _say(w['text'] as String, w['language'] as String),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Flexible(
                      child: LangText(w['text'] as String,
                          language: w['language'] as String,
                          style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                    ),
                    SizedBox(width: 6.w),
                    Icon(Icons.volume_up_rounded, size: 18.sp, color: AppColors.primary),
                  ]),
                  Text(
                    [
                      if ((w['reading'] as String? ?? '').isNotEmpty) w['language'] == 'en' ? '/${w['reading']}/' : w['reading'] as String,
                      w['meaning_vi'] as String? ?? '',
                    ].where((s) => s.isNotEmpty).join(' · '),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary),
                  ),
                ]),
              ),
            ),
            _saved.contains(w['word_id'])
                ? TextButton.icon(onPressed: null, icon: const Icon(Icons.check_rounded), label: const Text('Đã lưu'))
                : OutlinedButton.icon(onPressed: () => _save(w), icon: const Icon(Icons.add_rounded), label: const Text('Lưu')),
          ]),
        ),
    ];
  }
}
