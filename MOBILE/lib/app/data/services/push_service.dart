import 'dart:async';
import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:get/get.dart';

import '../../core/network/api_client.dart';

/// Push notifications (FCM). The server sends one for every new in-app notification (apps.push).
///
/// Off until Firebase is configured: without android/app/google-services.json (or the iOS plist)
/// Firebase cannot start and everything here quietly does nothing.
class PushService {
  PushService._();

  static String? _token;
  static StreamSubscription<String>? _refresh;
  static bool _listening = false;

  /// After sign-in: ask permission, register this phone's token with the server, listen for messages.
  static Future<void> start() async {
    try {
      if (Firebase.apps.isEmpty) await Firebase.initializeApp();
    } catch (e) {
      if (kDebugMode) debugPrint('[Push] off (Firebase not configured): $e');
      return;
    }
    try {
      // the channel the server sends to (apps/push/fcm.py: "lingoprism_default")
      await FlutterLocalNotificationsPlugin()
          .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(const AndroidNotificationChannel('lingoprism_default', 'Thông báo LingoPrism',
              description: 'Nhắc ôn tập, thành tích, cộng đồng', importance: Importance.high));
      final fm = FirebaseMessaging.instance;
      await fm.requestPermission();
      // the classic registration token: what the server's FCM HTTP v1 sender targets (message.token)
      // ignore: deprecated_member_use
      _token = await fm.getToken();
      if (_token != null) await _register(_token!);
      // ignore: deprecated_member_use
      _refresh ??= fm.onTokenRefresh.listen((t) {
        _token = t;
        _register(t);
      });
      if (!_listening) {
        _listening = true;
        // in the foreground Android shows nothing by itself: show it inside the app
        FirebaseMessaging.onMessage.listen((m) {
          final n = m.notification;
          if (n != null) {
            Get.snackbar(n.title ?? 'LingoPrism', n.body ?? '', snackPosition: SnackPosition.TOP,
                onTap: (_) => _open(m.data), duration: const Duration(seconds: 4), margin: const EdgeInsets.all(12));
          }
        });
        FirebaseMessaging.onMessageOpenedApp.listen((m) => _open(m.data));
        final first = await fm.getInitialMessage();
        if (first != null) _open(first.data);
      }
    } catch (e) {
      if (kDebugMode) debugPrint('[Push] $e');
    }
  }

  /// Before sign-out (while still signed in): this phone stops getting the account's notifications.
  static Future<void> stop() async {
    final t = _token;
    if (t == null) return;
    try {
      await ApiClient.to.post<dynamic>('/devices/unregister/', data: {'token': t});
    } catch (_) {}
  }

  static Future<void> _register(String token) async {
    try {
      await ApiClient.to.post<dynamic>('/devices/', data: {'token': token, 'platform': Platform.isIOS ? 'ios' : 'android'});
    } catch (_) {/* tried again at the next start */}
  }

  /// A notification can carry the screen to open ({"route": "/review"}).
  static void _open(Map<String, dynamic> data) {
    final route = data['route'];
    if (route is String && route.startsWith('/')) Get.toNamed(route);
  }
}
