import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/utils/vietnamese.dart';
import '../../data/models/api/literacy.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/game_service.dart';
import '../../data/services/tts_service.dart';
import '../../routes/app_pages.dart';
import '../../core/widgets/word_picture.dart';

const _vi = 'vi-VN';
void _say(String text) => TtsService.to.speak(text, _vi);

/// Học đọc – viết tiếng Việt for Vietnamese children: lesson map + lessons (intro cards, then exercises).

// ====================================================================== map

class LiteracyMapController extends GetxController {
  final RxList<LitLessonInfo> lessons = <LitLessonInfo>[].obs;
  final RxBool isLoading = false.obs;
  final RxString error = ''.obs;

  @override
  void onInit() {
    super.onInit();
    load();
  }

  Future<void> load() async {
    isLoading.value = true;
    error.value = '';
    try {
      lessons.assignAll(await LiteracyRepository.lessons());
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> open(LitLessonInfo l) async {
    if (l.locked) {
      Get.snackbar('Bài ${l.n} chưa mở', 'Con hãy học xong bài trước nhé!', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    await Get.toNamed(Routes.literacyLesson, arguments: l.n);
    load();
  }
}

class LiteracyMapView extends GetView<LiteracyMapController> {
  const LiteracyMapView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(title: const Text('Học đọc – viết'), backgroundColor: AppColors.appBarBackground),
      body: Obx(() {
        if (controller.isLoading.value && controller.lessons.isEmpty) return const Center(child: CircularProgressIndicator());
        if (controller.error.isNotEmpty) return Center(child: Text(controller.error.value));
        final done = controller.lessons.where((l) => l.status == 'done').length;
        return RefreshIndicator(
          onRefresh: controller.load,
          child: CustomScrollView(slivers: [
            SliverToBoxAdapter(
              child: Container(
                margin: EdgeInsets.all(16.w),
                padding: EdgeInsets.all(16.w),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(colors: [Color(0xFFFFF1C1), Color(0xFFFFD6E8)]),
                  borderRadius: BorderRadius.circular(20.r),
                ),
                child: Row(children: [
                  Text('📖', style: TextStyle(fontSize: 44.sp)),
                  SizedBox(width: 12.w),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('Học âm, dấu, vần rồi tập đọc, tập viết', style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700)),
                      SizedBox(height: 8.h),
                      LinearProgressIndicator(
                          value: controller.lessons.isEmpty ? 0 : done / controller.lessons.length,
                          minHeight: 8.h, color: Colors.orange, backgroundColor: Colors.white),
                      SizedBox(height: 4.h),
                      Text('$done/${controller.lessons.length} bài', style: TextStyle(fontSize: 12.sp)),
                    ]),
                  ),
                ]),
              ),
            ),
            SliverPadding(
              padding: EdgeInsets.symmetric(horizontal: 16.w),
              sliver: SliverGrid.count(
                crossAxisCount: 3,
                mainAxisSpacing: 10.h,
                crossAxisSpacing: 10.w,
                childAspectRatio: 0.85,
                children: [for (final l in controller.lessons) _tile(l)],
              ),
            ),
            SliverToBoxAdapter(child: SizedBox(height: 24.h)),
          ]),
        );
      }),
    );
  }

  Widget _tile(LitLessonInfo l) {
    final color = l.locked ? Colors.grey.shade200 : (l.status == 'done' ? Colors.green.shade50 : Colors.white);
    final border = l.locked ? Colors.grey.shade300 : (l.status == 'done' ? Colors.green.shade300 : Colors.orange.shade300);
    final big = l.review ? '✍️' : l.units.take(3).map((u) => u.display).join(' ');
    return InkWell(
      onTap: () => controller.open(l),
      borderRadius: BorderRadius.circular(16.r),
      child: Container(
        padding: EdgeInsets.all(8.w),
        decoration: BoxDecoration(color: color, border: Border.all(color: border, width: 2), borderRadius: BorderRadius.circular(16.r)),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Text('Bài ${l.n}', style: TextStyle(fontSize: 11.sp, color: Colors.grey)),
          SizedBox(height: 4.h),
          l.locked
              ? Icon(Icons.lock_rounded, color: Colors.grey, size: 28.sp)
              : Text(big, textAlign: TextAlign.center, maxLines: 1, overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 22.sp, fontWeight: FontWeight.w800)),
          SizedBox(height: 4.h),
          Text(l.title, textAlign: TextAlign.center, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 11.sp)),
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            for (var s = 1; s <= 3; s++) Icon(Icons.star_rounded, size: 16.sp, color: s <= l.stars ? Colors.amber : Colors.grey.shade300),
          ]),
        ]),
      ),
    );
  }
}

