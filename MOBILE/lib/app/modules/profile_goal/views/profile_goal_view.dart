import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/profile_goal_controller.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class ProfileGoalView extends GetView<ProfileGoalController> {
  const ProfileGoalView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primarySoft,
      appBar: AppBar(
        backgroundColor: AppColors.primarySoft,
        elevation: 0,
        leading: IconButton(
          onPressed: goBack,
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          color: AppColors.textPrimary,
        ),
        title: Text(
          'Mục tiêu',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 20.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
        centerTitle: false,
      ),
      body: Padding(
        padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 24.h),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _GoalField(
              label: 'Số từ vựng học mỗi ngày:',
              controller: controller.learnController,
            ),
            SizedBox(height: 24.h),
            _GoalField(
              label: 'Số từ vựng ôn tập mỗi ngày:',
              controller: controller.reviewController,
            ),
            SizedBox(height: 24.h),
            Obx(() {
              final message = controller.errorMessage.value;
              if (message.isEmpty) return const SizedBox.shrink();
              return Padding(
                padding: EdgeInsets.only(bottom: 8.h),
                child: Text(
                  message,
                  style: TextStyle(
                    color: AppColors.error,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              );
            }),
            const Spacer(),
            Obx(() {
              final isSaving = controller.isSaving.value;
              return SizedBox(
                width: double.infinity,
                height: 52.h,
                child: ElevatedButton(
                  onPressed: isSaving ? null : controller.saveGoals,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14.r),
                    ),
                    elevation: 0,
                  ),
                  child: isSaving
                      ? SizedBox(
                          width: 22.w,
                          height: 22.w,
                          child: const CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation(Colors.white),
                          ),
                        )
                      : Text(
                          'Cập nhật',
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                            fontSize: 16.sp,
                          ),
                        ),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
}

class _GoalField extends StatelessWidget {
  const _GoalField({
    required this.label,
    required this.controller,
  });

  final String label;
  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 15.sp,
            fontWeight: FontWeight.w600,
          ),
        ),
        SizedBox(height: 8.h),
        TextField(
          controller: controller,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(
            filled: true,
            fillColor: AppColors.surface,
            contentPadding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18.r),
              borderSide: BorderSide(color: AppColors.primary, width: 2),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18.r),
              borderSide: BorderSide(color: AppColors.primary, width: 2),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(18.r),
              borderSide: BorderSide(color: AppColors.primary, width: 2),
            ),
          ),
        ),
      ],
    );
  }
}
