import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/target_word.dart';
import '../../data/models/api/learning_extra.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/auth_service.dart';
import '../../data/services/game_service.dart';
import '../../routes/app_pages.dart';

// ====================================================================== list

class ExamListController extends GetxController {
  final RxList<ExamInfo> exams = <ExamInfo>[].obs;
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
      exams.assignAll(await ExamRepository.exams(language: AuthService.to.currentUser?.targetCode));
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
    } finally {
      isLoading.value = false;
    }
  }
}

class ExamListView extends GetView<ExamListController> {
  const ExamListView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(title: const Text('Bài kiểm tra'), backgroundColor: AppColors.appBarBackground),
      body: Obx(() {
        if (controller.isLoading.value) return const Center(child: CircularProgressIndicator());
        if (controller.error.isNotEmpty) return Center(child: Text(controller.error.value));
        if (controller.exams.isEmpty) {
          return Center(child: Text('Chưa có bài kiểm tra cho ngôn ngữ ${AuthService.to.currentUser?.languageLabel ?? ''}.'));
        }
        return RefreshIndicator(
          onRefresh: controller.load,
          child: ListView.separated(
            padding: EdgeInsets.all(16.w),
            itemCount: controller.exams.length,
            separatorBuilder: (_, __) => SizedBox(height: 12.h),
            itemBuilder: (_, i) {
              final e = controller.exams[i];
              return Material(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16.r),
                child: ListTile(
                  contentPadding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
                  title: Text(e.title, style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16.sp)),
                  subtitle: Text('${e.questionCount} câu · ${e.timeLimitMinutes ?? '–'} phút'
                      '${e.bestPercent != null ? ' · Tốt nhất: ${e.bestPercent!.toStringAsFixed(0)}%' : ''}'
                      '${e.bestStatus == 'submitted' ? ' (chờ chấm tự luận)' : ''}'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () async {
                    await Get.toNamed(Routes.examTake, arguments: e);
                    controller.load();
                  },
                ),
              );
            },
          ),
        );
      }),
    );
  }
}

// ====================================================================== take

class ExamTakeController extends GetxController {
  late final ExamInfo exam;
  final Rxn<ExamAttempt> attempt = Rxn<ExamAttempt>();
  final RxMap<int, int> selected = <int, int>{}.obs;
  final Map<int, TextEditingController> texts = {};
  final RxInt remainingSeconds = 0.obs;
  final RxBool submitting = false.obs;
  Timer? _timer;

  @override
  void onInit() {
    super.onInit();
    exam = Get.arguments as ExamInfo;
    _start();
  }

  Future<void> _start() async {
    try {
      final a = await ExamRepository.start(exam.id);
      for (final q in a.questions) {
        if (q.kind != 'mcq') texts[q.id] = TextEditingController();
      }
      attempt.value = a;
      if (a.timeLimitMinutes != null) {
        final end = a.startedAt.add(Duration(minutes: a.timeLimitMinutes!));
        remainingSeconds.value = end.difference(DateTime.now()).inSeconds.clamp(0, 1 << 30);
        _timer = Timer.periodic(const Duration(seconds: 1), (_) {
          if (remainingSeconds.value <= 0) {
            _timer?.cancel();
            submit(auto: true);
          } else {
            remainingSeconds.value--;
          }
        });
      }
    } catch (e) {
      Get.back();
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> submit({bool auto = false}) async {
    final a = attempt.value;
    if (a == null || submitting.value) return;
    if (!auto) {
      final unanswered = a.questions.where((q) => q.kind == 'mcq' ? !selected.containsKey(q.id) : texts[q.id]!.text.trim().isEmpty).length;
      if (unanswered > 0) {
        final ok = await Get.dialog<bool>(AlertDialog(
          title: const Text('Nộp bài?'),
          content: Text('Còn $unanswered câu chưa trả lời.'),
          actions: [
            TextButton(onPressed: () => Get.back(result: false), child: const Text('Làm tiếp')),
            TextButton(onPressed: () => Get.back(result: true), child: const Text('Nộp bài')),
          ],
        ));
        if (ok != true) return;
      }
    }
    submitting.value = true;
    _timer?.cancel();
    try {
      final result = await ExamRepository.submit(a.submissionId, [
        for (final q in a.questions)
          q.kind == 'mcq' ? {'question': q.id, 'selected_option': selected[q.id]} : {'question': q.id, 'text': texts[q.id]!.text},
      ]);
      GameService.to.refreshSummary();
      Get.offNamed(Routes.examResult, arguments: result.id);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      submitting.value = false;
    }
  }

  @override
  void onClose() {
    _timer?.cancel();
    for (final c in texts.values) {
      c.dispose();
    }
    super.onClose();
  }
}

class ExamTakeView extends GetView<ExamTakeController> {
  const ExamTakeView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        title: Text(controller.exam.title),
        backgroundColor: AppColors.appBarBackground,
        actions: [
          Obx(() {
            final s = controller.remainingSeconds.value;
            if (controller.attempt.value?.timeLimitMinutes == null) return const SizedBox();
            return Center(
              child: Padding(
                padding: EdgeInsets.only(right: 16.w),
                child: Text('${(s ~/ 60).toString().padLeft(2, '0')}:${(s % 60).toString().padLeft(2, '0')}',
                    style: TextStyle(fontWeight: FontWeight.w700, color: s < 60 ? Colors.red : AppColors.textPrimary)),
              ),
            );
          }),
        ],
      ),
      body: Obx(() {
        final a = controller.attempt.value;
        if (a == null) return const Center(child: CircularProgressIndicator());
        return ListView(
          padding: EdgeInsets.all(16.w),
          children: [
            for (var i = 0; i < a.questions.length; i++) _question(i + 1, a.questions[i], a.language),
            SizedBox(height: 12.h),
            Obx(() => ElevatedButton(
                  onPressed: controller.submitting.value ? null : () => controller.submit(),
                  style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.buttonActive, foregroundColor: Colors.white, padding: EdgeInsets.symmetric(vertical: 14.h)),
                  child: Text(controller.submitting.value ? 'Đang nộp…' : 'Nộp bài'),
                )),
          ],
        );
      }),
    );
  }

  Widget _question(int n, ExamQuestion q, String language) {
    return Container(
      margin: EdgeInsets.only(bottom: 12.h),
      padding: EdgeInsets.all(14.w),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14.r)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Câu $n (${q.points.toStringAsFixed(q.points % 1 == 0 ? 0 : 1)} điểm)',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 12.sp)),
        SizedBox(height: 4.h),
        LangText(q.prompt, language: language, style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w600)),
        SizedBox(height: 8.h),
        if (q.kind == 'mcq')
          for (var i = 0; i < q.options.length; i++)
            Obx(() => RadioListTile<int>(
                  dense: true,
                  value: i,
                  groupValue: controller.selected[q.id],
                  onChanged: (v) => controller.selected[q.id] = v!,
                  title: LangText(q.options[i], language: language, style: TextStyle(fontSize: 16.sp)),
                ))
        else
          TextField(
            controller: controller.texts[q.id],
            maxLines: q.kind == 'essay' ? 5 : 1,
            decoration: InputDecoration(
              hintText: q.kind == 'essay' ? 'Viết câu trả lời…' : 'Nhập đáp án',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(10.r)),
            ),
          ),
      ]),
    );
  }
}

