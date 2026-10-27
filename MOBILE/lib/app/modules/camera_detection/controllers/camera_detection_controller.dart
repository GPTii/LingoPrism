import 'dart:io';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:image_picker/image_picker.dart';
import 'package:image/image.dart' as img;
import 'package:path_provider/path_provider.dart';
import '../../../routes/app_pages.dart';
import '../views/custom_camera_view.dart';
import '../../../core/network/api_client.dart';
import '../../../data/models/api/learning_extra.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/offline_detections.dart';
import '../../../data/services/on_device_detector.dart';

class CameraDetectionController extends GetxController {
  static CameraDetectionController get to => Get.find();

  final _image = Rxn<File>();
  final _isLoading = false.obs;
  final ImagePicker _picker = ImagePicker();

  File? get image => _image.value;
  bool get isLoading => _isLoading.value;

  @override
  void onInit() {
    super.onInit();
    _sync(); // results saved while offline go up as soon as the server answers
  }

  Future<void> _sync() async {
    final n = await OfflineDetections.flush();
    if (n > 0) {
      Get.snackbar('Đã đồng bộ', 'Đã gửi $n kết quả nhận diện lúc offline lên máy chủ.',
          snackPosition: SnackPosition.BOTTOM, duration: const Duration(seconds: 2));
    }
  }

  /// Chụp ảnh từ camera với khung vuông
  Future<void> takePhoto() async {
    try {
      // Open custom camera with square frame
      final result = await Get.to<String>(() => const CustomCameraView());

      if (result == null) {
        debugPrint('❌ Người dùng hủy chụp ảnh');
        return;
      }

      if (result == CustomCameraView.galleryResultTag) {
        await pickFromGallery();
        return;
      }

      debugPrint('📷 Đã chụp ảnh: $result');
      // Crop ảnh thành hình vuông programmatically
      await _cropImageToSquare(result);
    } catch (e) {
      debugPrint('❌ Lỗi khi chụp ảnh: $e');
      _showError('Không thể chụp ảnh: $e');
    }
  }

  /// Chọn ảnh từ thư viện
  Future<void> pickFromGallery() async {
    try {
      final XFile? pickedFile = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
      );

      if (pickedFile != null) {
        debugPrint('🖼️ Đã chọn ảnh: ${pickedFile.path}');
        // Crop ảnh thành hình vuông programmatically
        await _cropImageToSquare(pickedFile.path);
      } else {
        debugPrint('❌ Người dùng hủy chọn ảnh');
      }
    } catch (e) {
      debugPrint('❌ Lỗi khi chọn ảnh: $e');
      _showError('Không thể chọn ảnh: $e');
    }
  }

  /// Crop ảnh thành hình vuông (center crop)
  Future<void> _cropImageToSquare(String imagePath) async {
    try {
      debugPrint('✂️ Đang crop ảnh thành hình vuông...');

      // Read image
      final bytes = await File(imagePath).readAsBytes();
      img.Image? image = img.decodeImage(bytes);

      if (image == null) {
        _showError('Không thể đọc ảnh');
        return;
      }

      // Calculate square size (use smaller dimension)
      final size = image.width < image.height ? image.width : image.height;

      // Calculate crop position (center)
      final x = (image.width - size) ~/ 2;
      final y = (image.height - size) ~/ 2;

      // Crop to square
      final cropped = img.copyCrop(image, x: x, y: y, width: size, height: size);

      // Save cropped image
      final tempDir = await getTemporaryDirectory();
      final croppedPath = '${tempDir.path}/cropped_${DateTime.now().millisecondsSinceEpoch}.jpg';
      final croppedFile = File(croppedPath);
      await croppedFile.writeAsBytes(img.encodeJpg(cropped, quality: 85));

      _image.value = croppedFile;
      debugPrint('✂️ Đã crop ảnh: $croppedPath');

      await _uploadAndDetect();
    } catch (e) {
      debugPrint('❌ Lỗi khi crop ảnh: $e');
      _showError('Không thể xử lý ảnh: $e');
    }
  }

  /// Detect on the phone first (TFLite, no server CPU). A clear photo – every object found at least
  /// [OnDeviceDetector.trustAbove] sure – is used as it is and logged with the photo, so it shows in the history and
  /// the learners' error reports apply. An unclear one (or one where the phone finds nothing) goes to the server's
  /// larger, more accurate model ensemble. When the server is unreachable, busy or has no model, the phone's answer
  /// is used; offline, with the word cards kept on the phone and what the learner saves queued (OfflineDetections).
  Future<void> _uploadAndDetect() async {
    final file = _image.value;
    if (file == null) return;
    _isLoading.value = true;
    try {
      DetectionResult result;
      List<Map<String, dynamic>>? offlineItems;
      final model = OnDeviceDetector.instance.modelName;
      final local = await OnDeviceDetector.instance.available ? await OnDeviceDetector.instance.detect(file) : null;
      final items = local?.$1.map((b) => b.toJson()).toList() ?? <Map<String, dynamic>>[];
      final clear = local != null && local.$1.isNotEmpty && local.$1.every((b) => b.confidence >= OnDeviceDetector.trustAbove);
      try {
        result = clear
            ? await DetectionRepository.logOnDevice(model, local.$2, items, imagePath: file.path)
            : await DetectionRepository.detectOnServer(file.path);
        OfflineDetections.refreshLabels();
        _sync();
      } on ApiException catch (e) {
        if (!(e.isNetwork || e.statusCode == 503 || e.statusCode == 429)) rethrow;
        if (local == null) {
          throw ApiException(e.isNetwork ? 'Không kết nối được máy chủ và máy chưa có mô hình nhận diện offline.' : e.message);
        }
        DetectionResult? logged;
        if (!clear && !e.isNetwork) {
          // the server answers but is busy or has no model: log the phone's answer instead
          try {
            logged = await DetectionRepository.logOnDevice(model, local.$2, items, imagePath: file.path);
          } on ApiException catch (e2) {
            if (!(e2.isNetwork || e2.statusCode == 503 || e2.statusCode == 429)) rethrow;
          }
        }
        if (logged != null) {
          result = logged;
        } else {
          // out of reach: the word cards kept on the phone, and what the learner saves waits in the queue
          if (!OfflineDetections.hasLabels) {
            throw ApiException('Đang offline và máy chưa có bộ từ vựng. Hãy nhận diện một lần khi có mạng để tải về.');
          }
          result = OfflineDetections.result(model, local.$2, items);
          offlineItems = items;
        }
      }
      if (result.items.isEmpty) {
        _showError('Không phát hiện được đối tượng nào. Hãy thử chụp gần và rõ hơn.');
        return;
      }
      Get.toNamed(Routes.detectionResult, arguments: {'result': result, 'image': file, 'offline_items': offlineItems});
    } catch (e) {
      _showError(ApiClient.toApiException(e).message);
    } finally {
      _isLoading.value = false;
    }
  }

  void _showError(String message) {
    Get.snackbar('Lỗi', message,
        snackPosition: SnackPosition.BOTTOM, backgroundColor: Colors.red, colorText: Colors.white, duration: const Duration(seconds: 3));
  }
}
