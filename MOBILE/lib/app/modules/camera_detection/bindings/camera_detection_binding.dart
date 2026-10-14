import 'package:get/get.dart';
import '../controllers/camera_detection_controller.dart';

class CameraDetectionBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut<CameraDetectionController>(
      () => CameraDetectionController(),
    );
  }
}
