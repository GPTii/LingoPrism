import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get/get.dart' hide Response, FormData, MultipartFile;
import 'package:get_storage/get_storage.dart';

import 'api_config.dart';

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode, this.errors = const {}});

  final String message;
  final int? statusCode;
  final Map<String, dynamic> errors;

  bool get isNetwork => statusCode == null;
  bool get isUnauthorized => statusCode == 401;

  @override
  String toString() => message;
}

/// Stores the JWT tokens in the platform keystore (Android Keystore / iOS Keychain), never in a plain file another
/// app or a backup could read, and caches the current user (not a secret) in GetStorage. [init] loads the tokens
/// into memory once at start-up so they can be read synchronously.
class TokenStorage {
  TokenStorage._();

  static final GetStorage _box = GetStorage();
  static const FlutterSecureStorage _secure = FlutterSecureStorage();
  static const _accessKey = 'auth.access';
  static const _refreshKey = 'auth.refresh';
  static const _userKey = 'auth.user';

  static String? _access;
  static String? _refresh;

  static Future<void> init() async {
    try {
      _access = await _secure.read(key: _accessKey);
      _refresh = await _secure.read(key: _refreshKey);
    } catch (_) {
      // keystore unreadable (e.g. restored on another phone): sign in again
      await _secure.deleteAll();
    }
    // tokens saved in plain storage by an older version move into the keystore
    final oldAccess = _box.read<String>(_accessKey), oldRefresh = _box.read<String>(_refreshKey);
    if (oldAccess != null || oldRefresh != null) {
      await save(access: _access ?? oldAccess, refresh: _refresh ?? oldRefresh);
      await _box.remove(_accessKey);
      await _box.remove(_refreshKey);
    }
  }

  static String? get access => _access;
  static String? get refresh => _refresh;
  static Map<String, dynamic>? get user {
    final raw = _box.read(_userKey);
    return raw is Map ? Map<String, dynamic>.from(raw) : null;
  }

  static Future<void> save({String? access, String? refresh, Map<String, dynamic>? user}) async {
    if (access != null) {
      _access = access;
      await _secure.write(key: _accessKey, value: access);
    }
    if (refresh != null) {
      _refresh = refresh;
      await _secure.write(key: _refreshKey, value: refresh);
    }
    if (user != null) await _box.write(_userKey, user);
  }

  static Future<void> clear() async {
    _access = null;
    _refresh = null;
    await _secure.delete(key: _accessKey);
    await _secure.delete(key: _refreshKey);
    await _box.remove(_userKey);
  }
}

/// Single HTTP client for the Django REST API. Adds the JWT, refreshes it once on 401 and
/// converts every failure into an [ApiException] with a Vietnamese message from the backend.
class ApiClient extends GetxService {
  static ApiClient get to => Get.find<ApiClient>();

  late final Dio dio;
  Completer<bool>? _refreshing;

  /// Called when the refresh token is no longer valid (AuthService logs out).
  void Function()? onSessionExpired;

  ApiClient() {
    dio = Dio(BaseOptions(
      baseUrl: ApiConfig.apiBase,
      connectTimeout: const Duration(seconds: 12),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Accept': 'application/json'},
    ));
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (ApiConfig.insecure) {
          return handler.reject(DioException(requestOptions: options, error: 'insecure',
              message: 'Bản phát hành chỉ kết nối máy chủ qua HTTPS (API_URL phải là https://).'));
        }
        final token = TokenStorage.access;
        if (token != null && options.extra['noAuth'] != true) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        final req = error.requestOptions;
        if (error.response?.statusCode == 401 && req.extra['retried'] != true && req.extra['noAuth'] != true) {
          if (await _refreshToken()) {
            req.extra['retried'] = true;
            req.headers['Authorization'] = 'Bearer ${TokenStorage.access}';
            try {
              return handler.resolve(await dio.fetch(req));
            } on DioException catch (e) {
              return handler.next(e);
            }
          }
          onSessionExpired?.call();
        }
        handler.next(error);
      },
    ));
  }

  Future<bool> _refreshToken() async {
    if (_refreshing != null) return _refreshing!.future;
    final refresh = TokenStorage.refresh;
    if (refresh == null) return false;
    _refreshing = Completer<bool>();
    try {
      final res = await dio.post('/auth/refresh/', data: {'refresh': refresh}, options: Options(extra: {'noAuth': true}));
      await TokenStorage.save(access: res.data['access'] as String?, refresh: res.data['refresh'] as String?);
      _refreshing!.complete(true);
    } catch (_) {
      _refreshing!.complete(false);
    }
    final ok = await _refreshing!.future;
    _refreshing = null;
    return ok;
  }

  static ApiException toApiException(Object error) {
    if (error is ApiException) return error;
    if (error is DioException) {
      final data = error.response?.data;
      if (data is Map && data['detail'] != null) {
        return ApiException(data['detail'].toString(),
            statusCode: error.response?.statusCode, errors: Map<String, dynamic>.from(data['errors'] ?? {}));
      }
      if (error.error == 'insecure') return ApiException(error.message ?? 'Kết nối không an toàn.');
      if (error.response == null) {
        return ApiException('Không kết nối được máy chủ. Kiểm tra mạng và thử lại.');
      }
      return ApiException('Có lỗi xảy ra (${error.response?.statusCode}).', statusCode: error.response?.statusCode);
    }
    if (kDebugMode) debugPrint('[ApiClient] $error');
    return ApiException('Có lỗi xảy ra, vui lòng thử lại.');
  }

  Future<T> _wrap<T>(Future<Response> Function() call) async {
    try {
      final res = await call();
      return res.data as T;
    } catch (e) {
      throw toApiException(e);
    }
  }

  Future<T> get<T>(String path, {Map<String, dynamic>? query}) =>
      _wrap<T>(() => dio.get(path, queryParameters: _clean(query)));

  Future<T> post<T>(String path, {Object? data, Map<String, dynamic>? query, bool auth = true}) =>
      _wrap<T>(() => dio.post(path, data: data, queryParameters: _clean(query), options: Options(extra: {'noAuth': !auth})));

  Future<T> patch<T>(String path, {Object? data}) => _wrap<T>(() => dio.patch(path, data: data));

  Future<T> delete<T>(String path, {Object? data}) => _wrap<T>(() => dio.delete(path, data: data));

  /// Multipart upload (images). List values are sent as repeated fields (DRF ListField).
  Future<T> upload<T>(String path,
      {required String filePath, String field = 'image', Map<String, dynamic>? fields, String method = 'POST'}) {
    return _wrap<T>(() async {
      final form = FormData.fromMap({
        ...?fields,
        field: await MultipartFile.fromFile(filePath, filename: filePath.split(RegExp(r'[\\/]')).last),
      }, ListFormat.multi);
      return dio.request(path, data: form, options: Options(method: method));
    });
  }

  /// Unwraps DRF pagination ({count, next, results}) or returns a plain list.
  static List<Map<String, dynamic>> results(dynamic data) {
    final list = data is Map ? (data['results'] as List? ?? const []) : (data as List? ?? const []);
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  static Map<String, dynamic>? _clean(Map<String, dynamic>? q) {
    if (q == null) return null;
    return Map.fromEntries(q.entries.where((e) => e.value != null && e.value != ''));
  }
}
