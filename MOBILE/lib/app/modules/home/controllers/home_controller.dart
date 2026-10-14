import 'dart:io';
import 'package:get/get.dart';
import 'package:image_picker/image_picker.dart';

class HomeController extends GetxController {
  static HomeController get to => Get.find();

  final _currentIndex = 0.obs;
  final _selectedImage = Rx<File?>(null);

  int get currentIndex => _currentIndex.value;
  File? get selectedImage => _selectedImage.value;

  void changeTab(int index) {
    _currentIndex.value = index;
  }

  /// Chọn ảnh từ máy ảnh hoặc thư viện
  Future<void> pickImage(ImageSource source) async {
    try {
      final pickedFile = await ImagePicker().pickImage(source: source);
      if (pickedFile != null) {
        _selectedImage.value = File(pickedFile.path);
        print("⚡ Ảnh đã chọn: ${_selectedImage.value!.path}");

        // TODO: Xử lý ảnh - gửi lên server để nhận diện từ vựng
        await _processImage(_selectedImage.value!);
      } else {
        print("❌ Không chọn ảnh nào!");
      }
    } catch (e) {
      print("❌ Lỗi khi chọn ảnh: $e");
      Get.snackbar(
        'Lỗi',
        'Không thể chọn ảnh: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }

  /// Xử lý ảnh - gửi lên server để nhận diện từ vựng
  Future<void> _processImage(File imageFile) async {
    // TODO: Implement image processing
    // 1. Show loading dialog
    // 2. Send image to server
    // 3. Navigate to result page

    Get.snackbar(
      'Thông báo',
      'Đang phát triển chức năng nhận diện từ vựng...',
      snackPosition: SnackPosition.BOTTOM,
    );
  }

}
