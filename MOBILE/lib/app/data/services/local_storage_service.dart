import 'package:shared_preferences/shared_preferences.dart';

class UserData {
  final String userId;
  final String? email;
  final String? displayName;
  final String? avatarUrl;

  UserData({
    required this.userId,
    this.email,
    this.displayName,
    this.avatarUrl,
  });
}

class LocalStorageService {
  static const String _keyIsFirstLaunch = 'is_first_launch';
  static const String _keyIsLoggedIn = 'is_logged_in';
  static const String _keyUserId = 'user_id';
  static const String _keyUserEmail = 'user_email';
  static const String _keyUserDisplayName = 'user_display_name';
  static const String _keyUserAvatarUrl = 'user_avatar_url';

  /// Kiểm tra có phải lần đầu mở app không
  static Future<bool> isFirstLaunch() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_keyIsFirstLaunch) ?? true;
  }

  /// Đánh dấu đã xem onboarding
  static Future<void> setFirstLaunchComplete() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyIsFirstLaunch, false);
  }

  /// Kiểm tra trạng thái đăng nhập
  static Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_keyIsLoggedIn) ?? false;
  }

  /// Lưu thông tin user sau khi đăng nhập
  static Future<void> saveUserData({
    required String userId,
    String? email,
    String? displayName,
    String? avatarUrl,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyIsLoggedIn, true);
    await prefs.setString(_keyUserId, userId);
    if (email != null) {
      await prefs.setString(_keyUserEmail, email);
    }
    if (displayName != null) {
      await prefs.setString(_keyUserDisplayName, displayName);
    }
    if (avatarUrl != null) {
      await prefs.setString(_keyUserAvatarUrl, avatarUrl);
    }
  }

  /// Lấy thông tin user đã lưu
  static Future<UserData?> getUserData() async {
    final prefs = await SharedPreferences.getInstance();
    final isLoggedIn = prefs.getBool(_keyIsLoggedIn) ?? false;

    if (!isLoggedIn) return null;

    final userId = prefs.getString(_keyUserId);
    if (userId == null) return null;

    return UserData(
      userId: userId,
      email: prefs.getString(_keyUserEmail),
      displayName: prefs.getString(_keyUserDisplayName),
      avatarUrl: prefs.getString(_keyUserAvatarUrl),
    );
  }

  /// Xóa thông tin user khi đăng xuất
  static Future<void> clearUserData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_keyIsLoggedIn, false);
    await prefs.remove(_keyUserId);
    await prefs.remove(_keyUserEmail);
    await prefs.remove(_keyUserDisplayName);
    await prefs.remove(_keyUserAvatarUrl);
  }

  /// Reset tất cả (for testing)
  static Future<void> clearAll() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
  }
}
