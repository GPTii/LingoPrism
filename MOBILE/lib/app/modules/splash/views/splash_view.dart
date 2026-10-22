import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:get/get.dart';

import '../../../core/widgets/prismo_face.dart';
import '../controllers/splash_controller.dart';

/// The opening screen. The phone first shows the still picture (flutter_native_splash: Prismo's face,
/// 180 dp, centred on the brand blue); this screen takes over at the same place and size and brings it to life.
class SplashView extends GetView<SplashController> {
  const SplashView({super.key});

  static const blue = Color(0xFF1899F0);

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.paddingOf(context).bottom;
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light.copyWith(
        statusBarColor: Colors.transparent,
        systemNavigationBarColor: blue,
        systemNavigationBarIconBrightness: Brightness.light,
      ),
      child: Scaffold(
        backgroundColor: blue,
        body: Stack(children: [
          const Center(child: LivingPrismoFace(size: 180)),
          Positioned(
            left: 24,
            right: 24,
            bottom: bottom + 48,
            child: Obx(() => controller.errorMessage.isNotEmpty ? _error() : _wordmark()),
          ),
        ]),
      ),
    );
  }

  Widget _wordmark() => const Text(
        'lingoprism',
        textAlign: TextAlign.center,
        style: TextStyle(color: Colors.white, fontSize: 34, fontWeight: FontWeight.w800, letterSpacing: -0.5),
      ).animate(delay: 650.ms).fadeIn(duration: 380.ms).moveY(begin: 14, end: 0, curve: Curves.easeOutBack, duration: 480.ms);

  Widget _error() => Column(mainAxisSize: MainAxisSize.min, children: [
        Text(controller.errorMessage,
            textAlign: TextAlign.center, style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.4)),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: controller.retry,
          style: FilledButton.styleFrom(backgroundColor: Colors.white, foregroundColor: blue),
          child: const Text('Thử lại', style: TextStyle(fontWeight: FontWeight.w800)),
        ),
      ]);
}
