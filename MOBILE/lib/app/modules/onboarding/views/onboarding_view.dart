import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../controllers/onboarding_controller.dart';

class OnboardingView extends GetView<OnboardingController> {
  const OnboardingView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE5FFFD),
      body: SafeArea(
        child: Column(
          children: [
            SizedBox(height: 40.h),
            Expanded(
              child: PageView.builder(
                controller: controller.pageController,
                onPageChanged: controller.onPageChanged,
                itemCount: controller.onboardingData.length,
                itemBuilder: (context, index) {
                  final data = controller.onboardingData[index];
                  return Padding(
                    padding: EdgeInsets.symmetric(horizontal: 24.w),
                    child: SingleChildScrollView(
                      child: Column(
                        children: [
                          SizedBox(
                            height: 350.h,
                            width: double.infinity,
                            child: Center(
                              child: Image.asset(
                                data.image,
                                height: 300.h,
                                width: 300.w,
                                fit: BoxFit.contain,
                                errorBuilder: (context, error, stackTrace) {
                                  return Container(
                                    height: 200.h,
                                    width: 200.w,
                                    decoration: BoxDecoration(
                                      color: Colors.orange.shade100,
                                      shape: BoxShape.circle,
                                    ),
                                    child: Icon(
                                      Icons.image,
                                      size: 80.sp,
                                      color: Colors.orange,
                                    ),
                                  );
                                },
                              ),
                            ),
                          ),
                          SizedBox(height: 28.h),
                          _buildTitle(data.title, index),
                          SizedBox(height: 12.h),
                          Padding(
                            padding: EdgeInsets.symmetric(horizontal: 8.w),
                            child: Text(
                              data.description,
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 16.sp,
                                fontWeight: FontWeight.bold,
                                height: 1.5,
                                color: Colors.black54,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 24.w),
              child: Column(
                children: [
                  Obx(() => Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(
                          controller.onboardingData.length,
                          (index) => Container(
                            margin: EdgeInsets.symmetric(horizontal: 4.w),
                            width: controller.currentIndex == index ? 24.w : 8.w,
                            height: 8.h,
                            decoration: BoxDecoration(
                              color: controller.currentIndex == index
                                  ? const Color(0xFF0088FF)
                                  : Colors.grey.shade300,
                              borderRadius: BorderRadius.circular(4.r),
                            ),
                          ),
                        ),
                      )),
                  SizedBox(height: 40.h),
                  Obx(() {
                    if (controller.currentIndex == controller.onboardingData.length - 1) {
                      return Row(
                        children: [
                          Expanded(
                            child: OutlinedButton(
                              onPressed: controller.goToLogin,
                              style: OutlinedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                side: const BorderSide(color: const Color(0xFF0088FF)),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                              child: const Text(
                                'Đăng nhập',
                                style: TextStyle(
                                  fontSize: 16,
                                  color: const Color(0xFF0088FF),
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: ElevatedButton(
                              onPressed: controller.goToRegister,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF0088FF),
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                              child: const Text(
                                'Đăng ký',
                                style: TextStyle(
                                  fontSize: 16,
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ),
                        ],
                      );
                    } else {
                      return SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: controller.nextPage,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF0088FF),
                            padding: const EdgeInsets.symmetric(vertical: 16),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: const Text(
                            'Tiếp tục',
                            style: TextStyle(
                              fontSize: 16,
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      );
                    }
                  }),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTitle(String title, int index) {
    final lines = title.split('\n');

    if (index == 2) {
      // Onboarding 3: dòng trên màu xanh
      return RichText(
        textAlign: TextAlign.center,
        text: TextSpan(
          children: [
            TextSpan(
              text: lines[0] + '\n',
              style: TextStyle(
                fontSize: 28.sp,
                fontWeight: FontWeight.bold,
                height: 1.2,
                color: const Color(0xFF0088FF),
              ),
            ),
            TextSpan(
              text: lines[1],
              style: TextStyle(
                fontSize: 28.sp,
                fontWeight: FontWeight.bold,
                height: 1.2,
                color: Colors.black87,
              ),
            ),
          ],
        ),
      );
    } else {
      // Onboarding 1 & 2: dòng dưới màu xanh
      return RichText(
        textAlign: TextAlign.center,
        text: TextSpan(
          children: [
            TextSpan(
              text: lines[0] + '\n',
              style: TextStyle(
                fontSize: 28.sp,
                fontWeight: FontWeight.bold,
                height: 1.2,
                color: Colors.black87,
              ),
            ),
            TextSpan(
              text: lines[1],
              style: TextStyle(
                fontSize: 28.sp,
                fontWeight: FontWeight.bold,
                height: 1.2,
                color: const Color(0xFF0088FF),
              ),
            ),
          ],
        ),
      );
    }
  }
}