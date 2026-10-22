import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/prismo.dart';
import '../../core/widgets/speak_check.dart';
import '../../core/widgets/target_word.dart';
import '../../core/widgets/word_picture.dart';
import '../../data/models/api/vocab.dart';
import '../../data/repositories/repositories.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

/// Luyện phát âm (same as the web's /speak): ten words from my library, one at a time –
/// listen to the model voice, say it, see the score; an average at the end.
class SpeakPracticeView extends StatefulWidget {
  const SpeakPracticeView({super.key});

  @override
  State<SpeakPracticeView> createState() => _SpeakPracticeViewState();
}

class _SpeakPracticeViewState extends State<SpeakPracticeView> {
  static const _round = 10;
  late Future<List<WordCard>> _deck = _load();
  int _index = 0;
  final Map<int, int> _scores = {};

  Future<List<WordCard>> _load() async {
    final words = (await VocabRepository.myWords()).where((c) => c.target != null && c.target!.ttsLocale.isNotEmpty).toList()
      ..shuffle();
    return words.take(_round).toList();
  }

  void _again() => setState(() {
        _deck = _load();
        _index = 0;
        _scores.clear();
      });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Luyện phát âm')),
      body: FutureBuilder<List<WordCard>>(
        future: _deck,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          final deck = snap.data ?? const <WordCard>[];
          if (deck.isEmpty) {
            return const _Message(
              mood: PrismoMood.wow,
              title: 'Thư viện của bạn chưa có từ nào',
              body: 'Lưu vài từ từ một chủ đề hoặc chụp ảnh một đồ vật, rồi quay lại luyện phát âm.',
            );
          }
          if (_index >= deck.length) {
            final avg = _scores.isEmpty ? 0 : (_scores.values.reduce((a, b) => a + b) / _scores.length).round();
            return _Message(
              mood: avg >= 80 ? PrismoMood.celebrate : avg >= 50 ? PrismoMood.happy : PrismoMood.think,
              title: 'Điểm phát âm trung bình: $avg/100',
              body: avg >= 80 ? 'Rất tốt! Giọng bạn đã rõ ràng.' : 'Nghe lại giọng mẫu thật chậm rồi thử lại, nhất là phần gạch đỏ.',
              action: FilledButton(onPressed: _again, child: const Text('Luyện thêm 10 từ')),
            );
          }
          final c = deck[_index];
          final t = c.target!;
          return ListView(
            padding: EdgeInsets.fromLTRB(20.w, 12.h, 20.w, 32.h),
            children: [
              Row(children: [
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8.r),
                    child: LinearProgressIndicator(value: _index / deck.length, minHeight: 8.h),
                  ),
                ),
                SizedBox(width: 10.w),
                Text('${_index + 1}/${deck.length}', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textSecondary)),
              ]),
              SizedBox(height: 16.h),
              Container(
                padding: EdgeInsets.all(20.w),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(20.r),
                  border: Border.fromBorderSide(BorderSide(color: AppColors.line)),
                ),
                child: Column(children: [
                  WordPicture(imageUrl: c.image, emoji: c.emoji, size: 140.w),
                  SizedBox(height: 12.h),
                  TargetWordView(target: t, fontSize: 40.sp),
                  SizedBox(height: 6.h),
                  Text(c.meaningVi, style: TextStyle(fontSize: 16.sp, color: AppColors.textSecondary)),
                  SizedBox(height: 18.h),
                  SpeakCheck(
                    key: ValueKey(c.id),
                    text: t.text,
                    language: t.language,
                    locale: t.ttsLocale,
                    onScore: (s) => setState(() => _scores[c.id] = (_scores[c.id] ?? 0) > s.score ? _scores[c.id]! : s.score),
                  ),
                ]),
              ),
              SizedBox(height: 16.h),
              _scores.containsKey(c.id)
                  ? FilledButton(onPressed: () => setState(() => _index++), child: const Text('Từ tiếp theo'))
                  : OutlinedButton(onPressed: () => setState(() => _index++), child: const Text('Bỏ qua từ này')),
            ],
          );
        },
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({required this.mood, required this.title, required this.body, this.action});
  final PrismoMood mood;
  final String title, body;
  final Widget? action;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: EdgeInsets.all(28.w),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Prismo(mood: mood, size: 120.w),
            SizedBox(height: 12.h),
            Text(title, textAlign: TextAlign.center, style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
            SizedBox(height: 8.h),
            Text(body, textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary)),
            if (action != null) ...[SizedBox(height: 18.h), action!],
            SizedBox(height: 8.h),
            const TextButton(onPressed: goBack, child: Text('Quay lại')),
          ]),
        ),
      );
}
