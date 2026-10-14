import 'package:google_sign_in/google_sign_in.dart';

const String _serverClientId = String.fromEnvironment('GOOGLE_SERVER_CLIENT_ID');

class GoogleSignInService {
  static bool get configured => _serverClientId.isNotEmpty;

  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'email',
      'profile',
    ],
    // Web OAuth client ID (same value as GOOGLE_CLIENT_IDS on the backend), passed with
    // --dart-define=GOOGLE_SERVER_CLIENT_ID=xxx.apps.googleusercontent.com
    serverClientId: _serverClientId.isEmpty ? null : _serverClientId,
  );

  /// Đăng nhập bằng Google
  Future<GoogleSignInAccount?> signIn() async {
    try {
      final GoogleSignInAccount? account = await _googleSignIn.signIn();
      return account;
    } catch (error) {
      return null;
    }
  }

  /// Đăng xuất Google
  Future<void> signOut() async {
    await _googleSignIn.signOut();
  }

  /// Kiểm tra trạng thái đăng nhập
  Future<GoogleSignInAccount?> get currentUser async {
    return await _googleSignIn.signInSilently();
  }

  /// Lấy ID token để gửi lên server
  Future<String?> getIdToken(GoogleSignInAccount account) async {
    try {
      final GoogleSignInAuthentication auth = await account.authentication;
      return auth.idToken;
    } catch (e) {
      return null;
    }
  }

  /// Lấy thông tin authentication đầy đủ
  Future<GoogleSignInAuthentication?> getAuthentication(GoogleSignInAccount account) async {
    return await account.authentication;
  }
}
