import 'dart:async';

import 'package:geolocator/geolocator.dart';
import 'package:get/get.dart';

import '../repositories/repositories.dart';
import 'auth_service.dart';

/// Location-based learning: current position for the POI map and periodic geofence checks
/// (the server sends a "gợi ý theo vị trí" notification when the user enters a POI).
class LocationService extends GetxService {
  static LocationService get to => Get.find<LocationService>();

  final Rxn<Position> position = Rxn<Position>();
  final RxBool permissionDenied = false.obs;
  StreamSubscription<Position>? _sub;
  DateTime? _lastCheck;

  Future<Position?> current() async {
    if (!await _ensurePermission()) return null;
    try {
      final p = await Geolocator.getCurrentPosition(locationSettings: const LocationSettings(accuracy: LocationAccuracy.high));
      position.value = p;
      return p;
    } catch (_) {
      return position.value;
    }
  }

  Future<bool> _ensurePermission() async {
    if (!await Geolocator.isLocationServiceEnabled()) {
      permissionDenied.value = true;
      return false;
    }
    var perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) perm = await Geolocator.requestPermission();
    final ok = perm == LocationPermission.always || perm == LocationPermission.whileInUse;
    permissionDenied.value = !ok;
    return ok;
  }

  /// Watch position while the app is open: a position after every 25 m moved, a geofence check at most every 15 s.
  /// The old 100 m / 2 minutes missed 43 % of bike and 61 % of motorbike passes by a POI; 25 m / 15 s found every pass,
  /// ~8 s after entering (server: run_algorithm_experiments --only geofence, BE/apps/algorithms/geofence.py).
  Future<void> startGeofencing() async {
    if (_sub != null || !await _ensurePermission()) return;
    _sub = Geolocator.getPositionStream(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, distanceFilter: 25),
    ).listen((p) {
      position.value = p;
      final now = DateTime.now();
      if (_lastCheck == null || now.difference(_lastCheck!) > const Duration(seconds: 15)) {
        _lastCheck = now;
        if (AuthService.to.isLoggedIn) {
          GisRepository.checkGeofence(p.latitude, p.longitude).catchError((_) => <Map<String, dynamic>>[]);
        }
      }
    });
  }

  void stopGeofencing() {
    _sub?.cancel();
    _sub = null;
  }

  @override
  void onClose() {
    stopGeofencing();
    super.onClose();
  }
}
