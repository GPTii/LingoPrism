import 'dart:async';

import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../core/network/ws_client.dart';
import '../repositories/repositories.dart';
import 'auth_service.dart';
import 'game_service.dart';

/// Keeps `/ws/events/` open while logged in: notifications, XP and quest updates arrive
/// instantly and stay in sync with the web app.
class RealtimeService extends GetxService {
  static RealtimeService get to => Get.find<RealtimeService>();

  final RxInt unreadNotifications = 0.obs;
  final _notifications = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get notifications => _notifications.stream;

  WsClient? _client;
  StreamSubscription? _sub;

  void start() {
    if (!AuthService.to.isLoggedIn || _client != null) return;
    _client = WsClient('/ws/events/')..connect();
    _sub = _client!.events.listen(_onEvent);
    refreshUnread();
  }

  void stop() {
    _sub?.cancel();
    _client?.dispose();
    _client = null;
    unreadNotifications.value = 0;
  }

  Future<void> refreshUnread() async {
    try {
      unreadNotifications.value = await NotificationRepository.unread();
    } catch (_) {}
  }

  void _onEvent(WsEvent e) {
    switch (e.event) {
      case 'notification':
        unreadNotifications.value++;
        _notifications.add(e.payload);
        final title = e.payload['title']?.toString() ?? '';
        if (title.isNotEmpty) {
          Get.snackbar(title, e.payload['body']?.toString() ?? '',
              snackPosition: SnackPosition.TOP, duration: const Duration(seconds: 3), margin: const EdgeInsets.all(12));
        }
        break;
      case 'xp':
        if (Get.isRegistered<GameService>()) GameService.to.applyRealtimeXp(e.payload);
        break;
      case 'quest_completed':
        if (Get.isRegistered<GameService>()) GameService.to.refreshQuests();
        break;
    }
  }

  @override
  void onClose() {
    stop();
    _notifications.close();
    super.onClose();
  }
}
