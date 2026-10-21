import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';
import 'package:get_storage/get_storage.dart';

import '../../core/network/api_client.dart';

/// Learning without a connection (FEATURES 5.9).
///
/// - While online, one "learn" and one "review" session are fetched ahead and kept on the phone
///   ([prefetch]); when a lesson must start offline, the kept one is used ([takeSession]).
/// - Answers and "finish" calls that cannot reach the server wait in a queue on the phone and are sent,
///   in order, as soon as the connection is back ([flush]). The server applies them as if they had
///   arrived on time, so the review schedule and XP catch up.
class OfflineLearning {
  OfflineLearning._();

  static final GetStorage _box = GetStorage();
  static const _sessionsKey = 'offline_sessions'; // {kind: raw session json}
  static const _queueKey = 'offline_queue'; // [{path, data}]
  static StreamSubscription<ConnectivityResult>? _sub;
  static bool _flushing = false;

  static bool isNetworkError(Object e) => e is ApiException ? e.isNetwork : ApiClient.toApiException(e).isNetwork;

  static int get pendingCount => (_box.read<List>(_queueKey) ?? const []).length;

  /// Start listening for the connection coming back; send what is waiting now.
  static void start() {
    _sub ??= Connectivity().onConnectivityChanged.listen((r) {
      if (r != ConnectivityResult.none) {
        flush();
        prefetch();
      }
    });
    flush();
    prefetch();
  }

  /// Keep one ready-made session per kind on the phone (only fetched when none is kept).
  static Future<void> prefetch() async {
    final kept = Map<String, dynamic>.from(_box.read<Map>(_sessionsKey) ?? {});
    for (final kind in const ['learn', 'review']) {
      if (kept[kind] != null) continue;
      try {
        final raw = await ApiClient.to.post<dynamic>('/sessions/', data: {'kind': kind, 'size': 10});
        final items = (raw is Map ? raw['items'] : null) as List?;
        if (items != null && items.isNotEmpty) kept[kind] = raw;
      } catch (_) {
        return; // offline or nothing to learn: try again later
      }
    }
    await _box.write(_sessionsKey, kept);
  }

  /// The kept session for [kind] (removed once taken), or null.
  static Map<String, dynamic>? takeSession(String kind) {
    final kept = Map<String, dynamic>.from(_box.read<Map>(_sessionsKey) ?? {});
    final raw = kept.remove(kind);
    _box.write(_sessionsKey, kept);
    return raw == null ? null : Map<String, dynamic>.from(raw as Map);
  }

  /// Remember a call to send later.
  static Future<void> enqueue(String path, Map<String, dynamic> data) async {
    final q = List<dynamic>.from(_box.read<List>(_queueKey) ?? const []);
    q.add({'path': path, 'data': data, 'at': DateTime.now().toIso8601String()});
    await _box.write(_queueKey, q);
  }

  /// Send what is waiting, oldest first; stops at the first call that still cannot get through.
  static Future<int> flush() async {
    if (_flushing) return 0;
    _flushing = true;
    var sent = 0;
    try {
      while (true) {
        final q = List<dynamic>.from(_box.read<List>(_queueKey) ?? const []);
        if (q.isEmpty) break;
        final next = Map<String, dynamic>.from(q.first as Map);
        try {
          await ApiClient.to.post<dynamic>(next['path'] as String, data: Map<String, dynamic>.from(next['data'] as Map));
        } catch (e) {
          if (isNetworkError(e)) break; // still offline: keep everything
          // the server refused it (e.g. the session is already closed): drop it so the queue moves on
          if (kDebugMode) debugPrint('[OfflineLearning] dropped ${next['path']}: $e');
        }
        q.removeAt(0);
        await _box.write(_queueKey, q);
        sent++;
      }
    } finally {
      _flushing = false;
    }
    return sent;
  }

  @visibleForTesting
  static Future<void> clearForTest() async {
    await _box.remove(_sessionsKey);
    await _box.remove(_queueKey);
  }
}
