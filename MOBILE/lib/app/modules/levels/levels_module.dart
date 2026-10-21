import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/network/api_client.dart';
import '../../core/widgets/target_word.dart';
import '../../data/models/api/levels.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/tts_service.dart';
import '../../routes/app_pages.dart';
import '../learning_session/controllers/learning_session_controller.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';

/// Lộ trình 4 cấp độ (BE /levels/): progress per level, choosing the level, skip test.

const levelColors = [Color(0xFF22C55E), AppColors.primary, Color(0xFFF59E0B), AppColors.error];

// ====================================================================== path

class LevelPathController extends GetxController {
  final Rxn<LevelProgress> progress = Rxn<LevelProgress>();
  final RxString error = ''.obs;

  @override
  void onInit() {
    super.onInit();
    load();
  }

  Future<void> load() async {
    try {
      progress.value = await LevelRepository.progress();
      error.value = '';
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
    }
  }

  Future<void> choose(int level) async {
    try {
      progress.value = await LevelRepository.choose(level);
      Get.snackbar('Đã đổi cấp', 'Từ mới sẽ lấy từ cấp $level', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Chưa mở', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }
}

/// Compact card for the home screen: current level + progress, opens the full path.
class LevelPathCard extends StatelessWidget {
  const LevelPathCard({super.key});

  @override
  Widget build(BuildContext context) {
    final c = Get.put(LevelPathController(), permanent: true);
    return Obx(() {
      final p = c.progress.value;
      if (p == null) return const SizedBox.shrink();
      final row = p.levels.firstWhere((r) => r.current, orElse: () => p.levels.first);
      final color = levelColors[row.level - 1];
      return InkWell(
        onTap: () async {
          await Get.toNamed(Routes.levelPath);
          c.load();
        },
        borderRadius: BorderRadius.circular(16.r),
        child: Container(
          padding: EdgeInsets.all(14.w),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(color: color, width: 2),
          ),
          child: Row(children: [
            CircleAvatar(
              radius: 24.r,
              backgroundColor: color,
              child: Text('${row.level}', style: TextStyle(color: Colors.white, fontSize: 20.sp, fontWeight: FontWeight.w800)),
            ),
            SizedBox(width: 12.w),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Cấp ${row.level} · ${row.name}', style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800)),
                SizedBox(height: 6.h),
                LinearProgressIndicator(value: row.percent / 100, color: color, backgroundColor: color.withValues(alpha: 0.15)),
                SizedBox(height: 4.h),
                Text('${row.started}/${row.total} từ · mở cấp tiếp khi đạt ${p.unlockPercent}%',
                    style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
              ]),
            ),
            const Icon(Icons.chevron_right),
          ]),
        ),
      );
    });
  }
}

class LevelPathView extends GetView<LevelPathController> {
  const LevelPathView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Lộ trình 4 cấp độ')),
      body: Obx(() {
        final p = controller.progress.value;
        if (p == null) {
          return Center(child: controller.error.isEmpty ? const CircularProgressIndicator() : Text(controller.error.value));
        }
        return RefreshIndicator(
          onRefresh: controller.load,
          child: ListView(padding: EdgeInsets.all(16.w), children: [
            Text('Học xong ${p.unlockPercent}% số từ của một cấp thì mở cấp tiếp theo. '
                'Đã biết rồi? Làm bài kiểm tra ${p.testSize} câu, đúng từ ${p.testPass} câu là qua.',
                style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
            SizedBox(height: 12.h),
            for (final r in p.levels) _LevelTile(row: r, next: r.level < p.levels.length ? p.levels[r.level] : null, lang: p.language),
          ]),
        );
      }),
    );
  }
}

class _LevelTile extends GetView<LevelPathController> {
  const _LevelTile({required this.row, required this.next, required this.lang});

  final LevelRow row;
  final LevelRow? next;
  final String lang;

  static const _zhHint = ['≈ HSK 1', '≈ HSK 2', '≈ HSK 3', 'HSK 4 trở lên'];

  @override
  Widget build(BuildContext context) {
    final color = row.unlocked ? levelColors[row.level - 1] : AppColors.textHint;
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14.r),
        side: BorderSide(color: row.current ? color : Colors.transparent, width: 2),
      ),
      child: Padding(
        padding: EdgeInsets.all(14.w),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Text('Cấp ${row.level} · ${row.name}', style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w800, color: color)),
            if (lang == 'zh') Text('  ${_zhHint[row.level - 1]}', style: TextStyle(fontSize: 12.sp, color: AppColors.textHint)),
            const Spacer(),
            if (row.current)
              Chip(label: const Text('Đang học'), backgroundColor: color.withValues(alpha: 0.15))
            else if (!row.unlocked)
              const Icon(Icons.lock_outline, color: AppColors.textHint),
          ]),
          Text(row.description, style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
          SizedBox(height: 8.h),
          LinearProgressIndicator(value: row.percent / 100, color: color, backgroundColor: color.withValues(alpha: 0.15)),
          SizedBox(height: 4.h),
          Text('${row.started}/${row.total} từ đã học · ${row.mastered} đã thuộc', style: TextStyle(fontSize: 12.sp)),
          if (row.unlocked && (!row.current || (next != null && !next!.unlocked)))
            Wrap(spacing: 8.w, children: [
              if (!row.current) OutlinedButton(onPressed: () => controller.choose(row.level), child: const Text('Học cấp này')),
              if (next != null && !next!.unlocked)
                TextButton.icon(
                  onPressed: () async {
                    await Get.toNamed(Routes.levelTest, arguments: row.level);
                    controller.load();
                  },
                  icon: const Icon(Icons.bolt),
                  label: Text('Kiểm tra vượt cấp (còn ${row.needed} từ)'),
                ),
            ]),
        ]),
      ),
    );
  }
}

