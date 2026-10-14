import 'package:get/get.dart';

import '../models/api/game.dart';
import '../models/api/vocab.dart';
import '../repositories/repositories.dart';
import 'auth_service.dart';

/// App-wide gamification + learning progress state: XP, streak, wallet, today's goals,
/// quests and library summary. Refreshed after sessions and on realtime "xp" events.
class GameService extends GetxService {
  static GameService get to => Get.find<GameService>();

  final Rx<GameSummary> summary = GameSummary().obs;
  final Rx<LibrarySummary> library = LibrarySummary().obs;
  final RxList<DailyQuest> quests = <DailyQuest>[].obs;
  final Rxn<MonthlyQuest> monthly = Rxn<MonthlyQuest>();
  final RxBool loading = false.obs;

  int get streak => summary.value.streak;
  int get scales => summary.value.scales;
  int get gems => summary.value.gems;

  Future<void> refreshAll() async {
    if (!AuthService.to.isLoggedIn) return;
    loading.value = true;
    try {
      await Future.wait([refreshSummary(), refreshLibrary(), refreshQuests()]);
    } finally {
      loading.value = false;
    }
  }

  Future<void> refreshSummary() async {
    try {
      summary.value = await GameRepository.summary();
    } catch (_) {}
  }

  Future<void> refreshLibrary() async {
    try {
      library.value = await VocabRepository.summary();
    } catch (_) {}
  }

  Future<void> refreshQuests() async {
    try {
      final (q, m) = await GameRepository.quests();
      quests.assignAll(q);
      monthly.value = m;
    } catch (_) {}
  }

  Future<int> claimQuest(DailyQuest quest) async {
    final gained = await GameRepository.claimQuest(quest.id);
    await Future.wait([refreshQuests(), refreshSummary()]);
    return gained;
  }

  Future<int> claimMonthly() async {
    final gained = await GameRepository.claimMonthly();
    await Future.wait([refreshQuests(), refreshSummary()]);
    return gained;
  }

  /// Applied when the server pushes an "xp" event over WebSocket.
  void applyRealtimeXp(Map<String, dynamic> payload) => refreshSummary();
}
