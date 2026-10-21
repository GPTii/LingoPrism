import 'dart:async';
import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/theme/app_colors.dart';
import '../../core/widgets/target_word.dart';
import '../../data/models/api/vocab.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/on_device_detector.dart';
import '../../data/services/tts_service.dart';

/// Camera trực tiếp (thử nghiệm): the phone keeps looking and names what it sees, live, in the
/// language being learned – no photo to take. Runs the same on-device TFLite model as the camera
/// screen, about once a second (research finds real-time detection costly, so it stays an
/// experiment next to the normal photo flow). Tap a label to hear it.
class LiveCameraView extends StatefulWidget {
  const LiveCameraView({super.key});

  @override
  State<LiveCameraView> createState() => _LiveCameraViewState();
}

class _LiveCameraViewState extends State<LiveCameraView> with WidgetsBindingObserver {
  CameraController? _camera;
  Timer? _timer;
  bool _busy = false;
  String _error = '';
  List<OnDeviceBox> _boxes = const [];
  final Map<String, WordCard?> _words = {}; // label → word card (null = no verified word)
  int _ms = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _start();
  }

  Future<void> _start() async {
    try {
      if (!await OnDeviceDetector.instance.available) {
        setState(() => _error = 'Máy này chưa có mô hình nhận diện offline.');
        return;
      }
      final cams = await availableCameras();
      final back = cams.firstWhere((c) => c.lensDirection == CameraLensDirection.back, orElse: () => cams.first);
      final cam = CameraController(back, ResolutionPreset.medium, enableAudio: false);
      await cam.initialize();
      await cam.setFlashMode(FlashMode.off);
      if (!mounted) return cam.dispose();
      setState(() => _camera = cam);
      _timer = Timer.periodic(const Duration(milliseconds: 1100), (_) => _tick());
    } catch (e) {
      setState(() => _error = 'Không mở được camera: $e');
    }
  }

  Future<void> _tick() async {
    final cam = _camera;
    if (_busy || cam == null || !cam.value.isInitialized || cam.value.isTakingPicture) return;
    _busy = true;
    try {
      final shot = await cam.takePicture();
      final (boxes, ms) = await OnDeviceDetector.instance.detect(File(shot.path));
      unawaited(File(shot.path).delete().catchError((_) => File(shot.path)));
      final missing = boxes.map((b) => b.label).where((l) => !_words.containsKey(l)).toSet().toList();
      if (missing.isNotEmpty) {
        try {
          final found = await VocabRepository.byLabels(missing);
          for (final l in missing) {
            _words[l] = found[l];
          }
        } catch (_) {/* offline: labels stay as the model's names */}
      }
      if (mounted) {
        setState(() {
          _boxes = boxes.take(6).toList();
          _ms = ms;
        });
      }
    } catch (_) {
      // a missed frame is fine; the next tick tries again
    } finally {
      _busy = false;
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused) {
      _timer?.cancel();
    } else if (state == AppLifecycleState.resumed && _camera != null && (_timer?.isActive != true)) {
      _timer = Timer.periodic(const Duration(milliseconds: 1100), (_) => _tick());
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    _camera?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cam = _camera;
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: const Text('Camera trực tiếp · thử nghiệm'),
      ),
      body: _error.isNotEmpty
          ? Center(child: Padding(padding: EdgeInsets.all(24.w), child: Text(_error, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white))))
          : cam == null
              ? const Center(child: CircularProgressIndicator())
              : Column(children: [
                  Expanded(
                    child: Center(
                      child: AspectRatio(
                        aspectRatio: 1 / cam.value.aspectRatio,
                        child: LayoutBuilder(builder: (context, box) {
                          return Stack(children: [
                            Positioned.fill(child: CameraPreview(cam)),
                            for (final b in _boxes) _label(b, box.biggest),
                          ]);
                        }),
                      ),
                    ),
                  ),
                  Container(
                    width: double.infinity,
                    color: Colors.black,
                    padding: EdgeInsets.fromLTRB(16.w, 10.h, 16.w, 16.h),
                    child: Text(
                      _boxes.isEmpty ? 'Hướng camera vào một đồ vật…' : 'Chạm vào tên để nghe · ${_ms} ms mỗi lần nhìn',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.white70, fontSize: 13.sp),
                    ),
                  ),
                ]),
    );
  }

  Widget _label(OnDeviceBox b, Size area) {
    final w = _words[b.label];
    final text = w?.target?.text ?? b.label;
    final rect = Rect.fromLTRB(b.bbox[0] * area.width, b.bbox[1] * area.height, b.bbox[2] * area.width, b.bbox[3] * area.height);
    return Positioned.fromRect(
      rect: rect,
      child: Container(
        decoration: BoxDecoration(border: Border.all(color: AppColors.beamMint, width: 2), borderRadius: BorderRadius.circular(6)),
        alignment: Alignment.topLeft,
        child: GestureDetector(
          onTap: () {
            final t = w?.target;
            if (t != null && Get.isRegistered<TtsService>()) TtsService.to.speak(t.text, t.ttsLocale);
          },
          child: Container(
            margin: const EdgeInsets.all(2),
            padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
            decoration: BoxDecoration(color: AppColors.ink.withValues(alpha: 0.85), borderRadius: BorderRadius.circular(6)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
              Text(text,
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 15.sp,
                      locale: (w?.target?.language ?? '').startsWith('zh') ? localeFor(w!.target!.language) : null)),
              if (w != null)
                Text('${w.meaningVi} · ${(b.confidence * 100).round()}%', style: TextStyle(color: Colors.white70, fontSize: 11.sp)),
            ]),
          ),
        ),
      ),
    );
  }
}
