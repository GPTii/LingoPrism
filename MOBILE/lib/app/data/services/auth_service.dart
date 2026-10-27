import 'package:get/get.dart';

import '../../core/network/api_client.dart';
import '../models/api/user.dart';
import '../repositories/repositories.dart';
import 'google_sign_in_service.dart';
import 'push_service.dart';
import '../../routes/app_pages.dart';

/// Session state for the whole app (JWT stored locally, user profile from `/me/`).
///
/// Methods keep the `{'success': bool, 'message': String}` result shape the screens expect.
class AuthService extends GetxService {
  static AuthService get to => Get.find<AuthService>();

  final Rxn<AppUser> user = Rxn<AppUser>();
  final RxBool _isLoggedIn = false.obs;

  bool get isLoggedIn => _isLoggedIn.value;
  String get currentUserId => user.value?.id.toString() ?? '';
  int get userId => user.value?.id ?? 0;
  String get currentUserEmail => user.value?.email ?? '';
  AppUser? get currentUser => user.value;

  @override
  void onInit() {
    super.onInit();
    ApiClient.to.onSessionExpired = () {
      if (_isLoggedIn.value) logout(remote: false);
    };
    final cached = TokenStorage.user;
    if (TokenStorage.access != null && cached != null) {
      user.value = AppUser.fromJson(cached);
      _isLoggedIn.value = true;
    }
  }

  /// Refresh the profile from the server (called on app start and after settings changes).
  Future<AppUser?> refreshUser() async {
    if (!_isLoggedIn.value) return null;
    try {
      final me = await AuthRepository.me();
      await _setUser(me);
      return me;
    } on ApiException catch (e) {
      if (e.isUnauthorized) await logout(remote: false);
      return user.value;
    }
  }

  Future<void> _setUser(AppUser u) async {
    user.value = u;
    await TokenStorage.save(user: u.toJson());
  }

  /// A fresh profile from an endpoint that answers with it (e-mail verified, parent agreed…).
  Future<void> applyUser(AppUser u) => _setUser(u);

  /// Where a signed-in learner goes: the first-visit survey, then – for a child – the parent's consent, then home.
  String get nextRoute {
    final u = user.value;
    if (u == null) return Routes.login;
    if (!u.onboardingCompleted) return Routes.survey;
    return u.needsParent ? Routes.parentConsent : Routes.home;
  }

  Future<void> _startSession(AppUser u, String access, String refresh) async {
    await TokenStorage.save(access: access, refresh: refresh, user: u.toJson());
    user.value = u;
    _isLoggedIn.value = true;
  }

  Map<String, dynamic> _ok(String m) => {'success': true, 'message': m};
  Map<String, dynamic> _fail(Object e) => {'success': false, 'message': ApiClient.toApiException(e).message};

  Future<Map<String, dynamic>> register({required String email, required String password, String? name}) async {
    try {
      final (u, access, refresh) = await AuthRepository.register(email.trim(), password, name ?? email.split('@').first);
      await _startSession(u, access, refresh);
      return _ok('Đăng ký thành công');
    } catch (e) {
      return _fail(e);
    }
  }

  Future<Map<String, dynamic>> login({required String email, required String password}) async {
    try {
      final (u, access, refresh) = await AuthRepository.login(email.trim(), password);
      await _startSession(u, access, refresh);
      return _ok('Đăng nhập thành công');
    } catch (e) {
      return _fail(e);
    }
  }

  /// Google sign-in: the ID token is verified by the backend (`/auth/google/`).
  Future<Map<String, dynamic>> loginWithGoogle() async {
    final google = GoogleSignInService();
    try {
      final account = await google.signIn();
      if (account == null) return {'success': false, 'message': 'Đăng nhập Google bị hủy', 'cancelled': true};
      final idToken = await google.getIdToken(account);
      if (idToken == null) return {'success': false, 'message': 'Không lấy được mã xác thực từ Google'};
      final (u, access, refresh) = await AuthRepository.google(idToken);
      await _startSession(u, access, refresh);
      return _ok('Đăng nhập thành công');
    } catch (e) {
      await google.signOut();
      return _fail(e);
    }
  }

  Future<void> logout({bool remote = true}) async {
    final refresh = TokenStorage.refresh;
    if (remote) await PushService.stop(); // while the session still works
    if (remote && refresh != null) {
      try {
        await AuthRepository.logout(refresh);
      } catch (_) {}
    }
    await TokenStorage.clear();
    try {
      await GoogleSignInService().signOut();
    } catch (_) {}
    user.value = null;
    _isLoggedIn.value = false;
  }

  Future<Map<String, dynamic>> sendPasswordResetCode(String email) async {
    try {
      await AuthRepository.forgot(email.trim());
      return _ok('Mã xác thực đã được gửi đến email của bạn');
    } catch (e) {
      return _fail(e);
    }
  }

  /// Returns {'success', 'message', 'reset_token'}.
  Future<Map<String, dynamic>> verifyResetCode({required String email, required String code}) async {
    try {
      final token = await AuthRepository.verify(email.trim(), code.trim());
      return {'success': true, 'message': 'Mã xác thực đúng', 'reset_token': token};
    } catch (e) {
      return _fail(e);
    }
  }

  Future<Map<String, dynamic>> resetPassword({required String resetToken, required String newPassword}) async {
    try {
      await AuthRepository.reset(resetToken, newPassword);
      return _ok('Mật khẩu đã được đặt lại thành công');
    } catch (e) {
      return _fail(e);
    }
  }

  Future<Map<String, dynamic>> changePassword({required String currentPassword, required String newPassword, String? confirmPassword}) async {
    if (currentPassword.isEmpty || newPassword.isEmpty) return {'success': false, 'message': 'Vui lòng nhập đầy đủ thông tin'};
    if (confirmPassword != null && confirmPassword != newPassword) {
      return {'success': false, 'message': 'Xác nhận mật khẩu không khớp'};
    }
    try {
      await AuthRepository.changePassword(currentPassword, newPassword);
      return _ok('Đổi mật khẩu thành công');
    } catch (e) {
      return _fail(e);
    }
  }

  /// PATCH /me/ and keep the cached profile in sync.
  Future<AppUser> updateProfile(Map<String, dynamic> data) async {
    final u = await AuthRepository.updateMe(data);
    await _setUser(u);
    return u;
  }

  Future<AppUser> uploadAvatar(String path) async {
    final u = await AuthRepository.uploadAvatar(path);
    await _setUser(u);
    return u;
  }

  Future<void> updateGoal({int? dailyNew, int? dailyReview, String? morning, String? evening}) async {
    await AuthRepository.updateGoal({
      if (dailyNew != null) 'daily_new_target': dailyNew,
      if (dailyReview != null) 'daily_review_target': dailyReview,
      if (morning != null) 'remind_morning': morning,
      if (evening != null) 'remind_evening': evening,
    });
    await refreshUser();
  }
}
