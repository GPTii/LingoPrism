import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:latlong2/latlong.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../data/models/api/learning_extra.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/location_service.dart';
import '../../routes/app_pages.dart';
import '../vocabulary_topic/controllers/vocabulary_topic_controller.dart';

/// Location-based learning: points of interest around the learner and the vocabulary topics
/// that fit each place (the server also sends a notification when you walk into one).
class PoiMapController extends GetxController {
  static const LatLng hcmc = LatLng(10.7769, 106.7009);

  final RxList<Poi> pois = <Poi>[].obs;
  final Rxn<LatLng> me = Rxn<LatLng>();
  final Rxn<Poi> selected = Rxn<Poi>();
  final RxBool loading = false.obs;
  final RxInt radius = 3000.obs;
  final mapController = MapController();

  @override
  void onInit() {
    super.onInit();
    refreshPosition();
  }

  Future<void> refreshPosition() async {
    loading.value = true;
    final p = await LocationService.to.current();
    me.value = p == null ? null : LatLng(p.latitude, p.longitude);
    await loadNearby(me.value ?? hcmc);
    if (me.value != null) mapController.move(me.value!, 14);
    if (p == null && LocationService.to.permissionDenied.value) {
      Get.snackbar('Chưa có vị trí', 'Hãy bật định vị để xem địa điểm quanh bạn. Đang hiển thị trung tâm TP.HCM.',
          snackPosition: SnackPosition.BOTTOM);
    }
    loading.value = false;
  }

  Future<void> loadNearby(LatLng center) async {
    try {
      pois.assignAll(await GisRepository.nearby(center.latitude, center.longitude, radius: radius.value));
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> openTopic(Map<String, dynamic> t) async {
    try {
      final topic = await VocabRepository.topic(int.parse('${t['id']}'));
      Get.toNamed(Routes.vocabularyTopic, arguments: VocabularyTopicArguments(topic: topic));
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }
}

class PoiMapView extends GetView<PoiMapController> {
  const PoiMapView({super.key});

  static const _icons = {
    'market': '🛒', 'supermarket': '🏬', 'hospital': '🏥', 'school': '🏫', 'park': '🌳', 'zoo': '🦁', 'museum': '🏛️',
    'airport': '✈️', 'station': '🚉', 'religious': '⛪', 'restaurant': '🍜', 'stadium': '🏟️', 'landmark': '📍',
    'library': '📚', 'theater': '🎭',
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Học theo vị trí'),
        backgroundColor: AppColors.appBarBackground,
        actions: [IconButton(icon: const Icon(Icons.my_location), onPressed: controller.refreshPosition)],
      ),
      body: Stack(children: [
        Obx(() => FlutterMap(
              mapController: controller.mapController,
              options: MapOptions(
                initialCenter: controller.me.value ?? PoiMapController.hcmc,
                initialZoom: 13,
                onTap: (_, __) => controller.selected.value = null,
              ),
              children: [
                TileLayer(urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', userAgentPackageName: 'com.lingoprism.app'),
                CircleLayer(circles: [
                  for (final p in controller.pois)
                    CircleMarker(
                      point: LatLng(p.lat, p.lng),
                      radius: p.radiusM.toDouble(),
                      useRadiusInMeter: true,
                      color: AppColors.buttonActive.withValues(alpha: 0.12),
                      borderColor: AppColors.buttonActive.withValues(alpha: 0.5),
                      borderStrokeWidth: 1,
                    ),
                ]),
                MarkerLayer(markers: [
                  if (controller.me.value != null)
                    Marker(point: controller.me.value!, width: 22, height: 22,
                        child: Container(decoration: BoxDecoration(color: Colors.blue, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 3)))),
                  for (final p in controller.pois)
                    Marker(
                      point: LatLng(p.lat, p.lng),
                      width: 40,
                      height: 40,
                      child: GestureDetector(
                        onTap: () => controller.selected.value = p,
                        child: Text(_icons[p.category] ?? '📍', style: const TextStyle(fontSize: 28)),
                      ),
                    ),
                ]),
                const RichAttributionWidget(attributions: [TextSourceAttribution('© OpenStreetMap contributors')]),
              ],
            )),
        Obx(() => controller.loading.value ? const LinearProgressIndicator() : const SizedBox()),
        Positioned(
          left: 12.w,
          right: 12.w,
          bottom: 16.h,
          child: Obx(() {
            final p = controller.selected.value;
            if (p == null) {
              return Card(
                child: Padding(
                  padding: EdgeInsets.all(12.w),
                  child: Text('${controller.pois.length} địa điểm trong bán kính ${controller.radius.value ~/ 1000} km. '
                      'Chạm vào một địa điểm để học từ vựng phù hợp.'),
                ),
              );
            }
            return Card(
              child: Padding(
                padding: EdgeInsets.all(14.w),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                  Text('${_icons[p.category] ?? '📍'} ${p.name}', style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700)),
                  Text('${p.categoryLabel}${p.distanceM != null ? ' · cách ${(p.distanceM! / 1000).toStringAsFixed(1)} km' : ''}',
                      style: const TextStyle(color: AppColors.textSecondary)),
                  if (p.address.isNotEmpty) Text(p.address, style: const TextStyle(color: AppColors.textSecondary)),
                  SizedBox(height: 8.h),
                  Wrap(spacing: 8, children: [
                    for (final t in p.topics)
                      ActionChip(label: Text('${t['icon']} ${t['name_vi']}'), onPressed: () => controller.openTopic(t)),
                  ]),
                ]),
              ),
            );
          }),
        ),
      ]),
    );
  }
}