// ====================================================================== lesson

class LiteracyLessonController extends GetxController {
  late final int n;
  final Rxn<LitLesson> lesson = Rxn<LitLesson>();
  final RxString error = ''.obs;
  final RxInt step = 0.obs;
  final RxnString picked = RxnString();
  final RxMap<String, String> build = <String, String>{}.obs;
  final Rxn<LitCheck> result = Rxn<LitCheck>();
  final Rxn<LitFinish> finish = Rxn<LitFinish>();
  final RxBool checking = false.obs;
  final TextEditingController input = TextEditingController();
  DateTime _started = DateTime.now();

  int get introCount => lesson.value?.intro.length ?? 0;
  int get total => introCount + (lesson.value?.exercises.length ?? 0);
  LitIntro? get intro => step.value < introCount ? lesson.value!.intro[step.value] : null;
  LitExercise? get exercise {
    final l = lesson.value;
    if (l == null || step.value < introCount || step.value - introCount >= l.exercises.length) return null;
    return l.exercises[step.value - introCount];
  }

  @override
  void onInit() {
    super.onInit();
    n = Get.arguments as int;
    load();
  }

  @override
  void onClose() {
    input.dispose();
    super.onClose();
  }

  Future<void> load() async {
    error.value = '';
    finish.value = null;
    step.value = 0;
    try {
      lesson.value = await LiteracyRepository.lesson(n);
      _show();
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
    }
  }

  void _show() {
    picked.value = null;
    build.clear();
    result.value = null;
    input.clear();
    _started = DateTime.now();
    final i = intro;
    if (i != null) _say(i.unit.spoken);
    final ex = exercise;
    if (ex != null && ex.type != 'find_unit') Future.delayed(const Duration(milliseconds: 300), () => _say(ex.ttsText));
  }

  Future<void> submit(Object answer) async {
    final ex = exercise;
    if (ex == null || result.value != null || checking.value) return;
    checking.value = true;
    try {
      final r = await LiteracyRepository.check(ex.token, answer, DateTime.now().difference(_started).inMilliseconds);
      result.value = r;
      _say(r.correct ? 'Đúng rồi!' : (r.word.isNotEmpty ? r.word : r.expected));
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      checking.value = false;
    }
  }

  void pick(String option) {
    picked.value = option;
    _say(option);
    submit(option);
  }

  void typeTone(String tone) {
    final sel = input.selection;
    final cursor = sel.isValid ? sel.baseOffset : input.text.length;
    final (text, pos) = toneAtCursor(input.text, cursor, tone);
    input.value = TextEditingValue(text: text, selection: TextSelection.collapsed(offset: pos));
  }

  void typeLetter(String letter) {
    final sel = input.selection;
    final cursor = sel.isValid ? sel.baseOffset : input.text.length;
    final text = input.text.substring(0, cursor) + letter + input.text.substring(cursor);
    input.value = TextEditingValue(text: text, selection: TextSelection.collapsed(offset: cursor + letter.length));
  }