// ====================================================================== result

class ExamResultController extends GetxController {
  final Rxn<SubmissionResult> result = Rxn<SubmissionResult>();

  @override
  void onInit() {
    super.onInit();
    ExamRepository.result(Get.arguments as int).then((r) => result.value = r).catchError((e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message);
      return SubmissionResult(id: 0, examTitle: '', status: '');
    });
  }
}

class ExamResultView extends GetView<ExamResultController> {
  const ExamResultView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(title: const Text('Kết quả'), backgroundColor: AppColors.appBarBackground),
      body: Obx(() {
        final r = controller.result.value;
        if (r == null) return const Center(child: CircularProgressIndicator());
        return ListView(padding: EdgeInsets.all(16.w), children: [
          Container(
            padding: EdgeInsets.all(20.w),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16.r)),
            child: Column(children: [
              Text(r.examTitle, style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w700), textAlign: TextAlign.center),
              SizedBox(height: 8.h),
              Text('${r.score.toStringAsFixed(1)} / ${r.maxScore.toStringAsFixed(1)} điểm',
                  style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w800, color: AppColors.buttonActive)),
              Text(r.waitingForTeacher
                  ? 'Đang chờ giáo viên chấm phần tự luận'
                  : (r.passed ? 'Đạt 🎉' : 'Chưa đạt – cố gắng lần sau nhé!')),
              if (r.feedback.isNotEmpty) Padding(padding: EdgeInsets.only(top: 8.h), child: Text('Nhận xét: ${r.feedback}')),
            ]),
          ),
          SizedBox(height: 16.h),
          for (var i = 0; i < r.answers.length; i++) _answer(i + 1, r.answers[i]),
        ]);
      }),
    );
  }

  Widget _answer(int n, AnswerResult a) {
    final color = a.isCorrect == null ? Colors.orange : (a.isCorrect! ? AppColors.buttonSuccess : Colors.red);
    final yours = a.questionKind == 'mcq'
        ? (a.selectedOption != null && a.selectedOption! < a.options.length ? a.options[a.selectedOption!] : '(bỏ trống)')
        : (a.text.isEmpty ? '(bỏ trống)' : a.text);
    final correct = a.questionKind == 'mcq'
        ? (a.correctOption != null ? a.options[a.correctOption!] : '')
        : a.acceptedAnswers.join(' / ');
    return Container(
      margin: EdgeInsets.only(bottom: 10.h),
      padding: EdgeInsets.all(14.w),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14.r), border: Border(left: BorderSide(color: color, width: 4))),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Câu $n: ${a.prompt}', style: const TextStyle(fontWeight: FontWeight.w600)),
        SizedBox(height: 6.h),
        Text('Bạn trả lời: $yours'),
        if (a.questionKind != 'essay' && a.isCorrect == false) Text('Đáp án: $correct', style: TextStyle(color: AppColors.buttonSuccess)),
        if (a.explanation.isNotEmpty) Text(a.explanation, style: TextStyle(color: AppColors.textSecondary)),
        if (a.score != null) Text('Điểm: ${a.score!.toStringAsFixed(1)} / ${a.points.toStringAsFixed(1)}'),
        if (a.isCorrect == null) const Text('Chờ giáo viên chấm', style: TextStyle(color: Colors.orange)),
        if (a.feedback.isNotEmpty) Text('Nhận xét: ${a.feedback}', style: const TextStyle(fontStyle: FontStyle.italic)),
      ]),
    );
  }
}
