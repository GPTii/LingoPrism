import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

import '../theme/app_colors.dart';
import 'target_word.dart';

/// Result of comparing what the phone heard with the expected word – same rules as the web
/// (FE/src/lib/pronounce.ts): Chinese compares characters, other languages letters.
class SpeakScore {
  SpeakScore(this.score, this.heard, this.units);
  final int score; // 0–100
  final String heard;
  final List<(String, bool)> units; // each unit of the expected text: heard right or not
  String get verdict => score >= 90 ? 'right' : score >= 50 ? 'close' : 'wrong';
}

String _normalise(String text, String language) {
  final t = text.toLowerCase().replaceAll(RegExp(r'[\p{P}\p{S}]', unicode: true), '');
  return language.startsWith('zh') ? t.replaceAll(RegExp(r'\s+'), '') : t.replaceAll(RegExp(r'\s+'), ' ').trim();
}

int _levenshtein(List<String> a, List<String> b) {
  final dp = List.generate(a.length + 1, (i) => List<int>.filled(b.length + 1, 0)..[0] = i);
  for (var j = 1; j <= b.length; j++) {
    dp[0][j] = j;
  }
  for (var i = 1; i <= a.length; i++) {
    for (var j = 1; j <= b.length; j++) {
      dp[i][j] = math.min(math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1), dp[i - 1][j - 1] + (a[i - 1] == b[j - 1] ? 0 : 1));
    }
  }
  return dp[a.length][b.length];
}

SpeakScore scoreSpeech(String expected, List<String> alternatives, String language) {
  final want = _normalise(expected, language);
  List<String> split(String s) => (language.startsWith('zh') ? s : s.replaceAll(' ', '')).characters.toList();
  var best = SpeakScore(0, alternatives.isEmpty ? '' : alternatives.first, [for (final u in split(want)) (u, false)]);
  for (final alt in alternatives) {
    final got = _normalise(alt, language);
    final a = split(want), b = split(got);
    final s = (got == want || (want.isNotEmpty && got.contains(want)))
        ? 100
        : math.max(0, (100 * (1 - _levenshtein(a, b) / math.max(math.max(a.length, b.length), 1))).round());
    if (s > best.score) {
      final heardSet = b.toSet();
      best = SpeakScore(s, alt, [for (final u in a) (u, s == 100 || heardSet.contains(u))]);
    }
  }
  return best;
}

/// "Nói thử": say the word into the phone, get a score and see which parts were heard right.
class SpeakCheck extends StatefulWidget {
  const SpeakCheck({super.key, required this.text, required this.language, required this.locale, this.onScore});

  final String text;
  final String language; // vi | en | zh-Hans | zh-Hant
  final String locale; // en-US, zh-CN, zh-TW, vi-VN
  final ValueChanged<SpeakScore>? onScore;

  @override
  State<SpeakCheck> createState() => _SpeakCheckState();
}

class _SpeakCheckState extends State<SpeakCheck> {
  static final SpeechToText _stt = SpeechToText();
  static bool? _available;
  bool _listening = false;
  SpeakScore? _result;
  String _error = '';

  @override
  void didUpdateWidget(covariant SpeakCheck old) {
    super.didUpdateWidget(old);
    if (old.text != widget.text) {
      _result = null;
      _error = '';
    }
  }

  @override
  void dispose() {
    if (_listening) _stt.cancel();
    super.dispose();
  }

  Future<void> _go() async {
    if (_listening) {
      await _stt.stop();
      return;
    }
    setState(() {
      _error = '';
      _result = null;
    });
    _available ??= await _stt.initialize(onError: (e) {
      if (!mounted) return;
      setState(() {
        _listening = false;
        _error = e.errorMsg.contains('no_match') || e.errorMsg.contains('speech_timeout')
            ? 'Chưa nghe rõ. Bấm mic rồi đọc to, rõ hơn nhé.'
            : 'Không nhận dạng được giọng nói, thử lại nhé.';
      });
    });
    if (_available != true) {
      setState(() => _error = 'Điện thoại chưa cho phép dùng micro hoặc chưa có nhận dạng giọng nói.');
      return;
    }
    setState(() => _listening = true);
    await _stt.listen(
      listenOptions: SpeechListenOptions(
        localeId: widget.locale.replaceAll('-', '_'),
        listenFor: const Duration(seconds: 6),
        pauseFor: const Duration(seconds: 2),
        partialResults: false,
        cancelOnError: true,
      ),
      onResult: (SpeechRecognitionResult r) {
        if (!r.finalResult || !mounted) return;
        final alts = r.alternates.map((a) => a.recognizedWords).toList();
        final s = scoreSpeech(widget.text, alts, widget.language);
        setState(() {
          _listening = false;
          _result = s;
        });
        widget.onScore?.call(s);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = _result;
    final color = r == null ? null : {'right': AppColors.success, 'close': AppColors.beamAmber, 'wrong': AppColors.error}[r.verdict];
    return Column(mainAxisSize: MainAxisSize.min, children: [
      FilledButton.icon(
        onPressed: _go,
        style: FilledButton.styleFrom(backgroundColor: _listening ? AppColors.beamCoral : AppColors.primary),
        icon: Icon(_listening ? Icons.graphic_eq_rounded : Icons.mic_rounded),
        label: Text(_listening ? 'Đang nghe… (chạm để dừng)' : 'Nói thử'),
      ),
      if (r != null) ...[
        SizedBox(height: 10.h),
        Text(
          '${r.verdict == 'right' ? 'Phát âm chuẩn!' : r.verdict == 'close' ? 'Gần đúng rồi' : 'Chưa đúng'}  ${r.score}/100',
          style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w800, color: color),
        ),
        SizedBox(height: 4.h),
        Text.rich(
          TextSpan(children: [
            for (final (u, ok) in r.units)
              TextSpan(
                text: u,
                style: TextStyle(
                  color: ok ? AppColors.success : AppColors.error,
                  decoration: ok ? null : TextDecoration.underline,
                  decorationThickness: 2,
                ),
              ),
          ]),
          style: TextStyle(fontSize: 22.sp, fontWeight: FontWeight.w700, locale: widget.language.startsWith('zh') ? localeFor(widget.language) : null),
        ),
        if (r.verdict != 'right' && r.heard.isNotEmpty)
          Text('Máy nghe thành: ${r.heard}', style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
      ],
      if (_error.isNotEmpty) ...[
        SizedBox(height: 8.h),
        Text(_error, textAlign: TextAlign.center, style: TextStyle(color: AppColors.error, fontSize: 13.sp)),
      ],
    ]);
  }
}
