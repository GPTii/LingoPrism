import 'package:camera/camera.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../../../core/theme/app_colors.dart';

class CustomCameraView extends StatefulWidget {
  static const String galleryResultTag = '__gallery__';

  const CustomCameraView({super.key});

  @override
  State<CustomCameraView> createState() => _CustomCameraViewState();
}

class _CustomCameraViewState extends State<CustomCameraView> {
  CameraController? _controller;
  List<CameraDescription>? _cameras;
  bool _isInitialized = false;
  bool _isTakingPicture = false;
  late final AudioPlayer _shutterPlayer;
  int _currentCameraIndex = 0;
  FlashMode _flashMode = FlashMode.off;
  double _currentZoomLevel = 1.0;
  double _minAvailableZoom = 1.0;
  double _maxAvailableZoom = 1.0;

  @override
  void initState() {
    super.initState();
    _shutterPlayer = AudioPlayer()..setReleaseMode(ReleaseMode.stop);
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras == null || _cameras!.isEmpty) {
        Get.snackbar('Lỗi', 'Không tìm thấy camera');
        Get.back();
        return;
      }

      final initialIndex = _cameras!
          .indexWhere((camera) => camera.lensDirection == CameraLensDirection.back);

      _currentCameraIndex = initialIndex == -1 ? 0 : initialIndex;

