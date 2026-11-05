import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

import '../../data/models/api/speech.dart';
import '../../data/repositories/repositories.dart';
import '../network/api_client.dart';
import '../theme/app_colors.dart';
import 'target_word.dart';

/// "Chấm chi tiết": record the learner (16 kHz mono WAV, at most 7 s), the server scores it phone by phone
/// (BE apps.speech) and the result shows which syllable / sound was wrong and how to fix it.
class PronunciationCheck extends StatefulWidget {
  const PronunciationCheck({super.key, this.translationId, this.sentenceId, required this.language, this.onScore});

  final int? translationId;
  final int? sentenceId;
  final String language; // vi | en | zh-Hans | zh-Hant
  final ValueChanged<int>? onScore;

  @override
  State<PronunciationCheck> createState() => _PronunciationCheckState();
}

enum _Phase { idle, recording, scoring }

class _PronunciationCheckState extends State<PronunciationCheck> {
  static const _maxSeconds = 7;
  final _recorder = AudioRecorder();
  _Phase _phase = _Phase.idle;
  PronunciationResult? _result;
  String _error = '';
  Timer? _limit;
  int _elapsed = 0;

  @override
  void didUpdateWidget(covariant PronunciationCheck old) {
    super.didUpdateWidget(old);
    if (old.translationId != widget.translationId || old.sentenceId != widget.sentenceId) {
      _result = null;
      _error = '';
    }
  }

  @override
  void dispose() {
    _limit?.cancel();
    _recorder.dispose();
    super.dispose();
  }

  Future<void> _tap() async {
    if (_phase == _Phase.scoring) return;
    if (_phase == _Phase.recording) return _stop();
    if (!await _recorder.hasPermission()) {
      setState(() => _error = 'Hãy cho phép LingoPrism dùng micro trong Cài đặt để luyện nói.');
      return;
    }
    final dir = await getTemporaryDirectory();
    final path = '${dir.path}/speak_${DateTime.now().millisecondsSinceEpoch}.wav';
    await _recorder.start(const RecordConfig(encoder: AudioEncoder.wav, sampleRate: 16000, numChannels: 1), path: path);
    setState(() {
      _phase = _Phase.recording;
      _error = '';
      _result = null;
      _elapsed = 0;
    });
    _limit = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) return t.cancel();
      setState(() => _elapsed++);
      if (_elapsed >= _maxSeconds) _stop();
    });
  }

  Future<void> _stop() async {
    _limit?.cancel();
    final path = await _recorder.stop();
    if (!mounted) return;
    if (path == null) {
      setState(() => _phase = _Phase.idle);
      return;
    }
    setState(() => _phase = _Phase.scoring);
    try {
      final r = await SpeechRepository.assess(path, translationId: widget.translationId, sentenceId: widget.sentenceId);
      if (!mounted) return;
      setState(() => _result = r);
      widget.onScore?.call(r.score);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.isNetwork ? 'Không kết nối được máy chủ.' : e.message);
    } finally {
      unawaited(File(path).delete().then((_) => null, onError: (_) => null));
      if (mounted) setState(() => _phase = _Phase.idle);
    }
  }

  Color _color(String status) => switch (status) {
        'right' || 'ok' => AppColors.success,
        'close' => AppColors.beamAmber,
        _ => AppColors.error,
      };

  @override
  Widget build(BuildContext context) {
    final r = _result;
    return Column(mainAxisSize: MainAxisSize.min, children: [
      FilledButton.icon(
        onPressed: _phase == _Phase.scoring ? null : _tap,
        style: FilledButton.styleFrom(
          backgroundColor: _phase == _Phase.recording ? AppColors.beamCoral : AppColors.primary,
          padding: EdgeInsets.symmetric(horizontal: 22.w, vertical: 14.h),
        ),
        icon: _phase == _Phase.scoring
            ? SizedBox(width: 18.w, height: 18.w, child: const CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
            : Icon(_phase == _Phase.recording ? Icons.stop_rounded : Icons.mic_rounded),
        label: Text(switch (_phase) {
          _Phase.recording => 'Đang ghi… ${_maxSeconds - _elapsed}s (chạm để dừng)',
          _Phase.scoring => 'Đang chấm từng âm…',
          _Phase.idle => r == null ? 'Bấm và đọc to' : 'Đọc lại',
        }),
      ),
      if (_error.isNotEmpty) ...[
        SizedBox(height: 10.h),
        Text(_error, textAlign: TextAlign.center, style: TextStyle(color: AppColors.error, fontSize: 13.sp)),
      ],
      if (r != null) ...[SizedBox(height: 16.h), _ResultView(result: r, language: widget.language, color: _color)],
    ]);
  }
}

class _ResultView extends StatelessWidget {
  const _ResultView({required this.result, required this.language, required this.color});
  final PronunciationResult result;
  final String language;
  final Color Function(String) color;

  bool get _zh => language.startsWith('zh');

