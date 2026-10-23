import 'package:get/get.dart';

import '../../../data/models/api/game.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';

/// Today's goals and quests on the home tab (data from GameService).
class LearningTabController extends GetxController {
  static LearningTabController get to => Get.find<LearningTabController>();

  final RxBool isLoading = false.obs;
  final RxString error = ''.obs;
  final RxInt newLearned = 0.obs;
  final RxInt newTarget = 10.obs;
  final RxInt reviewDone = 0.obs;
  final RxInt reviewDue = 20.obs;
  final RxInt dueNow = 0.obs;
  final RxList<DailyQuest> dailyQuests = <DailyQuest>[].obs;
  final Rxn<MonthlyQuest> monthlyQuest = Rxn<MonthlyQuest>();

  int get monthlyTarget => monthlyQuest.value?.target ?? 20;

  final List<Worker> _workers = [];

  @override
  void onInit() {
    super.onInit();
    final game = GameService.to;
    _workers.addAll([
      ever<GameSummary>(game.summary, _applySummary),
      ever(game.library, (l) => dueNow.value = l.due),
      ever<List<DailyQuest>>(game.quests, dailyQuests.assignAll),
      ever<MonthlyQuest?>(game.monthly, (m) => monthlyQuest.value = m),
    ]);
    _applySummary(game.summary.value);
    dailyQuests.assignAll(game.quests);
    monthlyQuest.value = game.monthly.value;
    refreshProgress();
  }

  void _applySummary(GameSummary s) {
    newLearned.value = s.newLearned;
    newTarget.value = s.newTarget;
    reviewDone.value = s.reviewsDone;
    reviewDue.value = s.reviewTarget;
  }

  Future<void> refreshProgress() async {
    if (!AuthService.to.isLoggedIn) {
      error.value = 'Bạn cần đăng nhập để xem tiến độ';
      return;
    }
    isLoading.value = true;
    error.value = '';
    try {
      await GameService.to.refreshAll();
    } catch (e) {
      error.value = 'Không thể làm mới tiến độ: $e';
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> claim(DailyQuest quest) async {
    final (scales, gems) = await GameService.to.claimQuest(quest);
    Get.snackbar('Nhận thưởng', gems > 0
        ? '+$scales vảy và +$gems ngọc vì đã xong hết nhiệm vụ hôm nay!'
        : '+$scales vảy đã được cộng vào tài khoản của bạn.',
        snackPosition: SnackPosition.BOTTOM, duration: const Duration(seconds: 2));
  }

  Future<void> claimMonthly() async {
    final gained = await GameService.to.claimMonthly();
    Get.snackbar('Nhận thưởng', '+$gained ngọc đã được cộng vào tài khoản của bạn.', snackPosition: SnackPosition.BOTTOM);
  }

  @override
  void onClose() {
    for (final w in _workers) {
      w.dispose();
    }
    super.onClose();
  }
}
