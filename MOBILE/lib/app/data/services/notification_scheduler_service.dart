import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:get/get.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;

class NotificationSchedulerService extends GetxService {
  NotificationSchedulerService({
    FlutterLocalNotificationsPlugin? notificationsPlugin,
  }) : _notificationsPlugin =
            notificationsPlugin ?? FlutterLocalNotificationsPlugin();

  static NotificationSchedulerService get to => Get.find();

  static const String _channelId = 'snaplingua_daily_reminders';
  static const String _channelName = 'Nhắc nhở học tập';
  static const String _channelDescription = 'Thông báo nhắc học từ SnapLingua';

  final FlutterLocalNotificationsPlugin _notificationsPlugin;

  bool _initialized = false;
  bool _canScheduleExact = false;

  Future<NotificationSchedulerService> init() async {
    if (_initialized) return this;
    await _initializeTimeZones();
    await _initializePlugin();
    _initialized = true;
    return this;
  }

  Future<void> _initializeTimeZones() async {
    tz.initializeTimeZones();
    tz.setLocalLocation(tz.local);
  }

  Future<void> _initializePlugin() async {
    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    const initializationSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _notificationsPlugin.initialize(initializationSettings);

    // Request permissions sequentially to avoid conflicts
    final androidImplementation = _notificationsPlugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>();

    if (androidImplementation != null) {
      try {
        // Request notification permission first
        await androidImplementation.requestNotificationsPermission();

        // Wait a bit and then request exact alarms permission
        await Future.delayed(const Duration(milliseconds: 100));
        _canScheduleExact =
            await androidImplementation.requestExactAlarmsPermission() ?? false;
        // Một số phiên bản plugin/platform không hỗ trợ kiểm tra trạng thái;
        // nếu request trả về false, ta vẫn giữ nguyên (_canScheduleExact) để
        // dùng lịch inexact.
      } catch (e) {
        // Log error but don't throw to avoid breaking the service
        debugPrint('Permission request error: $e');
      }
    }
  }

