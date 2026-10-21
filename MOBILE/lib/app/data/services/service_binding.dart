import 'package:get/get.dart';
import 'offline_learning.dart';
import 'package:get_storage/get_storage.dart';

import '../../core/network/api_client.dart';
import 'auth_service.dart';
import 'game_service.dart';
import 'location_service.dart';
import 'notification_scheduler_service.dart';
import 'realtime_service.dart';
import 'tts_service.dart';

/// Registers the app-wide services (idempotent – safe to call again after login/logout).
class ServiceBinding extends Bindings {
  @override
  void dependencies() {
    if (!Get.isRegistered<ApiClient>()) Get.put<ApiClient>(ApiClient(), permanent: true);
    if (!Get.isRegistered<AuthService>()) Get.put<AuthService>(AuthService(), permanent: true);
    if (!Get.isRegistered<GameService>()) Get.put<GameService>(GameService(), permanent: true);
    if (!Get.isRegistered<RealtimeService>()) Get.put<RealtimeService>(RealtimeService(), permanent: true);
    if (!Get.isRegistered<TtsService>()) Get.put<TtsService>(TtsService(), permanent: true);
    if (!Get.isRegistered<LocationService>()) Get.put<LocationService>(LocationService(), permanent: true);
  }
}

/// Things that must exist before `runApp` (local storage, services, local notifications).
class AppInitializer {
  static Future<void> initialize() async {
    await GetStorage.init();
    ServiceBinding().dependencies();
    if (!Get.isRegistered<NotificationSchedulerService>()) {
      final scheduler = NotificationSchedulerService();
      Get.put<NotificationSchedulerService>(scheduler, permanent: true);
      try {
        await scheduler.init();
      } catch (_) {
        // local notifications are optional (e.g. desktop)
      }
    }
  }

  /// Called after a successful login or on app start with a stored session.
  static Future<void> onSessionStarted() async {
    await AuthService.to.refreshUser();
    RealtimeService.to.start();
    GameService.to.refreshAll();
    LocationService.to.startGeofencing();
    OfflineLearning.start(); // send answers made offline, keep lessons ready for the next time
  }

  static Future<void> onSessionEnded() async {
    RealtimeService.to.stop();
    LocationService.to.stopGeofencing();
  }
}
