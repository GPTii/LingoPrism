import 'package:get/get.dart';

/// The home shell's bottom tabs. Taking a photo is CameraDetectionController's job (the camera button).
class HomeController extends GetxController {
  static HomeController get to => Get.find();

  final _currentIndex = 0.obs;

  int get currentIndex => _currentIndex.value;

  void changeTab(int index) {
    _currentIndex.value = index;
  }
}
