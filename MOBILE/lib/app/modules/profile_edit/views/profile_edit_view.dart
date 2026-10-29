import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/profile_edit_controller.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class ProfileEditView extends GetView<ProfileEditController> {
  const ProfileEditView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primarySoft,
      appBar: AppBar(
        backgroundColor: AppColors.primarySoft,
        elevation: 0,
        automaticallyImplyLeading: false,
        leading: controller.welcome
            ? null
            : IconButton(
                onPressed: goBack,
                icon: const Icon(Icons.arrow_back_ios_new_rounded),
                color: AppColors.textPrimary,
              ),
        actions: [
          if (controller.welcome) TextButton(onPressed: controller.skip, child: const Text('Để sau')),
        ],
        title: Text(
          controller.welcome ? 'Hoàn thiện hồ sơ' : 'Cập nhật hồ sơ',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 20.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
        centerTitle: false,
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 16.h),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    if (controller.welcome)
                      Padding(
                        padding: EdgeInsets.only(bottom: 16.h),
                        child: Text(
                          controller.isKid
                              ? 'Chọn ảnh đại diện và cho LingoPrism biết thêm về con nhé.'
                              : 'Thêm ảnh đại diện và vài thông tin để bạn bè dễ nhận ra bạn.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: AppColors.textSecondary, fontSize: 14.sp, height: 1.4),
                        ),
                      ),
                    Obx(() {
                      final avatar = controller.selectedAvatar.value;
                      return Column(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(24.r),
                            child: Container(
                              width: 140.w,
                              height: 140.w,
                              color: AppColors.surface,
                              child: _avatarWidget(avatar),
                            ),
                          ),
                          TextButton(
                            onPressed: () => _showAvatarPicker(context),
                            child: Text(
                              'THAY ẢNH ĐẠI DIỆN',
                              style: TextStyle(
                                color: AppColors.primary,
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
                          color: AppColors.textPrimary,
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
                        fillColor: AppColors.surface,
                        contentPadding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 14.h),
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
                    if (!controller.isKid) ...[
                      SizedBox(height: 20.h),
                      _label('Giới thiệu (không bắt buộc)'),
                      SizedBox(height: 10.h),
                      TextField(
                        controller: controller.bioController,
                        maxLength: 200,
                        minLines: 2,
                        maxLines: 4,
                        decoration: _box(hint: 'VD: Đang luyện HSK 3, thích chụp đồ ăn để học từ'),
                      ),
                    ],
                    SizedBox(height: 12.h),
                    _label('Ngày sinh'),
                    SizedBox(height: 10.h),
                    Obx(() {
                      final d = controller.birthDate.value;
                      return InkWell(
                        borderRadius: BorderRadius.circular(18.r),
                        onTap: () => controller.pickBirthDate(context),
                        child: InputDecorator(
                          decoration: _box(),
                          child: Row(children: [
                            Expanded(
                              child: Text(
                                d == null
                                    ? 'Chọn ngày'
                                    : '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}',
                                style: TextStyle(
                                    fontSize: 15.sp,
                                    color: d == null ? AppColors.textSecondary : AppColors.textPrimary),
                              ),
                            ),
                            Icon(Icons.calendar_month_rounded, color: AppColors.primary),
                          ]),
                        ),
                      );
                    }),
                    SizedBox(height: 20.h),
                    _label('Giới tính'),
                    SizedBox(height: 10.h),
                    Obx(() => Align(
                          alignment: Alignment.centerLeft,
                          child: Wrap(spacing: 10.w, children: [
                            for (final (value, label) in ProfileEditController.genders)
                              ChoiceChip(
                                label: Text(label),
                                selected: controller.gender.value == value,
                                onSelected: (_) => controller.gender.value = value,
                              ),
                          ]),
                        )),
                    SizedBox(height: 16.h),
                    Obx(() {
                      final error = controller.errorMessage.value;
                      if (error.isEmpty) return const SizedBox.shrink();
                      return Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          error,
                          style: TextStyle(
                            color: AppColors.error,
                            fontSize: 13.sp,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      );
                    }),
                  ],
                ),
              ),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(24.w, 8.h, 24.w, 16.h),
              child: Obx(() {
                final isSaving = controller.isSaving.value;
                return SizedBox(
                  width: double.infinity,
                  height: 52.h,
                  child: ElevatedButton(
                    onPressed: isSaving ? null : controller.saveProfile,
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
                              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                          )
                        : Text(
                            controller.welcome ? 'Lưu và bắt đầu' : 'Cập nhật',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 16.sp,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                  ),
                );
              }),
            ),
          ],
        ),
      ),
    );
  }

  Widget _label(String text) => Align(
        alignment: Alignment.centerLeft,
        child: Text(text, style: TextStyle(color: AppColors.textPrimary, fontSize: 16.sp, fontWeight: FontWeight.w700)),
      );

  InputDecoration _box({String? hint}) {
    final edge = OutlineInputBorder(
      borderRadius: BorderRadius.circular(18.r),
      borderSide: BorderSide(color: AppColors.primary, width: 2),
    );
    return InputDecoration(
      hintText: hint,
      filled: true,
      fillColor: AppColors.surface,
      contentPadding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 14.h),
      border: edge,
      enabledBorder: edge,
      focusedBorder: edge,
    );
  }

  void _showAvatarPicker(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.surface,
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
                  color: AppColors.textPrimary,
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
                    if (context.mounted) goBack();
                  },
                  icon: Icon(Icons.photo_library_rounded, color: AppColors.primary),
                  label: Text(
                    'Chọn từ thiết bị',
                    style: TextStyle(
                      color: AppColors.primary,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: BorderSide(color: AppColors.primary, width: 2),
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
                      goBack();
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
