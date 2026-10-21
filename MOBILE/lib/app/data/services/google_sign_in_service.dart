import 'package:google_sign_in/google_sign_in.dart';

/// The "Web application" OAuth client of the LingoPrism Google Cloud project. A client ID is public
/// (it is not the client secret); the Android client (package com.lingoprism.app + the signing key's
/// SHA-1) is matched by Google itself. Override with --dart-define=GOOGLE_SERVER_CLIENT_ID=… if needed.
const String _serverClientId = String.fromEnvironment(
  'GOOGLE_SERVER_CLIENT_ID',
  defaultValue: '456874322298-c4gor0fd840q17ov372sviemahcohodf.apps.googleusercontent.com',
);

class GoogleSignInService {
  static bool get configured => _serverClientId.isNotEmpty;

  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: [
      'email',
      'profile',
    ],
    // the ID token's audience is this Web client; the backend's GOOGLE_CLIENT_IDS must contain it
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
