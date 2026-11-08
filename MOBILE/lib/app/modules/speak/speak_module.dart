import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/prismo.dart';
import '../../core/widgets/pronunciation_check.dart';
import '../../core/widgets/speak_check.dart';
import '../../core/widgets/target_word.dart';
import '../../core/widgets/word_picture.dart';
import '../../data/models/api/speech.dart';
import '../../data/models/api/vocab.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/tts_service.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

/// Luyện phát âm (same as the web's /speak): ten words – or their example sentences – from my library, one at a time:
/// listen to the model voice, say it, see the score; an average at the end. When the server scores recordings
/// (BE apps.speech) each sound and tone is checked (PronunciationCheck); otherwise the phone's speech recogniser
/// compares the words (SpeakCheck).
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
  final Future<Set<String>> _detailedLanguages = SpeechRepository.languages();
  late final Future<bool> _detailed = _detailedLanguages.then((l) => l.isNotEmpty);
  bool _sentences = false;

  Future<List<WordCard>> _load() async {
    final words = (await VocabRepository.myWords())
        .where((c) => c.target != null && c.target!.ttsLocale.isNotEmpty && (!_sentences || _sentence(c) != null))
        .toList()
      ..shuffle();
    return words.take(_round).toList();
  }

  static ExampleSentence? _sentence(WordCard c) => c.examples.where((e) => e.id > 0 && e.text.length <= 120).firstOrNull;

  void _mode(bool sentences) => setState(() {
        _sentences = sentences;
        _deck = _load();
        _index = 0;
        _scores.clear();
      });

  void _again() => setState(() {
        _deck = _load();
        _index = 0;
        _scores.clear();
      });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Luyện phát âm'), actions: [
        FutureBuilder<bool>(
          future: _detailed,
          builder: (context, on) => on.data == true
              ? IconButton(
                  tooltip: 'Tiến bộ phát âm',
                  icon: const Icon(Icons.insights_rounded),
                  onPressed: () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => const SpeechProgressView())),
                )
              : const SizedBox.shrink(),
        ),
      ]),
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
              mood: avg >= 80
                  ? PrismoMood.celebrate
                  : avg >= 50
                      ? PrismoMood.happy
                      : PrismoMood.think,
              title: 'Điểm phát âm trung bình: $avg/100',
              body: avg >= 80 ? 'Rất tốt! Giọng bạn đã rõ ràng.' : 'Nghe lại giọng mẫu thật chậm rồi thử lại, nhất là phần gạch đỏ.',
              action: FilledButton(onPressed: _again, child: const Text('Luyện thêm 10 từ')),
            );
          }
          final c = deck[_index];
          final t = c.target!;
          final sentence = _sentence(c);
          void score(int s) => setState(() => _scores[c.id] = (_scores[c.id] ?? 0) > s ? _scores[c.id]! : s);
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
              FutureBuilder<Set<String>>(
                future: _detailedLanguages,
                builder: (context, on) => !(on.data ?? const {}).contains(t.language)
                    ? const SizedBox.shrink()
                    : Padding(
                        padding: EdgeInsets.only(top: 12.h),
                        child: SegmentedButton<bool>(
                          segments: const [
                            ButtonSegment(value: false, label: Text('Từ'), icon: Icon(Icons.abc_rounded)),
                            ButtonSegment(value: true, label: Text('Câu'), icon: Icon(Icons.short_text_rounded)),
                          ],
                          selected: {_sentences},
                          onSelectionChanged: (v) => _mode(v.first),
                        ),
                      ),
              ),
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
                  if (_sentences && sentence != null) ...[
                    SizedBox(height: 14.h),
                    Text(sentence.text,
                        textAlign: TextAlign.center,
                        style: TextStyle(
                            fontSize: 22.sp,
                            fontWeight: FontWeight.w700,
                            locale: t.language.startsWith('zh') ? localeFor(t.language) : null)),
                    if (sentence.transliteration.isNotEmpty)
                      Text(sentence.transliteration,
                          textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary, fontSize: 14.sp)),
                    if (sentence.translationVi.isNotEmpty)
                      Text(sentence.translationVi,
                          textAlign: TextAlign.center, style: TextStyle(color: AppColors.textHint, fontSize: 13.sp)),
                    TextButton.icon(
                      onPressed: () => TtsService.to.speak(sentence.text, t.ttsLocale),
                      icon: const Icon(Icons.volume_up_rounded),
                      label: const Text('Nghe câu mẫu'),
                    ),
                  ],
                  SizedBox(height: 18.h),
                  FutureBuilder<Set<String>>(
                    future: _detailedLanguages,
                    builder: (context, on) => on.connectionState != ConnectionState.done
                        ? const SizedBox(height: 48)
                        : (on.data ?? const {}).contains(t.language) && !(_sentences && sentence == null)
                            ? PronunciationCheck(
                                key: ValueKey('${c.id}-$_sentences'),
                                translationId: _sentences ? null : t.id,
                                sentenceId: _sentences ? sentence?.id : null,
                                language: t.language,
                                onScore: score,
                              )
                            : SpeakCheck(
                                key: ValueKey(c.id),
                                text: t.text,
                                language: t.language,
                                locale: t.ttsLocale,
                                onScore: (s) => score(s.score),
                              ),
                  ),
                ]),
              ),
              SizedBox(height: 16.h),
              _scores.containsKey(c.id)
                  ? FilledButton(onPressed: () => setState(() => _index++), child: Text(_sentences ? 'Câu tiếp theo' : 'Từ tiếp theo'))
                  : OutlinedButton(onPressed: () => setState(() => _index++), child: Text(_sentences ? 'Bỏ qua câu này' : 'Bỏ qua từ này')),
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
            Text(title,
                textAlign: TextAlign.center, style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
            SizedBox(height: 8.h),
            Text(body, textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary)),
            if (action != null) ...[SizedBox(height: 18.h), action!],
            SizedBox(height: 8.h),
            const TextButton(onPressed: goBack, child: Text('Quay lại')),
          ]),
        ),
      );
}