      await _startCamera(_currentCameraIndex);
    } catch (e) {
      Get.snackbar('Lỗi', 'Không thể khởi tạo camera: $e');
      Get.back();
    }
  }

  Future<void> _startCamera(int cameraIndex) async {
    final selectedCamera = _cameras![cameraIndex];

    setState(() {
      _isInitialized = false;
    });

    final previousController = _controller;
    final newController = CameraController(
      selectedCamera,
      ResolutionPreset.high,
      enableAudio: false,
      imageFormatGroup: ImageFormatGroup.jpeg,
    );

    try {
      await newController.initialize();

      final minZoom = await newController.getMinZoomLevel();
      final maxZoom = await newController.getMaxZoomLevel();

      await newController.setFlashMode(FlashMode.off);
      await newController.setZoomLevel(minZoom);

      setState(() {
        _controller = newController;
        _isInitialized = true;
        _currentCameraIndex = cameraIndex;
        _flashMode = FlashMode.off;
        _minAvailableZoom = minZoom;
        _maxAvailableZoom = maxZoom;
        _currentZoomLevel = minZoom;
      });
    } catch (e) {
      await newController.dispose();
      if (previousController != null && previousController.value.isInitialized) {
        setState(() {
          _controller = previousController;
          _isInitialized = true;
        });
        Get.snackbar('Lỗi', 'Không thể đổi camera: $e');
      } else {
        Get.snackbar('Lỗi', 'Không thể bật camera: $e');
        Get.back();
      }
      return;
    }

    await previousController?.dispose();
  }

  @override
  void dispose() {
    _shutterPlayer.dispose();
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _playShutterSound() async {
    try {
      await _shutterPlayer.play(AssetSource('sounds/camera.wav'));
    } catch (e) {
      Get.log('Không phát được âm thanh chụp: $e');
    }
  }

  Future<void> _takePicture() async {
    if (_controller == null || !_controller!.value.isInitialized || _isTakingPicture) {
      return;
    }

    setState(() {
      _isTakingPicture = true;
    });

    try {
      // Phát âm thanh khi bấm nút chụp
      _playShutterSound();
      final XFile picture = await _controller!.takePicture();
      Get.back(result: picture.path);
    } catch (e) {
      Get.snackbar('Lỗi', 'Không thể chụp ảnh: $e');
    } finally {
      if (mounted) {
        setState(() {
          _isTakingPicture = false;
        });
      }
    }
  }

  Future<void> _toggleFlash() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    FlashMode nextMode;
    switch (_flashMode) {
      case FlashMode.off:
        nextMode = FlashMode.auto;
        break;
      case FlashMode.auto:
        nextMode = FlashMode.always;
        break;
      case FlashMode.torch:
      case FlashMode.always:
        nextMode = FlashMode.off;
        break;
    }

    try {
      await _controller!.setFlashMode(nextMode);
      setState(() {
        _flashMode = nextMode;
      });
    } catch (_) {
      Get.snackbar('Lỗi', 'Chế độ flash không khả dụng');
    }
  }

  Future<void> _switchCamera() async {
    if (_cameras == null || _cameras!.length < 2) {
      Get.snackbar('Thông báo', 'Thiết bị không hỗ trợ đổi camera');
      return;
    }

    final nextIndex = (_currentCameraIndex + 1) % _cameras!.length;
    await _startCamera(nextIndex);
  }

  Future<void> _cycleZoomLevel() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    final nextZoom = (_currentZoomLevel + 1.0) <= _maxAvailableZoom
        ? _currentZoomLevel + 1.0
        : _minAvailableZoom;

    try {
      await _controller!.setZoomLevel(nextZoom);
      setState(() {
        _currentZoomLevel = nextZoom;
      });
    } catch (_) {
      Get.snackbar('Lỗi', 'Không thể thay đổi mức zoom');
    }
  }

  void _openGallery() {
    Get.back(result: CustomCameraView.galleryResultTag);
  }

  IconData get _flashIcon {
    switch (_flashMode) {
      case FlashMode.auto:
        return Icons.flash_auto;
      case FlashMode.always:
      case FlashMode.torch:
        return Icons.flash_on;
      case FlashMode.off:
        return Icons.flash_off;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized || _controller == null) {
      return const Scaffold(
        backgroundColor: Colors.black,
        body: Center(
          child: CircularProgressIndicator(
            color: Color(0xFF1CB0F6),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: AppColors.appBarBackground,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Get.back(),
        ),
        title: Text(
          'Chụp ảnh',
          style: TextStyle(
            color: Colors.black,
            fontSize: 24.sp,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
              child: Column(
                children: [
                  Container(
                    margin: EdgeInsets.only(bottom: 20.h),
                    padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          const Color(0xFF1CB0F6).withOpacity(0.08),
                          const Color(0xFF50E3D6).withOpacity(0.08),
                        ],
                        begin: Alignment.centerLeft,
                        end: Alignment.centerRight,
                      ),
                      borderRadius: BorderRadius.circular(20.r),
                      border: Border.all(
                        color: const Color(0xFF1CB0F6).withOpacity(0.2),
                        width: 1,
                      ),
                    ),
                    child: Column(
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.camera_alt_rounded,
                              color: const Color(0xFF1CB0F6),
                              size: 20.sp,
                            ),
                            SizedBox(width: 8.w),
                            Text(
                              'Chụp lại vật bạn muốn học',
                              style: TextStyle(
                                fontSize: 15.sp,
                                color: Colors.black87,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ],
                        ),
                        SizedBox(height: 4.h),
                        RichText(
                          textAlign: TextAlign.center,
                          text: TextSpan(
                            style: TextStyle(
                              fontSize: 14.sp,
                              color: Colors.black54,
                              height: 1.3,
                            ),
                            children: [
                              TextSpan(
                                text: 'SnapLingua',
                                style: TextStyle(
                                  color: const Color(0xFF1CB0F6),
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14.sp,
                                ),
                              ),
                              const TextSpan(
                                text: ' sẽ nhận diện và dịch tiếng Anh',
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  _buildCameraSurface(),
                  SizedBox(height: 60.h),
                  _buildBottomControls(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCameraSurface() {
    return LayoutBuilder(
      builder: (context, constraints) {
        // Make camera square based on available width
        final side = constraints.maxWidth;

        return SizedBox(
          width: side,
          height: side,
          child: Stack(
            clipBehavior: Clip.none,
            children: [
                  Positioned.fill(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(40.r),
                      child: _buildCameraPreview(),
                    ),
                  ),
                  Positioned.fill(
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(40.r),
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.black.withOpacity(0.35),
                            Colors.transparent,
                            Colors.black.withOpacity(0.45),
                          ],
                          stops: const [0.0, 0.45, 1.0],
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    top: 24.h,
                    left: 24.w,
                    child: _buildCircleButton(
                      icon: _flashIcon,
                      onTap: _toggleFlash,
                      size: 48.w,
                    ),
                  ),
                  Positioned(
                    top: 24.h,
                    right: 24.w,
                    child: GestureDetector(
                      onTap: _cycleZoomLevel,
                      child: Container(
                        padding:
                            EdgeInsets.symmetric(horizontal: 18.w, vertical: 10.h),
                        decoration: BoxDecoration(
                          color: Colors.black54,
                          borderRadius: BorderRadius.circular(24.r),
                        ),
                        child: Text(
                          '${_currentZoomLevel.toStringAsFixed(1)}x',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                  ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildCameraPreview() {
    final previewSize = _controller!.value.previewSize;
    if (previewSize == null) {
      return CameraPreview(_controller!);
    }

    return FittedBox(
      fit: BoxFit.cover,
      child: SizedBox(
        width: previewSize.height,
        height: previewSize.width,
        child: CameraPreview(_controller!),
      ),
    );
  }

  Widget _buildBottomControls() {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 12.w),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          _buildCircleButton(
            icon: Icons.photo,
            onTap: _openGallery,
            background: Colors.white,
            foreground: Colors.black,
            size: 60.w,
          ),
          GestureDetector(
            onTap: _isTakingPicture ? null : _takePicture,
            child: Stack(
              alignment: Alignment.center,
              children: [
                Container(
                  width: 96.w,
                  height: 96.w,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      colors: [Color.fromARGB(255, 80, 227, 214), Color(0xFF1CB0F6)],
                    ),
                  ),
                ),
                Container(
                  width: 80.w,
                  height: 80.w,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.backgroundLight,
                  ),
                  child: Center(
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      width: _isTakingPicture ? 48.w : 64.w,
                      height: _isTakingPicture ? 48.w : 64.w,
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          colors: [Color.fromARGB(255, 80, 227, 214), Color(0xFF1CB0F6)],
                        ),
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          _buildCircleButton(
            icon: Icons.cameraswitch,
            onTap: _switchCamera,
            size: 60.w,
          ),
        ],
      ),
    );
  }


  Widget _buildCircleButton({
    required IconData icon,
    required VoidCallback? onTap,
    Color background = Colors.black54,
    Color foreground = Colors.white,
    double? size,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: size ?? 44.w,
        height: size ?? 44.w,
        decoration: BoxDecoration(
          color: background,
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          color: foreground,
          size: 22.sp,
        ),
      ),
    );
  }
}
