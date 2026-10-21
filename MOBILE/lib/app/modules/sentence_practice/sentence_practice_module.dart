import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/target_word.dart';
import '../../data/models/api/sentence.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/auth_service.dart';
import '../../data/services/game_service.dart';
import '../../data/services/tts_service.dart';

/// Sentence practice (arrange / listen / fill / meaning) built from verified Tatoeba sentences.
/// Arguments: `{'topic': int?, 'title': String?}`.
class SentencePracticeController extends GetxController {
  int? topic;
  String title = 'Luyện câu';

  final Rxn<SentenceLesson> lesson = Rxn<SentenceLesson>();
  final RxString error = ''.obs;
  final RxInt index = 0.obs;
  final RxList<int> picked = <int>[].obs; // tile indexes in answer order
  final Rxn<SentenceCheck> result = Rxn<SentenceCheck>();
  final RxBool checking = false.obs;
  final RxInt correctCount = 0.obs;
  final RxInt xp = 0.obs;
  DateTime _started = DateTime.now();

  List<SentenceExercise> get exercises => lesson.value?.exercises ?? const [];
  SentenceExercise? get current => index.value < exercises.length ? exercises[index.value] : null;
  String get language => lesson.value?.language ?? '';
  bool get finished => lesson.value != null && exercises.isNotEmpty && index.value >= exercises.length;

  @override
  void onInit() {
    super.onInit();
    final args = Get.arguments;
    if (args is Map) {
      topic = args['topic'] as int?;
      title = (args['title'] as String?) ?? title;
    }
    load();
  }

  Future<void> load() async {
    error.value = '';
    lesson.value = null;
    index.value = 0;
    correctCount.value = 0;
    xp.value = 0;
    try {
      lesson.value = await SentenceRepository.lesson(topic: topic, size: 10);
      _onShow();
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
    }
  }

  void _onShow() {
    picked.clear();
    result.value = null;
    _started = DateTime.now();
    final ex = current;
    if (ex != null && ex.type == 'listen') playPrompt();
  }

  void playPrompt() {
    final ex = current;
    if (ex != null && ex.ttsText.isNotEmpty) TtsService.to.speak(ex.ttsText, ex.ttsLocale);
  }

  void pickTile(int i) {
    if (result.value == null && !picked.contains(i)) picked.add(i);
  }

  void unpick(int position) {
    if (result.value == null) picked.removeAt(position);
  }

  Future<void> submit(Object answer) async {
    final ex = current;
    if (ex == null || result.value != null || checking.value) return;
    checking.value = true;
    try {
      final r = await SentenceRepository.check(
        sentence: ex.id,
        type: ex.type,
        answer: answer,
        responseMs: DateTime.now().difference(_started).inMilliseconds,
      );
      result.value = r;
      if (r.correct) {
        correctCount.value++;
        xp.value += r.xp;
      }
      TtsService.to.speak(r.sentence.text, r.sentence.ttsLocale);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      checking.value = false;
    }
  }

  void submitTiles() {
    final ex = current;
    if (ex == null || picked.length != ex.tiles.length) return;
    submit(picked.map((i) => ex.tiles[i].text).toList());
  }

  void next() {
    index.value++;
    if (finished) {
      if (Get.isRegistered<GameService>()) GameService.to.refreshSummary();
    } else {
      _onShow();
    }
  }
}

// ====================================================================== widgets

/// Sentence with the reading (pinyin, or zhuyin when enabled) above each Chinese word.
class TokenLine extends StatelessWidget {
  const TokenLine({super.key, required this.tokens, required this.language, this.highlight = const [], this.fontSize = 22});

  final List<SentenceToken> tokens;
  final String language;
  final List<int> highlight;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    final isZh = language.startsWith('zh');
    final zhuyin = AuthService.to.currentUser?.showZhuyin == true;
    final locale = localeFor(language);
    return Wrap(
      alignment: WrapAlignment.center,
      crossAxisAlignment: WrapCrossAlignment.end,
      spacing: isZh ? 2.w : 6.w,
      runSpacing: 6.h,
      children: [
        for (var i = 0; i < tokens.length; i++)
          if (tokens[i].blank)
            Container(
              width: 56.w,
              margin: EdgeInsets.symmetric(horizontal: 4.w),
              decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.buttonActive, width: 3))),
              child: Text(' ', style: TextStyle(fontSize: fontSize.sp)),
            )
          else
            Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (isZh)
                  Text(
                    tokens[i].punct ? ' ' : (zhuyin && tokens[i].zhuyin.isNotEmpty ? tokens[i].zhuyin : tokens[i].pinyin),
                    locale: zhuyin ? localeFor('zh-Hant') : null,
                    style: TextStyle(fontSize: 11.sp, color: AppColors.textSecondary),
                  ),
                Text(
                  tokens[i].text,
                  locale: locale,
                  style: TextStyle(
                    fontSize: fontSize.sp,
                    color: highlight.contains(i) ? AppColors.buttonActive : AppColors.textPrimary,
                    fontWeight: highlight.contains(i) ? FontWeight.w700 : FontWeight.w500,
                  ),
                ),
              ],
            ),
      ],
    );
  }
}