// ====================================================================== skip test

class LevelTestController extends GetxController {
  late final int level = Get.arguments as int;
  final Rxn<LevelTest> test = Rxn<LevelTest>();
  final RxList<String> answers = <String>[].obs;
  final Rxn<LevelTestResult> result = Rxn<LevelTestResult>();
  final RxString error = ''.obs;

  @override
  void onInit() {
    super.onInit();
    LevelRepository.test(level).then((t) {
      test.value = t;
      _speak();
    }).catchError((Object e) {
      error.value = ApiClient.toApiException(e).message;
    });
  }

  LevelTestQuestion? get question {
    final t = test.value;
    return t == null || answers.length >= t.questions.length ? null : t.questions[answers.length];
  }

  void _speak() {
    final a = question?.audio;
    if (a != null) TtsService.to.speak(a.text, a.ttsLocale);
  }

  Future<void> pick(String option) async {
    final t = test.value;
    if (t == null) return;
    answers.add(option);
    if (answers.length == t.questions.length) {
      try {
        result.value = await LevelRepository.submit(level, t.token, answers.toList());
      } catch (e) {
        error.value = ApiClient.toApiException(e).message;
      }
    } else {
      _speak();
    }
  }
}

class LevelTestView extends GetView<LevelTestController> {
  const LevelTestView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Kiểm tra vượt cấp ${controller.level}')),
      body: Obx(() {
        if (controller.error.isNotEmpty) return Center(child: Text(controller.error.value));
        final t = controller.test.value;
        if (t == null) return const Center(child: CircularProgressIndicator());
        final r = controller.result.value;
        if (r != null) return _result(r, t);
        final q = controller.question;
        if (q == null) return const Center(child: CircularProgressIndicator());
        return ListView(padding: EdgeInsets.all(20.w), children: [
          LinearProgressIndicator(value: controller.answers.length / t.questions.length),
          SizedBox(height: 8.h),
          Text('Đúng từ ${t.pass}/${t.questions.length} câu để mở cấp ${controller.level + 1}',
              style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
          SizedBox(height: 24.h),
          if (q.word != null) ...[
            Text('Từ này nghĩa là gì?', textAlign: TextAlign.center, style: TextStyle(fontSize: 15.sp)),
            SizedBox(height: 12.h),
            TargetWordView(target: q.word!, fontSize: 34),
          ],
          if (q.audio != null) ...[
            Text('Nghe rồi chọn từ đúng', textAlign: TextAlign.center, style: TextStyle(fontSize: 15.sp)),
            if (q.emoji.isNotEmpty) Text(q.emoji, textAlign: TextAlign.center, style: TextStyle(fontSize: 56.sp)),
            IconButton(
              iconSize: 40.sp,
              icon: const Icon(Icons.volume_up_rounded),
              onPressed: () => TtsService.to.speak(q.audio!.text, q.audio!.ttsLocale),
            ),
          ],
          SizedBox(height: 20.h),
          for (final o in q.options)
            Padding(
              padding: EdgeInsets.only(bottom: 10.h),
              child: OutlinedButton(
                style: OutlinedButton.styleFrom(padding: EdgeInsets.symmetric(vertical: 14.h)),
                onPressed: () => controller.pick(o),
                child: Text(o, style: TextStyle(fontSize: 16.sp)),
              ),
            ),
        ]);
      }),
    );
  }

  Widget _result(LevelTestResult r, LevelTest t) => Center(
        child: Padding(
          padding: EdgeInsets.all(24.w),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Image.asset(r.passed ? 'assets/brand/mascot/prismo_celebrate.png' : 'assets/brand/mascot/prismo_think.png', width: 120.w, height: 120.w),
            SizedBox(height: 8.h),
            Text(r.passed ? 'Bạn đã mở Cấp ${r.unlocked}!' : 'Chưa qua – đúng ${r.score}/${r.total} câu',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800)),
            SizedBox(height: 8.h),
            Text(r.passed ? 'Từ giờ từ mới sẽ lấy từ cấp ${r.unlocked}.' : 'Cần đúng ít nhất ${t.pass} câu. Học thêm rồi thử lại nhé.',
                textAlign: TextAlign.center),
            SizedBox(height: 20.h),
            FilledButton(
              onPressed: () {
                Get.back();
                if (r.passed) Get.toNamed(Routes.learningSession, arguments: const LearningSessionArguments(kind: 'learn'));
              },
              child: Text(r.passed ? 'Học từ mới' : 'Quay lại'),
            ),
          ]),
        ),
      );
}