  String _toneName(String t) => _zh ? 'thanh $t' : t;

  void _details(BuildContext context, SpeechUnit u, int index) {
    final tips = result.errors.where((e) => e.unit == index).toList();
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (_) => SafeArea(
        child: ListView(shrinkWrap: true, padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 20.h), children: [
          Text(u.text,
              style: TextStyle(fontSize: 30.sp, fontWeight: FontWeight.w800, color: color(u.status), locale: _zh ? localeFor(language) : null)),
          if (u.reading.isNotEmpty) Text(u.reading, style: TextStyle(color: AppColors.textSecondary, fontSize: 14.sp)),
          SizedBox(height: 12.h),
          Text('Từng âm (âm đúng → máy nghe được)', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14.sp)),
          SizedBox(height: 6.h),
          Wrap(spacing: 8.w, runSpacing: 8.h, children: [
            for (final p in u.phones)
              Container(
                padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 6.h),
                decoration: BoxDecoration(
                  color: color(p.status).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10.r),
                  border: Border.all(color: color(p.status)),
                ),
                child: Text(p.status == 'ok' ? '/${p.expected}/' : '/${p.expected}/ → ${p.heard == null ? 'thiếu' : '/${p.heard}/'}',
                    style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w600)),
              ),
          ]),
          if (u.tone != null) ...[
            SizedBox(height: 12.h),
            Text(
              'Thanh điệu (thử nghiệm): cần ${_toneName(u.tone!.expected)}, máy nghe ${_toneName(u.tone!.heard)}',
              style: TextStyle(color: color(u.tone!.status), fontWeight: FontWeight.w600),
            ),
          ],
          for (final e in tips) ...[SizedBox(height: 10.h), _Tip(error: e)],
        ]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = result;
    final verdict = switch (r.verdict) { 'right' => 'Phát âm chuẩn!', 'close' => 'Gần đúng rồi', _ => 'Chưa đúng' };
    return Column(children: [
      Text('$verdict  ${r.score}/100', style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800, color: color(r.verdict))),
      SizedBox(height: 8.h),
      Wrap(alignment: WrapAlignment.center, spacing: 8.w, runSpacing: 6.h, children: [
        _Chip('Âm', r.phoneScore),
        if (r.toneScore != null) _Chip('Thanh điệu*', r.toneScore!),
        _Chip('Đầy đủ', r.completeness),
      ]),
      SizedBox(height: 14.h),
      Wrap(alignment: WrapAlignment.center, spacing: 10.w, runSpacing: 10.h, children: [
        for (final (i, u) in r.units.indexed)
          InkWell(
            borderRadius: BorderRadius.circular(12.r),
            onTap: () => _details(context, u, i),
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 6.h),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12.r),
                border: Border(bottom: BorderSide(color: color(u.status), width: 3)),
              ),
              child: Column(children: [
                Text(u.text,
                    style: TextStyle(
                        fontSize: 24.sp, fontWeight: FontWeight.w800, color: color(u.status), locale: _zh ? localeFor(language) : null)),
                if (u.reading.isNotEmpty && _zh) Text(u.reading, style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
              ]),
            ),
          ),
      ]),
      SizedBox(height: 6.h),
      Text('Chạm vào một chữ để xem từng âm', style: TextStyle(fontSize: 12.sp, color: AppColors.textHint)),
      for (final e in r.errors.take(3)) ...[SizedBox(height: 10.h), _Tip(error: e)],
      if (r.toneScore != null)
        Padding(
          padding: EdgeInsets.only(top: 8.h),
          child: Text('* Chấm thanh điệu theo cao độ giọng – đang thử nghiệm, có thể chưa chính xác.',
              textAlign: TextAlign.center, style: TextStyle(fontSize: 11.sp, color: AppColors.textHint)),
        ),
    ]);
  }
}

class _Chip extends StatelessWidget {
  const _Chip(this.label, this.value);
  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    final c = value >= 90 ? AppColors.success : value >= 60 ? AppColors.beamAmber : AppColors.error;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 5.h),
      decoration: BoxDecoration(color: c.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20.r)),
      child: Text('$label $value', style: TextStyle(color: c, fontWeight: FontWeight.w700, fontSize: 13.sp)),
    );
  }
}

class _Tip extends StatelessWidget {
  const _Tip({required this.error});
  final SpeechError error;

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: EdgeInsets.all(12.w),
        decoration: BoxDecoration(
          color: (error.major ? AppColors.errorSoft : AppColors.beamAmber.withValues(alpha: 0.12)),
          borderRadius: BorderRadius.circular(12.r),
        ),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Icon(Icons.lightbulb_rounded, size: 20.w, color: error.major ? AppColors.error : AppColors.beamAmber),
          SizedBox(width: 8.w),
          Expanded(child: Text(error.tip, style: TextStyle(fontSize: 14.sp, color: AppColors.textPrimary))),
        ]),
      );
}
