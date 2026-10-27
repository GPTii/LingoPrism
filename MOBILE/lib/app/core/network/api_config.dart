import 'package:flutter/foundation.dart';

/// Backend address, injected at build time:
///   flutter run --dart-define=API_URL=http://10.0.2.2:8000          (Android emulator)
///   flutter run --dart-define=API_URL=http://192.168.1.10:8000      (real phone, same Wi-Fi)
///   flutter build apk --dart-define=API_URL=https://lingoprism.id.vn
/// A release build only ever talks HTTPS (see [insecure]).
class ApiConfig {
  ApiConfig._();

  static const String baseUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');

  static String get apiBase => '$baseUrl/api/v1';

  static String get wsBase => baseUrl.replaceFirst(RegExp(r'^http'), 'ws');

  /// A release build pointed at plain http: every call is refused before it leaves the phone, so a password or a
  /// token never crosses the network unencrypted. (Android's usesCleartextTraffic=false does not cover Dart's own
  /// HTTP client, which is what Dio and the WebSocket use, so the rule has to live here.)
  static bool get insecure => kReleaseMode && !baseUrl.startsWith('https://');

  /// Media paths returned by the API are absolute; this handles the rare relative one.
  static String absolute(String? url) {
    if (url == null || url.isEmpty) return '';
    if (url.startsWith('http') || url.startsWith('assets/')) return url;
    return '$baseUrl$url';
  }
}
