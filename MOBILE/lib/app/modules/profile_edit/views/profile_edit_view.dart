import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/profile_edit_controller.dart';

class ProfileEditView extends GetView<ProfileEditController> {
  const ProfileEditView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE6F9FF),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE6F9FF),
        elevation: 0,
        leading: IconButton(
          onPressed: Get.back,
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          color: const Color(0xFF0B1D28),
        ),
        title: Text(
          'Cập nhật hồ sơ',
          style: TextStyle(
            color: const Color(0xFF0B1D28),
            fontSize: 20.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
        centerTitle: false,
      ),
      body: Padding(
        padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 24.h),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Obx(() {
              final avatar = controller.selectedAvatar.value;
              return Column(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(24.r),
                    child: Container(
                      width: 140.w,
                      height: 140.w,
                      color: Colors.white,
                      child: _avatarWidget(avatar),
                    ),
                  ),
                  TextButton(
                    onPressed: () => _showAvatarPicker(context),
                    child: Text(
                      'THAY ẢNH ĐẠI DIỆN',
                      style: TextStyle(
                        color: const Color(0xFF1CB0F6),
                        fontWeight: FontWeight.w700,
                        fontSize: 14.sp,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                ],
              );
            }),
            SizedBox(height: 28.h),
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Tên',
                style: TextStyle(
                  color: const Color(0xFF0B1D28),
                  fontSize: 16.sp,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            SizedBox(height: 10.h),
            TextField(
              controller: controller.nameController,
              decoration: InputDecoration(
                filled: true,
                fillColor: Colors.white,
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 18.w, vertical: 14.h),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(18.r),
                  borderSide:
                      const BorderSide(color: Color(0xFF1CB0F6), width: 2),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(18.r),
                  borderSide:
                      const BorderSide(color: Color(0xFF1CB0F6), width: 2),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(18.r),
                  borderSide:
                      const BorderSide(color: Color(0xFF1CB0F6), width: 2),
                ),
              ),
            ),
            SizedBox(height: 16.h),
            Obx(() {
              final error = controller.errorMessage.value;
              if (error.isEmpty) return const SizedBox.shrink();
              return Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  error,
                  style: TextStyle(
                    color: const Color(0xFFE8505B),
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
                  onPressed: isSaving ? null : controller.saveProfile,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1CB0F6),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(26.r),
                    ),
                    elevation: 0,
                  ),
                  child: isSaving
                      ? SizedBox(
                          width: 22.w,
                          height: 22.w,
                          child: const CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(Colors.white),
                          ),
                        )
                      : Text(
                          'Cập nhật',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w700,
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

  void _showAvatarPicker(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
      ),
      builder: (_) {
        return Padding(
          padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 24.h),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Chọn ảnh đại diện',
                style: TextStyle(
                  color: const Color(0xFF0B1D28),
                  fontSize: 16.sp,
                  fontWeight: FontWeight.w700,
                ),
              ),
              SizedBox(height: 16.h),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () async {
                    await controller.pickAvatarFromDevice();
                    if (context.mounted) Get.back();
                  },
                  icon: const Icon(Icons.photo_library_rounded, color: Color(0xFF1CB0F6)),
                  label: Text(
                    'Chọn từ thiết bị',
                    style: TextStyle(
                      color: const Color(0xFF1CB0F6),
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Color(0xFF1CB0F6), width: 2),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16.r),
                    ),
                    padding: EdgeInsets.symmetric(vertical: 12.h),
                  ),
                ),
              ),
              SizedBox(height: 16.h),
              Wrap(
                spacing: 16.w,
                runSpacing: 16.h,
                children: ProfileEditController.avatarOptions.map((path) {
                  return GestureDetector(
                    onTap: () {
                      controller.chooseAvatar(path);
                      Get.back();
                    },
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(18.r),
                      child: Image.asset(
                        path,
                        width: 80.w,
                        height: 80.w,
                        fit: BoxFit.cover,
                      ),
                    ),
                  );
                }).toList(),
              ),
              SizedBox(height: 12.h),
            ],
          ),
        );
      },
    );
  }

  Widget _avatarWidget(String avatar) {
    // Network
    if (avatar.startsWith('http')) {
      return Image.network(
        avatar,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => Image.asset(
          ProfileEditController.avatarOptions.first,
          fit: BoxFit.cover,
        ),
      );
    }
    // Asset
    if (avatar.startsWith('assets/')) {
      return Image.asset(avatar, fit: BoxFit.cover);
    }
    // Local file path
    return Image.file(
      File(avatar),
      fit: BoxFit.cover,
      errorBuilder: (_, __, ___) => Image.asset(
        ProfileEditController.avatarOptions.first,
        fit: BoxFit.cover,
      ),
    );
  }
}
