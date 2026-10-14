import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/community_create_group_controller.dart';

class CommunityCreateGroupView extends GetView<CommunityCreateGroupController> {
  const CommunityCreateGroupView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE6F9FF),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          color: const Color(0xFF1A1D1F),
          onPressed: Get.back,
        ),
        title: Text(
          'Tạo nhóm học',
          style: TextStyle(
            fontSize: 18.sp,
            fontWeight: FontWeight.w700,
            color: const Color(0xFF1A1D1F),
          ),
        ),
        centerTitle: false,
      ),
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 20.w),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  child: Form(
                    key: controller.formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(height: 12.h),
                        _IconSelector(controller: controller),
                        SizedBox(height: 24.h),
                        _GroupTextField(
                          label: 'Tên nhóm học *',
                          controller: controller.nameController,
                          hintText: 'Nhập tên nhóm học',
                        ),
                        SizedBox(height: 18.h),
                        _GroupTextField(
                          label: 'Yêu cầu ngắn *',
                          controller: controller.requirementController,
                          hintText: 'Chia sẻ tiêu chí tham gia',
                        ),
                        SizedBox(height: 28.h),
                        Text(
                          'Duyệt thành viên',
                          style: TextStyle(
                            fontSize: 15.sp,
                            fontWeight: FontWeight.w600,
                            color: const Color(0xFF1A1D1F),
                          ),
                        ),
                        SizedBox(height: 14.h),
                        _ApprovalToggle(controller: controller),
                        SizedBox(height: 40.h),
                      ],
                    ),
                  ),
                ),
              ),
              Obx(
                () => Padding(
                  padding: EdgeInsets.only(bottom: 16.h),
                  child: SizedBox(
                    height: 54.h,
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: controller.canSubmit.value &&
                              !controller.isSubmitting.value
                          ? controller.submit
                          : null,
                      style: ElevatedButton.styleFrom(
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(32.r),
                        ),
                        backgroundColor: controller.canSubmit.value &&
                                !controller.isSubmitting.value
                            ? const Color(0xFF0A69C7)
                            : const Color(0xFFD2D4DB),
                        foregroundColor: Colors.white,
                        textStyle: TextStyle(
                          fontSize: 15.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      child: controller.isSubmitting.value
                          ? SizedBox(
                              height: 20.w,
                              width: 20.w,
                              child: const CircularProgressIndicator(
                                strokeWidth: 2.6,
                                valueColor:
                                    AlwaysStoppedAnimation<Color>(Colors.white),
                              ),
                            )
                          : const Text('Lưu lại'),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _IconSelector extends StatelessWidget {
  const _IconSelector({required this.controller});

  final CommunityCreateGroupController controller;

  @override
  Widget build(BuildContext context) {
    return Obx(
      () {
        final selectedIndex = controller.selectedIconIndex.value;
        final hasSelection = selectedIndex >= 0 &&
            selectedIndex < CommunityCreateGroupController.iconAssets.length;
        final imagePath = hasSelection
            ? CommunityCreateGroupController.iconAssets[selectedIndex]
            : null;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 80.w,
              height: 80.w,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.05),
                    blurRadius: 10.r,
                    offset: Offset(0, 6.h),
                  ),
                ],
              ),
              alignment: Alignment.center,
              child: imagePath != null
                  ? Padding(
                      padding: EdgeInsets.all(12.w),
                      child: Image.asset(imagePath, fit: BoxFit.contain),
                    )
                  : Text(
                      '+ Icon',
                      style: TextStyle(
                        fontSize: 14.sp,
                        fontWeight: FontWeight.w600,
                        color: const Color(0xFF6D7B8C),
                      ),
                    ),
            ),
            SizedBox(height: 18.h),
            Wrap(
              spacing: 14.w,
              runSpacing: 14.h,
              children: List.generate(
                CommunityCreateGroupController.iconAssets.length,
                (index) {
                  final asset =
                      CommunityCreateGroupController.iconAssets[index];
                  final isActive = selectedIndex == index;
                  return GestureDetector(
                    onTap: () => controller.selectIcon(index),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 180),
                      width: 60.w,
                      height: 60.w,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white,
                        border: Border.all(
                          color: isActive
                              ? const Color(0xFF0A69C7)
                              : const Color(0xFFD4E5F7),
                          width: isActive ? 2 : 1,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.05),
                            blurRadius: 10.r,
                            offset: Offset(0, 6.h),
                          ),
                        ],
                      ),
                      padding: EdgeInsets.all(8.w),
                      child: Image.asset(asset, fit: BoxFit.contain),
                    ),
                  );
                },
              ),
            ),
          ],
        );
      },
    );
  }
}

