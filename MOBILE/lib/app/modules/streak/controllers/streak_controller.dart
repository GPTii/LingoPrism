import 'package:get/get.dart';

import '../../../data/repositories/repositories.dart';
import '../../../data/services/game_service.dart';

class StreakController extends GetxController {
  final currentStreak = 0.obs;
  final studyDaysInMonth = 0.obs;
  final freezeItemsUsed = 0.obs;
  final currentMonth = DateTime.now().obs;
  final studiedDays = <DateTime>[].obs;
  final frozenDays = <DateTime>[].obs;
  final isLoading = false.obs;
  final todayHasActivity = false.obs;
  final errorMessage = ''.obs;

  @override
  void onInit() {
    super.onInit();
    refreshStreakData();
  }

  Future<void> refreshStreakData() async {
    await GameService.to.refreshSummary();
    final s = GameService.to.summary.value;
    currentStreak.value = s.streak;
    freezeItemsUsed.value = s.freezesUsed;
    todayHasActivity.value = s.studiedToday;
    await _loadMonth(currentMonth.value);
  }

  Future<void> previousMonth() => _loadMonth(DateTime(currentMonth.value.year, currentMonth.value.month - 1));

  Future<void> nextMonth() => _loadMonth(DateTime(currentMonth.value.year, currentMonth.value.month + 1));

  Future<void> _loadMonth(DateTime month) async {
    currentMonth.value = DateTime(month.year, month.month);
    isLoading.value = true;
    errorMessage.value = '';
    try {
      final start = DateTime(month.year, month.month, 1);
      final end = DateTime(month.year, month.month + 1, 0);
      final days = await GameRepository.progress(start: start, end: end);
      studiedDays.assignAll(days.where((d) => d.active || d.freezeUsed).map((d) => d.date));
      frozenDays.assignAll(days.where((d) => d.freezeUsed).map((d) => d.date));
      studyDaysInMonth.value = days.where((d) => d.active).length;
    } catch (e) {
      errorMessage.value = 'Không tải được dữ liệu streak';
    } finally {
      isLoading.value = false;
    }
  }

  bool _same(DateTime a, DateTime b) => a.year == b.year && a.month == b.month && a.day == b.day;

  bool isDayStudied(DateTime day) => studiedDays.any((d) => _same(d, day));

  bool isDayFrozen(DateTime day) => frozenDays.any((d) => _same(d, day));

  bool isToday(DateTime day) => _same(day, DateTime.now());

  bool isCurrentMonth(DateTime day) => day.month == currentMonth.value.month && day.year == currentMonth.value.year;

  String getMotivationalMessage() {
    final streak = currentStreak.value;

    if (streak == 0) {
      return 'Hãy bắt đầu streak của bạn hôm nay!';
    } else if (streak < 7) {
      return 'Tuyệt vời! Tiếp tục duy trì streak!';
    } else if (streak < 30) {
      return 'Streak ấn tượng! Bạn đang làm rất tốt!';
    } else if (streak < 100) {
      return 'Wow! Streak tháng rồi! Bạn thật kiên trì!';
    } else {
      return 'Huyền thoại! Streak 100+ ngày là điều tuyệt vời!';
    }
  }}