  /// Gửi thông báo thử ngay lập tức để kiểm tra quyền/thông báo.
  Future<void> showTestNotification() async {
    await init();

    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        _channelId,
        _channelName,
        channelDescription: _channelDescription,
        importance: Importance.high,
        priority: Priority.high,
        playSound: true,
        enableVibration: true,
      ),
      iOS: DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
      ),
    );

    await _notificationsPlugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      'SnapLingua nhắc học (test)',
      'Nếu bạn thấy được thông báo này thì quyền đã ok.',
      details,
    );
  }

  /// Lên lịch thông báo thử sau [delay] (mặc định 1 phút) để kiểm tra scheduling.
  Future<void> scheduleTestNotification({Duration delay = const Duration(minutes: 1)}) async {
    await init();
    final tz.TZDateTime scheduled =
        tz.TZDateTime.from(DateTime.now().add(delay), tz.local);

    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        _channelId,
        _channelName,
        channelDescription: _channelDescription,
        importance: Importance.high,
        priority: Priority.high,
        playSound: true,
        enableVibration: true,
      ),
      iOS: DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
      ),
    );

    if (_canScheduleExact) {
      await _notificationsPlugin.zonedSchedule(
        DateTime.now().millisecondsSinceEpoch ~/ 1000,
        'SnapLingua nhắc học (test hẹn giờ)',
        'Thông báo test hẹn giờ sau ${delay.inMinutes} phút.',
        scheduled,
        details,
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
        androidAllowWhileIdle: true,
      );
    } else {
      // Fallback: nếu không có quyền exact alarm, dùng delay trong app để đảm bảo người dùng
      // thấy thông báo test, dù có thể không đánh thức thiết bị sau khi app bị kill.
      Future.delayed(delay, () {
        showTestNotification();
      });
    }
  }

  Future<void> updateSchedule({
    required bool enabled,
    required TimeOfDay startTime,
    required TimeOfDay endTime,
    required int dailyFrequency,
    required int weeklyFrequency,
  }) async {
    await init();

    if (!enabled) {
      await cancelAll();
      return;
    }

    await cancelAll();
    await _scheduleNotifications(
      startTime: startTime,
      endTime: endTime,
      dailyFrequency: dailyFrequency,
      weeklyFrequency: weeklyFrequency,
    );
  }

  Future<void> cancelAll() async {
    await _notificationsPlugin.cancelAll();
  }

  Future<void> _scheduleNotifications({
    required TimeOfDay startTime,
    required TimeOfDay endTime,
    required int dailyFrequency,
    required int weeklyFrequency,
  }) async {
    const notificationDetails = NotificationDetails(
      android: AndroidNotificationDetails(
        _channelId,
        _channelName,
        channelDescription: _channelDescription,
        importance: Importance.high,
        priority: Priority.high,
        playSound: true,
        enableVibration: true,
        actions: <AndroidNotificationAction>[
          AndroidNotificationAction(
            'mark_complete',
            'Hoàn thành',
            showsUserInterface: true,
          ),
        ],
      ),
      iOS: DarwinNotificationDetails(
        presentAlert: true,
        presentBadge: true,
        presentSound: true,
      ),
    );

    final List<int> minutesInDay = _calculateDailySchedule(
      startTime: startTime,
      endTime: endTime,
      dailyFrequency: dailyFrequency,
    );

    final List<int> weekdays = _selectWeekdays(weeklyFrequency);
    final Random random = Random();

    for (final weekday in weekdays) {
      for (int index = 0; index < minutesInDay.length; index++) {
        final totalMinutes = minutesInDay[index];
        final int hour = totalMinutes ~/ 60;
        final int minute = totalMinutes % 60;

        final tz.TZDateTime scheduledDate =
            _nextInstanceOfWeekdayTime(weekday, hour, minute);

        final notificationId = weekday * 100 + index;

        final String message =
            _notificationMessages[random.nextInt(_notificationMessages.length)];

        await _notificationsPlugin.zonedSchedule(
          notificationId,
          'SnapLingua nhắc học',
          message,
          scheduledDate,
          notificationDetails,
          androidScheduleMode: _canScheduleExact
              ? AndroidScheduleMode.exactAllowWhileIdle
              : AndroidScheduleMode.inexactAllowWhileIdle,
          uiLocalNotificationDateInterpretation:
              UILocalNotificationDateInterpretation.absoluteTime,
          matchDateTimeComponents: DateTimeComponents.dayOfWeekAndTime,
        );
      }
    }
  }

  List<int> _calculateDailySchedule({
    required TimeOfDay startTime,
    required TimeOfDay endTime,
    required int dailyFrequency,
  }) {
    final int startMinutes = startTime.hour * 60 + startTime.minute;
    final int endMinutes = endTime.hour * 60 + endTime.minute;
    final int range = max(0, endMinutes - startMinutes);

    if (dailyFrequency <= 1 || range == 0) {
      return <int>[startMinutes];
    }

    final List<int> result = <int>[];
    final double step = range / (dailyFrequency - 1);
    for (int i = 0; i < dailyFrequency; i++) {
      final minutes = startMinutes + (step * i).round();
      result.add(minutes);
    }
    return result;
  }

  List<int> _selectWeekdays(int weeklyFrequency) {
    const List<int> allDays = <int>[
      DateTime.monday,
      DateTime.tuesday,
      DateTime.wednesday,
      DateTime.thursday,
      DateTime.friday,
      DateTime.saturday,
      DateTime.sunday,
    ];

    if (weeklyFrequency >= allDays.length) {
      return allDays;
    }

    if (weeklyFrequency <= 1) {
      return <int>[DateTime.monday];
    }

    final List<int> selectedDays = <int>[];
    final double step = allDays.length / weeklyFrequency;

    for (int i = 0; i < weeklyFrequency; i++) {
      final int index = (i * step).round().clamp(0, allDays.length - 1);
      final int day = allDays[index];
      if (!selectedDays.contains(day)) {
        selectedDays.add(day);
      }
    }

    // In case rounding produced fewer unique days, fill with remaining days.
    for (final day in allDays) {
      if (selectedDays.length >= weeklyFrequency) {
        break;
      }
      if (!selectedDays.contains(day)) {
        selectedDays.add(day);
      }
    }

    return selectedDays;
  }

  tz.TZDateTime _nextInstanceOfWeekdayTime(int weekday, int hour, int minute) {
    final tz.TZDateTime now = tz.TZDateTime.now(tz.local);
    tz.TZDateTime scheduledDate =
        tz.TZDateTime(tz.local, now.year, now.month, now.day, hour, minute);

    while (scheduledDate.weekday != weekday || scheduledDate.isBefore(now)) {
      scheduledDate = scheduledDate.add(const Duration(days: 1));
      scheduledDate = tz.TZDateTime(tz.local, scheduledDate.year,
          scheduledDate.month, scheduledDate.day, hour, minute);
    }
    return scheduledDate;
  }

  static const List<String> _notificationMessages = <String>[
    'Học thêm một chút để giữ streak nhé!',
    'Đã đến giờ luyện từ vựng rồi đó!',
    'Hoàn thành mục tiêu hôm nay cùng SnapLingua nào!',
    'Chinh phục thêm vài từ mới bạn nhé!',
    'Giữ phong độ học tập thôi, SnapLingua đồng hành cùng bạn.',
  ];
}