class _GroupTextField extends StatelessWidget {
  const _GroupTextField({
    required this.label,
    required this.controller,
    required this.hintText,
  });

  final String label;
  final TextEditingController controller;
  final String hintText;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 14.sp,
            fontWeight: FontWeight.w600,
            color: const Color(0xFF1A1D1F),
          ),
        ),
        SizedBox(height: 10.h),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(24.r),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.05),
                blurRadius: 12.r,
                offset: Offset(0, 6.h),
              ),
            ],
          ),
          child: TextFormField(
            controller: controller,
            decoration: InputDecoration(
              contentPadding: EdgeInsets.symmetric(
                horizontal: 18.w,
                vertical: 16.h,
              ),
              hintText: hintText,
              hintStyle: TextStyle(
                fontSize: 13.sp,
                color: const Color(0xFF8A97A6),
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(24.r),
                borderSide: BorderSide.none,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _ApprovalToggle extends StatelessWidget {
  const _ApprovalToggle({required this.controller});

  final CommunityCreateGroupController controller;

  @override
  Widget build(BuildContext context) {
    return Obx(
      () {
        final selected = controller.approvalMode.value;
        return Row(
          children: [
            Expanded(
              child: _ApprovalButton(
                label: 'Không duyệt',
                isActive: selected == StudyGroupApprovalMode.auto,
                activeColor: const Color(0xFF0A69C7),
                inactiveColor: const Color(0xFFD6E2F2),
                activeTextColor: Colors.white,
                inactiveTextColor: const Color(0xFF516579),
                onTap: () =>
                    controller.setApprovalMode(StudyGroupApprovalMode.auto),
              ),
            ),
            SizedBox(width: 12.w),
            Expanded(
              child: _ApprovalButton(
                label: 'Cần duyệt',
                isActive: selected == StudyGroupApprovalMode.require,
                activeColor: const Color(0xFF8E96A3),
                inactiveColor: const Color(0xFFE1E4EA),
                activeTextColor: Colors.white,
                inactiveTextColor: const Color(0xFF5E6470),
                onTap: () =>
                    controller.setApprovalMode(StudyGroupApprovalMode.require),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _ApprovalButton extends StatelessWidget {
  const _ApprovalButton({
    required this.label,
    required this.isActive,
    required this.onTap,
    required this.activeColor,
    required this.inactiveColor,
    required this.activeTextColor,
    required this.inactiveTextColor,
  });

  final String label;
  final bool isActive;
  final VoidCallback onTap;
  final Color activeColor;
  final Color inactiveColor;
  final Color activeTextColor;
  final Color inactiveTextColor;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        height: 46.h,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24.r),
          color: isActive ? activeColor : inactiveColor,
          boxShadow: isActive
              ? [
                  BoxShadow(
                    color: activeColor.withValues(alpha: 0.28),
                    blurRadius: 16.r,
                    offset: Offset(0, 10.h),
                  ),
                ]
              : [],
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            fontSize: 14.sp,
            fontWeight: FontWeight.w700,
            color: isActive ? activeTextColor : inactiveTextColor,
          ),
        ),
      ),
    );
  }
}