class SentenceCard extends StatelessWidget {
  const SentenceCard({super.key, required this.sentence, this.showTranslation = true, this.fontSize = 22});

  final Sentence sentence;
  final bool showTranslation;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    final t = sentence.translation;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Flexible(child: TokenLine(tokens: sentence.tokens, language: sentence.language, highlight: sentence.targetTokens, fontSize: fontSize)),
            IconButton(
              icon: const Icon(Icons.volume_up_rounded, color: AppColors.buttonActive),
              onPressed: () => TtsService.to.speak(sentence.text, sentence.ttsLocale),
            ),
          ],
        ),
        if (showTranslation && t != null) ...[
          SizedBox(height: 6.h),
          Text(t.text,
              textAlign: TextAlign.center, style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
        ],
        if (sentence.source.url.isNotEmpty)
          TextButton(
            onPressed: () => launchUrl(Uri.parse(sentence.source.url), mode: LaunchMode.externalApplication),
            child: Text(sentence.source.label, style: TextStyle(fontSize: 11.sp, color: Colors.grey)),
          ),
      ],
    );
  }
}

// ====================================================================== view

class SentencePracticeView extends GetView<SentencePracticeController> {
  const SentencePracticeView({super.key});

  static const _titles = {
    'arrange': 'Sắp xếp các từ thành câu đúng',
    'listen': 'Nghe và sắp xếp lại câu',
    'fill': 'Chọn từ còn thiếu',
    'meaning': 'Câu này có nghĩa là gì?',
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(title: Text(controller.title), backgroundColor: AppColors.appBarBackground),
      body: SafeArea(
        child: Obx(() {
          if (controller.error.isNotEmpty) return _message(controller.error.value, retry: true);
          final lesson = controller.lesson.value;
          if (lesson == null) return const Center(child: CircularProgressIndicator());
          if (lesson.exercises.isEmpty) {
            return _message('Chưa có câu luyện tập cho phần này.\n'
                'Câu chỉ lấy từ nguồn đã kiểm tra (Tatoeba, người bản xứ). Hãy học thêm từ hoặc chọn chủ đề khác.');
          }
          if (controller.finished) return _summary();
          return _exercise(controller.current!);
        }),
      ),
    );
  }

  Widget _message(String text, {bool retry = false}) => Center(
        child: Padding(
          padding: EdgeInsets.all(24.w),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(text, textAlign: TextAlign.center, style: TextStyle(fontSize: 15.sp)),
            SizedBox(height: 16.h),
            if (retry) ElevatedButton(onPressed: controller.load, child: const Text('Thử lại'))
            else ElevatedButton(onPressed: Get.back, child: const Text('Quay lại')),
          ]),
        ),
      );

  Widget _summary() => Center(
        child: Padding(
          padding: EdgeInsets.all(24.w),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text('🎉', style: TextStyle(fontSize: 56.sp)),
            SizedBox(height: 12.h),
            Text('Hoàn thành bài luyện câu!', style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w700)),
            SizedBox(height: 8.h),
            Text('Đúng ${controller.correctCount.value}/${controller.exercises.length} câu · +${controller.xp.value} XP',
                style: TextStyle(fontSize: 15.sp, color: AppColors.textSecondary)),
            SizedBox(height: 24.h),
            Row(mainAxisSize: MainAxisSize.min, children: [
              OutlinedButton(onPressed: Get.back, child: const Text('Về trước')),
              SizedBox(width: 12.w),
              ElevatedButton(onPressed: controller.load, child: const Text('Luyện tiếp')),
            ]),
          ]),
        ),
      );

  Widget _exercise(SentenceExercise ex) {
    final res = controller.result.value;
    final total = controller.exercises.length;
    return Column(
      children: [
        LinearProgressIndicator(value: controller.index.value / total, minHeight: 6.h, color: AppColors.buttonActive),
        Expanded(
          child: SingleChildScrollView(
            padding: EdgeInsets.all(16.w),
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.all(18.w),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20.r)),
              child: Column(
                children: [
                  Text(_titles[ex.type] ?? '', style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary, fontWeight: FontWeight.w600)),
                  SizedBox(height: 16.h),
                  if (ex.isTiles) _tiles(ex, res),
                  if (ex.type == 'fill') _fill(ex, res),
                  if (ex.type == 'meaning') _meaning(ex, res),
                ],
              ),
            ),
          ),
        ),
        if (res != null) _feedback(res),
      ],
    );
  }

  Widget _tiles(SentenceExercise ex, SentenceCheck? res) {
    final locale = localeFor(controller.language);
    final isZh = controller.language.startsWith('zh');
    final zhuyin = AuthService.to.currentUser?.showZhuyin == true;
    Widget tile(SentenceToken t, {bool reading = false, bool hidden = false, VoidCallback? onTap}) => Opacity(
          opacity: hidden ? 0 : 1,
          child: InkWell(
            onTap: hidden ? null : onTap,
            borderRadius: BorderRadius.circular(12.r),
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey.shade300, width: 2),
                borderRadius: BorderRadius.circular(12.r),
                color: Colors.white,
              ),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                if (reading) Text(zhuyin && t.zhuyin.isNotEmpty ? t.zhuyin : t.pinyin, style: TextStyle(fontSize: 10.sp, color: Colors.grey)),
                Text(t.text, locale: locale, style: TextStyle(fontSize: 18.sp)),
              ]),
            ),
          ),
        );
    return Column(children: [
      if (ex.type == 'arrange' && ex.prompt != null)
        Text(ex.prompt!.text, textAlign: TextAlign.center, style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w600)),
      if (ex.type == 'listen')
        IconButton.filled(iconSize: 36.sp, onPressed: controller.playPrompt, icon: const Icon(Icons.volume_up_rounded)),
      SizedBox(height: 16.h),
      Container(
        constraints: BoxConstraints(minHeight: 60.h),
        width: double.infinity,
        padding: EdgeInsets.only(bottom: 8.h),
        decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Colors.grey.shade300, width: 2))),
        child: Wrap(alignment: WrapAlignment.center, spacing: 8.w, runSpacing: 8.h, children: [
          for (var pos = 0; pos < controller.picked.length; pos++)
            tile(ex.tiles[controller.picked[pos]], onTap: () => controller.unpick(pos)),
        ]),
      ),
      SizedBox(height: 16.h),
      Wrap(alignment: WrapAlignment.center, spacing: 8.w, runSpacing: 8.h, children: [
        for (var i = 0; i < ex.tiles.length; i++)
          tile(ex.tiles[i], reading: isZh && ex.type == 'arrange', hidden: controller.picked.contains(i), onTap: () => controller.pickTile(i)),
      ]),
      SizedBox(height: 20.h),
      if (res == null)
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: controller.picked.length == ex.tiles.length && !controller.checking.value ? controller.submitTiles : null,
            child: Text(controller.checking.value ? 'Đang kiểm tra…' : 'Kiểm tra'),
          ),
        ),
    ]);
  }

  Widget _options(List<String> options, String? correct, {String? language, bool grid = true}) {
    final res = controller.result.value;
    Widget button(String opt) {
      final right = res != null && opt == correct;
      return InkWell(
        onTap: res == null ? () => controller.submit(opt) : null,
        borderRadius: BorderRadius.circular(16.r),
        child: Container(
          width: double.infinity,
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 14.h),
          decoration: BoxDecoration(
            color: right ? Colors.green.shade50 : Colors.white,
            border: Border.all(color: right ? Colors.green : Colors.grey.shade300, width: 2),
            borderRadius: BorderRadius.circular(16.r),
          ),
          child: language != null
              ? LangText(opt, language: language, textAlign: TextAlign.center, style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w600))
              : Text(opt, style: TextStyle(fontSize: 15.sp)),
        ),
      );
    }

    if (!grid) {
      return Column(children: [for (final o in options) Padding(padding: EdgeInsets.only(bottom: 10.h), child: button(o))]);
    }
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 10.h,
      crossAxisSpacing: 10.w,
      childAspectRatio: 2.4,
      children: [for (final o in options) button(o)],
    );
  }

  Widget _fill(SentenceExercise ex, SentenceCheck? res) => Column(children: [
        TokenLine(tokens: ex.tokens, language: controller.language),
        SizedBox(height: 10.h),
        if (ex.prompt != null)
          Text(ex.prompt!.text, textAlign: TextAlign.center, style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
        SizedBox(height: 18.h),
        _options(ex.options, res?.answer, language: controller.language),
      ]);

  Widget _meaning(SentenceExercise ex, SentenceCheck? res) => Column(children: [
        if (ex.sentence != null) SentenceCard(sentence: ex.sentence!, showTranslation: false),
        SizedBox(height: 18.h),
        _options(ex.options, res?.sentence.translation?.text, grid: false),
      ]);

  Widget _feedback(SentenceCheck res) => Container(
        width: double.infinity,
        padding: EdgeInsets.all(16.w),
        color: res.correct ? Colors.green.shade50 : Colors.red.shade50,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(children: [
              Icon(res.correct ? Icons.check_circle : Icons.cancel, color: res.correct ? Colors.green : Colors.red),
              SizedBox(width: 8.w),
              Text(res.correct ? 'Chính xác!${res.xp > 0 ? ' +${res.xp} XP' : ''}' : 'Chưa đúng – câu đúng là:',
                  style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700)),
            ]),
            SizedBox(height: 8.h),
            SentenceCard(sentence: res.sentence, fontSize: 18),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(onPressed: controller.next, child: const Text('Tiếp tục')),
            ),
          ],
        ),
      );
}