/// Tiến bộ phát âm: average of the last 7 days, score per day, the sounds most often wrong (with the tip).
class SpeechProgressView extends StatelessWidget {
  const SpeechProgressView({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(title: const Text('Tiến bộ phát âm')),
        body: FutureBuilder<SpeechProgress>(
          future: SpeechRepository.progress(),
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
            final p = snap.data;
            if (p == null || p.attempts == 0) {
              return const _Message(
                mood: PrismoMood.think,
                title: 'Chưa có lượt luyện nói nào',
                body: 'Luyện vài từ ở màn Luyện phát âm, điểm và các âm hay sai sẽ hiện ở đây.',
              );
            }
            final days = p.byDay.length > 14 ? p.byDay.sublist(p.byDay.length - 14) : p.byDay;
            final maxCount = days.fold<int>(1, (m, d) => d.$3 > m ? d.$3 : m);
            return ListView(padding: EdgeInsets.all(20.w), children: [
              Text('Trung bình 7 ngày: ${p.average7d ?? '–'}/100',
                  style: TextStyle(fontSize: 22.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
              Text('${p.attempts} lượt trong 60 ngày', style: TextStyle(color: AppColors.textSecondary)),
              SizedBox(height: 16.h),
              SizedBox(
                height: 120.h,
                child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
                  for (final d in days)
                    Expanded(
                      child: Tooltip(
                        message: '${d.$1}: ${d.$2}/100 (${d.$3} lượt)',
                        child: Container(
                          margin: EdgeInsets.symmetric(horizontal: 2.w),
                          height: 110.h * d.$2 / 100,
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.35 + 0.65 * d.$3 / maxCount),
                            borderRadius: BorderRadius.vertical(top: Radius.circular(6.r)),
                          ),
                        ),
                      ),
                    ),
                ]),
              ),
              SizedBox(height: 20.h),
              Text('Âm bạn hay sai', style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w800)),
              for (final w in p.weak)
                Card(
                  margin: EdgeInsets.only(top: 10.h),
                  child: ListTile(
                    title: Text(w.heard == null ? 'Thiếu /${w.expected}/' : '/${w.expected}/ → /${w.heard}/',
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    subtitle: Text(w.tip),
                    trailing: Text('${w.count}×', style: TextStyle(color: AppColors.textSecondary)),
                  ),
                ),
              SizedBox(height: 20.h),
              Text('Lần gần đây', style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w800)),
              for (final r in p.recent) ListTile(dense: true, title: Text(r.$1), trailing: Text('${r.$2}/100')),
            ]);
          },
        ),
      );
}
