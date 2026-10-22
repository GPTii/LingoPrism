import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/theme/app_colors.dart';
import '../controllers/add_vocabulary_category_controller.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class AddVocabularyCategoryView
    extends GetView<AddVocabularyCategoryController> {
  const AddVocabularyCategoryView({super.key});

  @override
  Widget build(BuildContext context) {
    final bottomPadding = MediaQuery.of(context).viewInsets.bottom;
    return Scaffold(
      resizeToAvoidBottomInset: true,
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        leading: IconButton(
          onPressed: () => goBack(),
          icon: Icon(
            Icons.arrow_back,
            color: AppColors.textPrimary,
          ),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: EdgeInsets.fromLTRB(24.w, 8.h, 24.w, 24.h),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Thêm chủ đề',
                      style: TextStyle(
                        fontSize: 28.sp,
                        fontWeight: FontWeight.w700,
                        color: AppColors.ink,
                      ),
                    ),
                    SizedBox(height: 24.h),
                    Text(
                      'Vui lòng chọn icon và đặt tên cho chủ đề mới của bạn.',
                      style: TextStyle(
                        fontSize: 14.sp,
                        color: AppColors.textSecondary,
                      ),
                    ),
                    SizedBox(height: 32.h),
                    _IconPickerSection(controller: controller),
                    SizedBox(height: 24.h),
                    _NameField(controller: controller),
                  ],
                ),
              ),
            ),
            Container(
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
                border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
              padding: EdgeInsets.fromLTRB(24.w, 16.h, 24.w,
                  bottomPadding > 0 ? bottomPadding + 16 : 24.h),
              child: SizedBox(
                width: double.infinity,
                child: Obx(
                  () => ElevatedButton(
                    onPressed:
                        controller.canSave.value ? controller.onSave : null,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      disabledBackgroundColor: AppColors.primaryLight,
                      elevation: 0,
                      padding: EdgeInsets.symmetric(vertical: 16.h),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14.r),
                      ),
                    ),
                    child: Text(
                      'Lưu lại',
                      style: TextStyle(
                        fontSize: 18.sp,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _IconPickerSection extends StatelessWidget {
  const _IconPickerSection({required this.controller});

  final AddVocabularyCategoryController controller;

  @override
  Widget build(BuildContext context) {
    return Obx(
      () {
        final icon = controller.selectedIcon.value;
        final error = controller.iconError.value;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _RequiredLabel(label: 'Icon'),
            SizedBox(height: 12.h),
            GestureDetector(
              onTap: controller.openIconPicker,
              child: Container(
                width: 64.w,
                height: 64.w,
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: error == null
                        ? AppColors.primary
                        : AppColors.error,
                    width: 2,
                  ),),
                child: Center(
                  child: icon == null
                      ? Text(
                          '+',
                          style: TextStyle(
                            fontSize: 32.sp,
                            fontWeight: FontWeight.bold,
                            color: AppColors.primary,
                          ),
                        )
                      : Text(
                          icon,
                          style: TextStyle(fontSize: 32.sp),
                        ),
                ),
              ),
            ),
            if (error != null) ...[
              SizedBox(height: 8.h),
              Text(
                error,
                style: TextStyle(
                  fontSize: 12.sp,
                  color: AppColors.error,
                ),
              ),
            ],
          ],
        );
      },
    );
  }
}

class _NameField extends StatelessWidget {
  const _NameField({required this.controller});

  final AddVocabularyCategoryController controller;

  @override
  Widget build(BuildContext context) {
    return Obx(
      () {
        final error = controller.nameError.value;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const _RequiredLabel(label: 'Tên chủ đề'),
            SizedBox(height: 12.h),
            TextField(
              controller: controller.nameController,
              decoration: InputDecoration(
                hintText: 'Nhập tên chủ đề...',
                filled: true,
                fillColor: AppColors.surface,
                contentPadding: EdgeInsets.symmetric(
                  horizontal: 20.w,
                  vertical: 18.h,
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24.r),
                  borderSide: BorderSide(
                    color: error == null
                        ? AppColors.primarySoft
                        : AppColors.error,
                    width: 1.5,
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24.r),
                  borderSide: BorderSide(
                    color: error == null
                        ? AppColors.primary
                        : AppColors.error,
                    width: 1.8,
                  ),
                ),
                errorText: error,
              ),
              textInputAction: TextInputAction.done,
              onSubmitted: (_) {
                if (controller.canSave.value) {
                  controller.onSave();
                }
              },
            ),
          ],
        );
      },
    );
  }
}

class _RequiredLabel extends StatelessWidget {
  const _RequiredLabel({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return RichText(
      text: TextSpan(
        text: '',
        style: TextStyle(
          fontSize: 14.sp,
          color: AppColors.ink,
          fontWeight: FontWeight.w600,
        ),
        children: [
          TextSpan(
            text: '* ',
            style: TextStyle(
              color: AppColors.error,
              fontWeight: FontWeight.w600,
            ),
          ),
          TextSpan(
            text: label,
          ),
        ],
      ),
    );
  }
}
