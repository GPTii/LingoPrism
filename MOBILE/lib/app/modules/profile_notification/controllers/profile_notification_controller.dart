import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../data/repositories/repositories.dart';
import '../../../data/services/notification_scheduler_service.dart';

/// Reminder settings: stored on the server (`/notification-settings/`) and scheduled locally.
class ProfileNotificationController extends GetxController {
  final RxBool notificationsEnabled = true.obs;
  final Rx<TimeOfDay> reminderTime = const TimeOfDay(hour: 20, minute: 0).obs;
  final RxString frequency = '1 lần/ngày'.obs;
  final RxBool contextualAllowed = true.obs;
  final List<String> frequencies = const ['1 lần/ngày', '2 lần/ngày', '3 lần/ngày'];

  NotificationSchedulerService get _scheduler => NotificationSchedulerService.to;

  @override
  void onInit() {
    super.onInit();
    _load();
  }

  Future<void> _load() async {
    try {
      final s = await NotificationRepository.settings();
      notificationsEnabled.value = s['push_enabled'] != false;
      contextualAllowed.value = s['contextual_allowed'] != false;
      final evening = s['evening_time'] as String?;
      if (evening != null && evening.contains(':')) {
        final p = evening.split(':');
        reminderTime.value = TimeOfDay(hour: int.parse(p[0]), minute: int.parse(p[1]));
      }
      if (s['morning_time'] != null) frequency.value = '2 lần/ngày';
    } catch (_) {}
  }

  String _fmt(TimeOfDay t) => '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  Future<void> _sync() async {
    final times = frequencies.indexOf(frequency.value) + 1;
    try {
      await NotificationRepository.updateSettings({
        'push_enabled': notificationsEnabled.value,
        'evening_time': _fmt(reminderTime.value),
        'morning_time': times >= 2 ? '08:00' : null,
        'contextual_allowed': contextualAllowed.value,
      });
    } catch (_) {}
    final start = reminderTime.value;
    await _scheduler.updateSchedule(
      enabled: notificationsEnabled.value,
      startTime: times >= 2 ? const TimeOfDay(hour: 8, minute: 0) : start,
      endTime: start,
      dailyFrequency: times,
      weeklyFrequency: 7,
    );
  }

  Future<void> toggleNotifications(bool value) async {
    notificationsEnabled.value = value;
    await _sync();
  }

  Future<void> toggleContextual(bool value) async {
    contextualAllowed.value = value;
    await _sync();
  }

  Future<void> updateTime(TimeOfDay time) async {
    reminderTime.value = time;
    await _sync();
  }

  Future<void> updateFrequency(String value) async {
    frequency.value = value;
    await _sync();
  }

  Future<void> sendTestNotification() => _scheduler.showTestNotification();

  Future<void> sendScheduledTestNotification() => _scheduler.scheduleTestNotification();
}
