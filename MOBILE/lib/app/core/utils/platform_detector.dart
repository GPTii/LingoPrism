import 'dart:io';
import 'package:flutter/foundation.dart';

/// Utility class để detect platform và environment
class PlatformDetector {
  /// Kiểm tra xem có phải đang chạy trên Android emulator không
  static bool get isAndroidEmulator {
    if (!Platform.isAndroid) return false;

    // Thử bắt một số chỉ dấu mà Flutter expose qua env (không tin cậy tuyệt đối
    // nhưng tránh việc auto coi thiết bị thật là emulator chỉ vì đang debug).
    const possibleKeys = ['ANDROID_PRODUCT', 'ANDROID_MODEL', 'ANDROID_HARDWARE'];
    final indicators = <String>[
      for (final key in possibleKeys)
        (Platform.environment[key] ?? '').toLowerCase(),
    ].where((e) => e.isNotEmpty).toList();

    return indicators.any((v) =>
        v.contains('sdk') ||
        v.contains('emulator') ||
        v.contains('gphone') ||
        v.contains('generic'));
  }

  /// Kiểm tra xem có phải đang chạy trên iOS simulator không
  static bool get isIOSSimulator {
    if (!Platform.isIOS) return false;

    // iOS simulator chạy trên architecture x86_64 hoặc arm64 (M1)
    // Nhưng Flutter không expose info này dễ dàng
    // Nên ta cũng dùng debug mode để detect
    return kDebugMode;
  }

  /// Kiểm tra có phải emulator/simulator không
  static bool get isEmulator {
    return isAndroidEmulator || isIOSSimulator;
  }

  /// Kiểm tra có phải real device không
  static bool get isRealDevice {
    return !isEmulator;
  }

  /// Lấy base URL phù hợp cho backend
  ///
  /// - Android Emulator: 10.0.2.2 (địa chỉ đặc biệt trỏ đến localhost của host machine)
  /// - iOS Simulator: localhost
  /// - Real Device: IP của máy trong mạng LAN
  static String getBackendUrl({
    required String localIp,
    required int port,
    bool useHttps = false,
  }) {
    final protocol = useHttps ? 'https' : 'http';

    if (kIsWeb) {
      // Web app: dùng localhost
      return '$protocol://localhost:$port';
    }

    if (Platform.isAndroid) {
      // Emulator luôn dùng 10.0.2.2 để trỏ về host, kể cả build release
      if (isAndroidEmulator) {
        return '$protocol://10.0.2.2:$port';
      }
      // Real device: IP của máy trên LAN
      return '$protocol://$localIp:$port';
    }

    if (Platform.isIOS) {
      // Simulator dùng localhost, kể cả build release
      if (isIOSSimulator) {
        return '$protocol://localhost:$port';
      }
      // Real device: IP của máy trên LAN
      return '$protocol://$localIp:$port';
    }

    // Fallback: dùng IP thật
    return '$protocol://$localIp:$port';
  }
}
