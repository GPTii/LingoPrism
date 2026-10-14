import 'package:get/get.dart';

import '../../../data/models/api/user.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';
import '../../../data/services/realtime_service.dart';

/// Header data of the home screen: profile, wallet, streak, unread notifications.
class HomeStatsController extends GetxController {
  final Rxn<AppUser> user = Rxn<AppUser>();
  final RxBool isLoading = false.obs;
  final RxInt unreadNotifications = 0.obs;
  final RxInt streak = 0.obs;
  final RxInt scales = 0.obs;
  final RxInt gems = 0.obs;

  final List<Worker> _workers = [];

  @override
  void onInit() {
    super.onInit();
    final game = GameService.to;
    user.value = AuthService.to.currentUser;
    _workers.addAll([
      ever<AppUser?>(AuthService.to.user, (u) => user.value = u),
      ever(game.summary, (s) {
        streak.value = s.streak;
        scales.value = s.scales;
        gems.value = s.gems;
      }),
      ever<int>(RealtimeService.to.unreadNotifications, (n) => unreadNotifications.value = n),
    ]);
    streak.value = game.summary.value.streak;
    scales.value = game.summary.value.scales;
    gems.value = game.summary.value.gems;
    unreadNotifications.value = RealtimeService.to.unreadNotifications.value;
    load();
  }

  Future<void> load() async {
    isLoading.value = game.summary.value.lifetimeXp == 0 && game.summary.value.scales == 0;
    try {
      await Future.wait([GameService.to.refreshSummary(), RealtimeService.to.refreshUnread()]);
    } finally {
      isLoading.value = false;
    }
  }

  GameService get game => GameService.to;

  @override
  void onClose() {
    for (final w in _workers) {
      w.dispose();
    }
    super.onClose();
  }
}
