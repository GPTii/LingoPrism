import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'api_client.dart';
import 'api_config.dart';

class WsEvent {
  WsEvent(this.event, this.payload);

  final String event;
  final Map<String, dynamic> payload;
}

/// WebSocket connection to Django Channels (`/ws/events/`, `/ws/groups/<id>/`, `/ws/support/<id>/`)
/// with JWT auth and automatic reconnect (exponential backoff).
class WsClient {
  WsClient(this.path);

  final String path;
  WebSocketChannel? _channel;
  StreamSubscription? _sub;
  Timer? _retry;
  Timer? _ping;
  int _attempt = 0;
  bool _closed = false;
  final _events = StreamController<WsEvent>.broadcast();
  final connected = ValueNotifier<bool>(false);

  Stream<WsEvent> get events => _events.stream;

  void connect() {
    _closed = false;
    final token = TokenStorage.access;
    if (token == null || ApiConfig.insecure) return; // never a token over plain ws:// in a release build
    final uri = Uri.parse('${ApiConfig.wsBase}$path?token=$token');
    try {
      _channel = WebSocketChannel.connect(uri);
      _sub = _channel!.stream.listen(_onData, onError: (Object _) => _scheduleReconnect(), onDone: _scheduleReconnect);
      _channel!.ready.then((_) {
        _attempt = 0;
        connected.value = true;
        _ping?.cancel();
        _ping = Timer.periodic(const Duration(seconds: 25), (_) => send({'event': 'ping'}));
      }).catchError((Object _) {
        _scheduleReconnect();
      });
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _onData(dynamic raw) {
    try {
      final data = jsonDecode(raw as String) as Map<String, dynamic>;
      _events.add(WsEvent(data['event'] as String? ?? '', Map<String, dynamic>.from(data['payload'] as Map? ?? {})));
    } catch (e) {
      if (kDebugMode) debugPrint('[WsClient] bad message: $e');
    }
  }

  void _scheduleReconnect() {
    connected.value = false;
    _ping?.cancel();
    if (_closed) return;
    _retry?.cancel();
    final delay = Duration(seconds: (1 << _attempt.clamp(0, 5)));
    _attempt++;
    _retry = Timer(delay, connect);
  }

  bool send(Map<String, dynamic> message) {
    if (_channel == null || !connected.value) return false;
    _channel!.sink.add(jsonEncode(message));
    return true;
  }

  void close() {
    _closed = true;
    _retry?.cancel();
    _ping?.cancel();
    _sub?.cancel();
    _channel?.sink.close();
    connected.value = false;
  }

  void dispose() {
    close();
    _events.close();
  }
}