  Future<void> next() async {
    final l = lesson.value;
    if (l == null) return;
    if (step.value + 1 < total) {
      step.value++;
      _show();
      return;
    }
    try {
      finish.value = await LiteracyRepository.finish(n, l.session, l.exercises.length);
      if (Get.isRegistered<GameService>()) GameService.to.refreshSummary();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }
}

class LiteracyLessonView extends GetView<LiteracyLessonController> {
  const LiteracyLessonView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: AppColors.appBarBackground,
        title: Obx(() => Text(controller.lesson.value == null ? 'Bài ${controller.n}' : 'Bài ${controller.n}: ${controller.lesson.value!.title}',
            style: TextStyle(fontSize: 15.sp))),
      ),
      body: SafeArea(
        child: Obx(() {
          if (controller.error.isNotEmpty) {
            return Center(child: Padding(padding: EdgeInsets.all(24.w), child: Text(controller.error.value, textAlign: TextAlign.center)));
          }
          if (controller.lesson.value == null) return const Center(child: CircularProgressIndicator());
          if (controller.finish.value != null) return _finish(controller.finish.value!);
          return Column(children: [
            LinearProgressIndicator(value: controller.step.value / controller.total, minHeight: 6.h, color: Colors.orange),
            Expanded(
              child: SingleChildScrollView(
                padding: EdgeInsets.all(16.w),
                child: Container(
                  width: double.infinity,
                  padding: EdgeInsets.all(18.w),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20.r)),
                  child: controller.intro != null ? _intro(controller.intro!) : _exercise(controller.exercise!),
                ),
              ),
            ),
            if (controller.intro != null)
              Padding(
                padding: EdgeInsets.all(16.w),
                child: SizedBox(width: double.infinity, child: ElevatedButton(onPressed: controller.next, child: const Text('Tiếp tục'))),
              ),
            if (controller.result.value != null) _feedback(controller.result.value!),
          ]);
        }),
      ),
    );
  }

  // ---------------------------------------------------------------- pieces

  Widget _speaker(String text, {double size = 40}) => IconButton.filled(
        iconSize: size.sp,
        onPressed: () => _say(text),
        icon: const Icon(Icons.volume_up_rounded),
      );

  Widget _spell(List<String> steps) => Wrap(
        alignment: WrapAlignment.center,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 2.w,
        children: [
          for (var i = 0; i < steps.length; i++) ...[
            if (i > 0) Text('–', style: TextStyle(color: Colors.grey.shade400)),
            InkWell(
              onTap: () => _say(steps[i]),
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 2.h),
                child: Text(steps[i],
                    style: TextStyle(fontSize: 18.sp, fontWeight: i == steps.length - 1 ? FontWeight.w800 : FontWeight.w400,
                        color: i == steps.length - 1 ? AppColors.buttonActive : AppColors.textSecondary)),
              ),
            ),
          ],
        ],
      );

  Widget _intro(LitIntro intro) {
    final u = intro.unit;
    return Column(children: [
      Text(u.kind == 'am' ? 'Âm mới' : u.kind == 'van' ? 'Vần mới' : 'Dấu thanh mới', style: TextStyle(color: Colors.grey, fontSize: 14.sp)),
      InkWell(onTap: () => _say(u.spoken),
          child: Text(u.display, style: TextStyle(fontSize: 80.sp, fontWeight: FontWeight.w800, color: AppColors.buttonActive))),
      Text(u.kind == 'thanh' ? u.label : 'đọc là “${u.spoken}”', style: TextStyle(fontSize: 18.sp)),
      if (intro.rhymeSpell.length > 1) ...[SizedBox(height: 8.h), _spell(intro.rhymeSpell)],
      SizedBox(height: 16.h),
      for (final e in intro.examples)
        Container(
          width: double.infinity,
          margin: EdgeInsets.only(bottom: 8.h),
          padding: EdgeInsets.symmetric(vertical: 6.h),
          decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(14.r)),
          child: _spell(e.spell),
        ),
      if (intro.words.isNotEmpty) ...[
        SizedBox(height: 8.h),
        Wrap(spacing: 10.w, runSpacing: 10.h, alignment: WrapAlignment.center, children: [
          for (final w in intro.words)
            InkWell(
              onTap: () => _say(w.text),
              borderRadius: BorderRadius.circular(14.r),
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 8.h),
                decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade300, width: 2), borderRadius: BorderRadius.circular(14.r)),
                child: Column(children: [WordPicture(imageUrl: w.image, emoji: w.emoji, size: 72.w), SizedBox(height: 4.h), Text(w.text, style: TextStyle(fontSize: 16.sp))]),
              ),
            ),
        ]),
      ],
    ]);
  }

  Widget _options(LitExercise ex, {bool big = true}) {
    final res = controller.result.value;
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 10.h,
      crossAxisSpacing: 10.w,
      childAspectRatio: big ? 1.8 : 2.6,
      children: [
        for (final o in ex.options)
          InkWell(
            onTap: res == null ? () => controller.pick(o) : null,
            borderRadius: BorderRadius.circular(16.r),
            child: Container(
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: res == null ? Colors.white : o == res.expected ? Colors.green.shade50
                    : o == controller.picked.value ? Colors.red.shade50 : Colors.white,
                border: Border.all(
                    color: res == null ? (o == controller.picked.value ? AppColors.buttonActive : Colors.grey.shade300)
                        : o == res.expected ? Colors.green : o == controller.picked.value ? Colors.red : Colors.grey.shade300,
                    width: 2),
                borderRadius: BorderRadius.circular(16.r),
              ),
              child: Text(o, textAlign: TextAlign.center, style: TextStyle(fontSize: big ? 30.sp : 18.sp, fontWeight: FontWeight.w700)),
            ),
          ),
      ],
    );
  }

  Widget _title(String text) => Padding(
        padding: EdgeInsets.only(bottom: 12.h),
        child: Text(text, textAlign: TextAlign.center, style: TextStyle(fontSize: 16.sp, color: AppColors.textSecondary, fontWeight: FontWeight.w600)),
      );

  Widget _exercise(LitExercise ex) {
    switch (ex.type) {
      case 'listen_choose':
        return Column(children: [_title('Nghe rồi chọn tiếng đúng'), _speaker(ex.ttsText), SizedBox(height: 16.h), _options(ex)]);
      case 'find_unit':
        return Column(children: [
          _title(ex.question),
          InkWell(onTap: () => _say(ex.syllable), child: Text(ex.syllable, style: TextStyle(fontSize: 56.sp, fontWeight: FontWeight.w800))),
          SizedBox(height: 16.h),
          _options(ex, big: false),
        ]);
      case 'rule':
        return Column(children: [
          _title(ex.question),
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            Text(ex.pattern, style: TextStyle(fontSize: 52.sp, fontWeight: FontWeight.w800, letterSpacing: 2)),
            SizedBox(width: 8.w),
            _speaker(ex.ttsText, size: 28),
          ]),
          SizedBox(height: 16.h),
          _options(ex),
        ]);
      case 'build':
        return _build(ex);
      default:
        return _dictation(ex);
    }
  }

  Widget _build(LitExercise ex) {
    Widget row(String key, String label, List<(String, String)> opts) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: TextStyle(fontSize: 13.sp, color: Colors.grey)),
          SizedBox(height: 4.h),
          Wrap(spacing: 8.w, runSpacing: 8.h, children: [
            for (final (value, text) in opts)
              ChoiceChip(
                label: Text(text, style: TextStyle(fontSize: 18.sp)),
                selected: controller.build[key] == value,
                onSelected: controller.result.value == null ? (_) => controller.build[key] = value : null,
              ),
          ]),
          SizedBox(height: 12.h),
        ]);
    final ready = ['onset', 'rhyme', 'tone'].every(controller.build.containsKey);
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      _title('Nghe rồi ghép tiếng: âm đầu + vần + dấu'),
      Center(child: _speaker(ex.ttsText)),
      SizedBox(height: 12.h),
      row('onset', 'Âm đầu', [for (final o in ex.onsets) (o, o == '∅' ? '(không có)' : o)]),
      row('rhyme', 'Vần', [for (final r in ex.rhymes) (r, r)]),
      row('tone', 'Dấu', [for (final t in ex.tones) (t.code, t.symbol.isEmpty ? t.label : '${t.symbol}  ${t.label}')]),
      if (controller.result.value == null)
        ElevatedButton(
          onPressed: ready && !controller.checking.value ? () => controller.submit(Map<String, String>.from(controller.build)) : null,
          child: const Text('Kiểm tra'),
        ),
    ]);
  }

  Widget _dictation(LitExercise ex) {
    final done = controller.result.value != null;
    return Column(children: [
      _title('${ex.type == 'sentence' ? 'Nghe rồi viết lại câu' : 'Nghe rồi viết lại'} (${ex.syllables} tiếng)'),
      if (ex.type == 'dictation') WordPicture(imageUrl: ex.image, emoji: ex.emoji, size: 160.w),
      _speaker(ex.ttsText),
      SizedBox(height: 12.h),
      TextField(
        controller: controller.input,
        enabled: !done,
        autofocus: true,
        textAlign: TextAlign.center,
        autocorrect: false,
        enableSuggestions: false,
        style: TextStyle(fontSize: 24.sp),
        decoration: InputDecoration(border: OutlineInputBorder(borderRadius: BorderRadius.circular(14.r))),
        onSubmitted: (v) => v.trim().isEmpty ? null : controller.submit(v),
      ),
      if (!done) ...[
        SizedBox(height: 10.h),
        Wrap(spacing: 6.w, runSpacing: 6.h, alignment: WrapAlignment.center, children: [
          for (final l in specialLetters) OutlinedButton(onPressed: () => controller.typeLetter(l), child: Text(l, style: TextStyle(fontSize: 18.sp))),
          for (final (tone, label) in const [('huyen', '`'), ('sac', '´'), ('hoi', '?'), ('nga', '~'), ('nang', '.'), ('ngang', 'bỏ dấu')])
            OutlinedButton(
              style: OutlinedButton.styleFrom(foregroundColor: Colors.orange.shade800),
              onPressed: () => controller.typeTone(tone),
              child: Text(label, style: TextStyle(fontSize: 18.sp)),
            ),
        ]),
        SizedBox(height: 12.h),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: controller.checking.value ? null : () => controller.input.text.trim().isEmpty ? null : controller.submit(controller.input.text),
            child: const Text('Kiểm tra'),
          ),
        ),
      ],
      if (ex.sourceUrl.isNotEmpty)
        TextButton(
          onPressed: () => launchUrl(Uri.parse(ex.sourceUrl), mode: LaunchMode.externalApplication),
          child: Text(ex.sourceLabel, style: TextStyle(fontSize: 11.sp, color: Colors.grey)),
        ),
    ]);
  }

  Widget _feedback(LitCheck r) => Container(
        width: double.infinity,
        padding: EdgeInsets.all(16.w),
        color: r.correct ? Colors.green.shade50 : Colors.red.shade50,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(r.correct ? Icons.check_circle : Icons.cancel, color: r.correct ? Colors.green : Colors.red),
            SizedBox(width: 8.w),
            Text(r.correct ? 'Đúng rồi!${r.xp > 0 ? ' +${r.xp} XP' : ''}' : 'Chưa đúng rồi, xem lại nhé:',
                style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w700)),
          ]),
          if (r.diff.isNotEmpty) ...[
            SizedBox(height: 8.h),
            Wrap(spacing: 8.w, runSpacing: 4.h, children: [
              for (final d in r.diff)
                Text(
                  d.ok ? d.expected : (d.expected.isEmpty ? '(thừa: ${d.given})' : '${d.expected} (con viết: ${d.given.isEmpty ? '…' : d.given}${d.hint.isNotEmpty ? ' – ${d.hint}' : ''})'),
                  style: TextStyle(fontSize: 18.sp, color: d.ok ? Colors.green.shade800 : Colors.red.shade700, fontWeight: FontWeight.w600),
                ),
            ]),
          ],
          if (r.spell.isNotEmpty) ...[SizedBox(height: 8.h), Center(child: _spell(r.spell))],
          SizedBox(height: 10.h),
          SizedBox(width: double.infinity, child: ElevatedButton(onPressed: controller.next, child: const Text('Tiếp tục'))),
        ]),
      );

  Widget _finish(LitFinish f) => Center(
        child: Padding(
          padding: EdgeInsets.all(24.w),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(f.passed ? '🎉' : '💪', style: TextStyle(fontSize: 64.sp)),
            SizedBox(height: 8.h),
            Text(f.passed ? 'Giỏi lắm! Con đã xong bài học.' : 'Cố lên! Mình học lại bài này nhé.',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800)),
            SizedBox(height: 8.h),
            Row(mainAxisSize: MainAxisSize.min, children: [
              for (var s = 1; s <= 3; s++) Icon(Icons.star_rounded, size: 40.sp, color: s <= f.stars ? Colors.amber : Colors.grey.shade300),
            ]),
            Text('Đúng ngay lần đầu ${f.correct}/${f.total} câu', style: TextStyle(fontSize: 15.sp, color: AppColors.textSecondary)),
            SizedBox(height: 20.h),
            Row(mainAxisSize: MainAxisSize.min, children: [
              OutlinedButton(onPressed: Get.back, child: const Text('Về lộ trình')),
              SizedBox(width: 12.w),
              f.nextUnlocked
                  ? ElevatedButton(
                      onPressed: () => Get.offNamed(Routes.literacyLesson, arguments: controller.n + 1, preventDuplicates: false),
                      child: const Text('Bài tiếp theo'))
                  : ElevatedButton(onPressed: controller.load, child: const Text('Học lại')),
            ]),
          ]),
        ),
      );
}
