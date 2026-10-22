import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/theme/app_widgets.dart';
import '../controllers/survey_controller.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class SurveyView extends GetView<SurveyController> {
  const SurveyView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: SafeArea(
        child: Column(
          children: [
            // Header with progress and back button
            _buildHeader(),

            // Content based on current step
            Expanded(
              child: Obx(() {
                switch (controller.currentStep) {
                  case 1:
                    return _buildStep1();
                  case 2:
                    return _buildLanguageStep();
                  case 3:
                    return _buildStep2();
                  case 4:
                    return _buildStep3();
                  case 5:
                    return _buildStep4();
                  default:
                    return _buildStep1();
                }
              }),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 16.h),
      child: Row(
        children: [
          // Back button
          Obx(() => controller.currentStep > 1
              ? GestureDetector(
                  onTap: controller.previousStep,
                  child: Icon(
                    Icons.arrow_back_ios,
                    size: 24.sp,
                    color: AppColors.textPrimary,
                  ),
                )
              : SizedBox(width: 24.w)),

          SizedBox(width: 16.w),

          // Progress bar
          Expanded(
            child: Obx(() => _buildProgressBar()),
          ),

          SizedBox(width: 40.w), // Space for symmetry
        ],
      ),
    );
  }

  Widget _buildProgressBar() {
    return Row(
      children: List.generate(5, (index) {
        final stepNumber = index + 1;
        final isActive = stepNumber == controller.currentStep;
        final isCompleted = stepNumber < controller.currentStep;

        return Expanded(
          child: Container(
            height: 4.h,
            margin: EdgeInsets.symmetric(horizontal: 2.w),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(2.r),
              color: isActive || isCompleted
                  ? AppColors.buttonActive
                  : AppColors.progressLocked,
            ),
          ),
        );
      }),
    );
  }

  Widget _buildStep1() {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 24.w),
      child: Column(
        children: [
          SizedBox(height: 20.h),

          // Form container with Prismo and bubble inside
          Expanded(
            child: Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: AppColors.backgroundWhite,
                borderRadius: BorderRadius.circular(20.r),
              ),
              child: SingleChildScrollView(
                padding: EdgeInsets.all(24.w),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                  SizedBox(height: 20.h),

                  // Prismo and chat bubble in a row
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Prismo (mascot)
                      _buildMascot(fallbackIcon: Icons.person),


                      // Chat bubble
                      Expanded(
                        child: Container(
                          padding: EdgeInsets.all(16.w),
                          decoration: BoxDecoration(
                            color: AppColors.buttonActive,
                            borderRadius: BorderRadius.circular(20.r),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Đăng ký thành công!',
                                style: AppTextStyles.bodyMedium.copyWith(
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.textWhite,
                                ),
                              ),
                              SizedBox(height: 4.h),
                              Text(
                                'Trả lời nhanh để cá nhân hóa trải nghiệm học tập.',
                                style: AppTextStyles.captionMedium.copyWith(
                                  color: AppColors.textWhite,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),

                  SizedBox(height: 32.h),

                  // Form content
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                        Text(
                          'Chúng tôi có thể gọi bạn là gì?',
                          style: AppTextStyles.h4,
                        ),

                        SizedBox(height: 16.h),

                        // Name input
                        Container(
                          decoration: BoxDecoration(
                            color: AppColors.surfaceLight,
                            borderRadius: BorderRadius.circular(12.r),
                          ),
                          child: TextField(
                            controller: controller.nameController,
                            decoration: InputDecoration(
                              hintText: 'Tên của bạn',
                              hintStyle: AppTextStyles.hintText,
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(12.r),
                                borderSide: BorderSide.none,
                              ),
                              contentPadding: EdgeInsets.symmetric(
                                horizontal: 16.w,
                                vertical: 16.h,
                              ),
                            ),
                          ),
                        ),

                        SizedBox(height: 24.h),

                        Text(
                          'Ngày sinh của bạn:',
                          style: AppTextStyles.bodyMedium,
                        ),

                        SizedBox(height: 16.h),

                        // Birth date input (lunar calendar style)
                        Obx(() => _buildDatePicker()),

                        SizedBox(height: 24.h),

                        Text(
                          'Giới tính:',
                          style: AppTextStyles.bodyMedium,
                        ),

                        SizedBox(height: 16.h),

                        // Gender selection
                        Row(
                          children: [
                            Expanded(
                              child: Obx(() => _buildGenderButton('Nam', 'Nam')),
                            ),
                            SizedBox(width: 16.w),
                            Expanded(
                              child: Obx(() => _buildGenderButton('Nữ', 'Nữ')),
                            ),
                          ],
                        ),

                        SizedBox(height: 32.h),

                        // Continue button
                        Obx(() => AppWidgets.primaryButton(
                              text: 'Tiếp tục',
                              onPressed: controller.nextStep,
                              enabled: controller.canContinueStep1(),
                            )),
                      ],
                    ),
                ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLanguageStep() {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 24.w),
      child: Column(
        children: [
          SizedBox(height: 20.h),
          Expanded(
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.all(24.w),
              decoration: BoxDecoration(color: AppColors.backgroundWhite, borderRadius: BorderRadius.circular(20.r)),
              child: Column(
                children: [
                  Row(
                    children: [
                      _buildMascot(fallbackIcon: Icons.translate),
                      Expanded(
                        child: Container(
                          padding: EdgeInsets.all(16.w),
                          decoration: BoxDecoration(color: AppColors.buttonActive, borderRadius: BorderRadius.circular(20.r)),
                          child: Text('Bạn muốn học ngôn ngữ nào?',
                              style: AppTextStyles.bodyMedium.copyWith(color: AppColors.textWhite)),
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 24.h),
                  Expanded(
                    child: ListView(
                      children: [
                        for (final o in controller.languageOptions)
                          Obx(() => _buildOptionItem(
                                '${o.$2}\n${o.$3}',
                                controller.language == o.$1,
                                () => controller.setLanguage(o.$1),
                              )),
                        SizedBox(height: 12.h),
                        Text('Người học là:', style: AppTextStyles.bodyMedium),
                        SizedBox(height: 8.h),
                        Obx(() => Row(
                              children: [
                                Expanded(child: _buildOptionItem('Người lớn', controller.learnerType == 'adult', () => controller.setLearnerType('adult'))),
                                SizedBox(width: 12.w),
                                Expanded(child: _buildOptionItem('Trẻ em', controller.learnerType == 'kid', () => controller.setLearnerType('kid'))),
                              ],
                            )),
                      ],
                    ),
                  ),
                  SizedBox(height: 16.h),
                  Obx(() => AppWidgets.primaryButton(
                        text: 'Tiếp tục',
                        onPressed: controller.nextStep,
                        enabled: controller.canContinueLanguage(),
                      )),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep2() {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 24.w),
      child: Column(
        children: [
          SizedBox(height: 20.h),

          // Form container with Prismo and bubble inside
          Expanded(
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.all(24.w),
              decoration: BoxDecoration(
                color: AppColors.backgroundWhite,
                borderRadius: BorderRadius.circular(20.r),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  SizedBox(height: 20.h),

                  // Prismo and chat bubble in a row
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Prismo (mascot)
                      _buildMascot(fallbackIcon: Icons.school),


                      // Chat bubble
                      Expanded(
                        child: Container(
                          padding: EdgeInsets.all(16.w),
                          decoration: BoxDecoration(
                            color: AppColors.buttonActive,
                            borderRadius: BorderRadius.circular(20.r),
                          ),
                          child: Text(
                            'Bạn học ngoại ngữ để phục vụ cho điều gì?',
                            style: AppTextStyles.bodyMedium.copyWith(
                              color: AppColors.textWhite,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),

                  SizedBox(height: 32.h),

                  // Options
                  Expanded(
                    child: ListView.builder(
                      itemCount: controller.purposeOptions.length,
                      itemBuilder: (context, index) {
                        final option = controller.purposeOptions[index];
                        return Obx(() => _buildOptionItem(
                          option,
                          controller.purpose == option,
                          () => controller.setPurpose(option),
                        ));
                      },
                    ),
                  ),

                  SizedBox(height: 24.h),

                  // Continue button
                  Obx(() => AppWidgets.primaryButton(
                        text: 'Tiếp tục',
                        onPressed: controller.nextStep,
                        enabled: controller.canContinueStep2(),
                      )),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep3() {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 24.w),
      child: Column(
        children: [
          SizedBox(height: 20.h),

          // Form container with Prismo and bubble inside
          Expanded(
            child: Container(
              width: double.infinity,
              padding: EdgeInsets.all(24.w),
              decoration: BoxDecoration(
                color: AppColors.backgroundWhite,
                borderRadius: BorderRadius.circular(20.r),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  SizedBox(height: 20.h),

                  // Prismo and chat bubble in a row
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      // Prismo (mascot)
                      _buildMascot(fallbackIcon: Icons.schedule),

                      SizedBox(width: 16.w),

                      // Chat bubble
                      Expanded(
                        child: Container(
                          padding: EdgeInsets.all(16.w),
                          decoration: BoxDecoration(
                            color: AppColors.buttonActive,
                            borderRadius: BorderRadius.circular(20.r),
                          ),
                          child: Text(
                            'Thời gian học tập hàng\nngày của bạn là:',
                            style: AppTextStyles.bodyMedium.copyWith(
                              color: AppColors.textWhite,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),

                  SizedBox(height: 32.h),

                  // Options
                  Expanded(
                    child: ListView.builder(
                      itemCount: controller.studyTimeOptions.length,
                      itemBuilder: (context, index) {
                        final option = controller.studyTimeOptions[index];
                        return Obx(() => _buildOptionItem(
                          option,
                          controller.studyTime == option,
                          () => controller.setStudyTime(option),
                        ));
                      },
                    ),
                  ),

                  SizedBox(height: 24.h),

                  // Continue button
                  Obx(() => AppWidgets.primaryButton(
                        text: 'Tiếp tục',
                        onPressed: controller.nextStep,
                        enabled: controller.canContinueStep3(),
                      )),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep4() {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 24.w),
      child: Column(
        children: [
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Large title
                Text(
                  'Học thôi nào!',
                  style: TextStyle(
                    fontSize: 48.sp,
                    fontWeight: FontWeight.bold,
                    color: AppColors.buttonActive,
                  ),
                ),

                SizedBox(height: 40.h),

                // Happy Prismo
                SizedBox(
                  width: 200.w,
                  height: 200.h,
                  child: Image.asset(
                    'assets/brand/mascot/prismo_love.png',
                    fit: BoxFit.contain,
                    errorBuilder: (context, error, stackTrace) {
                      return Container(
                        decoration: const BoxDecoration(
                          color: AppColors.xpGold,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.star,
                          size: 100.sp,
                          color: AppColors.textWhite,
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),

          // Start button at bottom
          AppWidgets.primaryButton(
            text: 'Bắt đầu',
            onPressed: controller.completeSurvey,
          ),

          SizedBox(height: 24.h),
        ],
      ),
    );
  }

  Widget _buildDatePicker() {
    final hasDate = controller.birthDay.isNotEmpty &&
                   controller.birthMonth.isNotEmpty &&
                   controller.birthYear.isNotEmpty;

    final displayText = hasDate
        ? '${controller.birthDay}/${controller.birthMonth}/${controller.birthYear}'
        : 'Ngày sinh';

    return GestureDetector(
      onTap: () => _selectBirthDate(),
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 16.h),
        decoration: BoxDecoration(
          color: AppColors.surfaceLight,
          borderRadius: BorderRadius.circular(12.r),
        ),
        child: Row(
          children: [
            Icon(
              Icons.calendar_today_outlined,
              color: AppColors.textSecondary,
              size: 20.sp,
            ),
            SizedBox(width: 12.w),
            Expanded(
              child: Text(
                displayText,
                style: AppTextStyles.bodyMedium.copyWith(
                  color: hasDate
                      ? AppColors.textPrimary
                      : AppColors.textSecondary,
                ),
              ),
            ),
            Icon(
              Icons.keyboard_arrow_down,
              color: AppColors.textSecondary,
              size: 20.sp,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _selectBirthDate() async {
    showModalBottomSheet(
      context: Get.context!,
      backgroundColor: Colors.transparent,
      builder: (context) => _buildCustomDatePicker(),
    );
  }

  Widget _buildCustomDatePicker() {
    int selectedDay = controller.birthDay.isNotEmpty ? int.parse(controller.birthDay) : 1;
    int selectedMonth = controller.birthMonth.isNotEmpty ? int.parse(controller.birthMonth) : 1;
    int selectedYear = controller.birthYear.isNotEmpty ? int.parse(controller.birthYear) : 1990;

    return Container(
      height: 400.h,
      decoration: BoxDecoration(
        color: AppColors.primaryTint,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20.r)),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: EdgeInsets.all(20.w),
            child: Text(
              'Chọn ngày sinh',
              style: AppTextStyles.h4.copyWith(
                color: AppColors.textPrimary,
              ),
            ),
          ),

          // Date pickers
          Expanded(
            child: Row(
              children: [
                // Day picker
                Expanded(
                  child: Column(
                    children: [
                      Text(
                        'Ngày',
                        style: AppTextStyles.bodyMedium.copyWith(
                          color: AppColors.textPrimary.withOpacity(0.7),
                        ),
                      ),
                      SizedBox(height: 8.h),
                      Expanded(
                        child: CupertinoPicker(
                          scrollController: FixedExtentScrollController(
                            initialItem: selectedDay - 1,
                          ),
                          itemExtent: 50.h,
                          onSelectedItemChanged: (index) {
                            selectedDay = index + 1;
                          },
                          children: List.generate(31, (index) {
                            final day = index + 1;
                            return Center(
                              child: Container(
                                padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
                                decoration: BoxDecoration(
                                  color: Colors.transparent,
                                  borderRadius: BorderRadius.circular(12.r),
                                ),
                                child: Text(
                                  day.toString(),
                                  style: AppTextStyles.bodyLarge.copyWith(
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                              ),
                            );
                          }),
                        ),
                      ),
                    ],
                  ),
                ),

                // Month picker
                Expanded(
                  child: Column(
                    children: [
                      Text(
                        'Tháng',
                        style: AppTextStyles.bodyMedium.copyWith(
                          color: AppColors.textPrimary.withOpacity(0.7),
                        ),
                      ),
                      SizedBox(height: 8.h),
                      Expanded(
                        child: CupertinoPicker(
                          scrollController: FixedExtentScrollController(
                            initialItem: selectedMonth - 1,
                          ),
                          itemExtent: 50.h,
                          onSelectedItemChanged: (index) {
                            selectedMonth = index + 1;
                          },
                          children: List.generate(12, (index) {
                            final month = index + 1;
                            return Center(
                              child: Container(
                                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 8.h),
                                decoration: BoxDecoration(
                                  color: Colors.transparent,
                                  borderRadius: BorderRadius.circular(12.r),
                                ),
                                child: Text(
                                  'Tháng $month',
                                  style: AppTextStyles.bodyLarge.copyWith(
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                              ),
                            );
                          }),
                        ),
                      ),
                    ],
                  ),
                ),

                // Year picker
                Expanded(
                  child: Column(
                    children: [
                      Text(
                        'Năm',
                        style: AppTextStyles.bodyMedium.copyWith(
                          color: AppColors.textPrimary.withOpacity(0.7),
                        ),
                      ),
                      SizedBox(height: 8.h),
                      Expanded(
                        child: CupertinoPicker(
                          scrollController: FixedExtentScrollController(
                            initialItem: selectedYear - (DateTime.now().year - 79),
                          ),
                          itemExtent: 50.h,
                          onSelectedItemChanged: (index) {
                            selectedYear = (DateTime.now().year - 79) + index;
                          },
                          children: List.generate(80, (index) {
                            final year = (DateTime.now().year - 79) + index;
                            return Center(
                              child: Container(
                                padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 8.h),
                                decoration: BoxDecoration(
                                  color: Colors.transparent,
                                  borderRadius: BorderRadius.circular(12.r),
                                ),
                                child: Text(
                                  year.toString(),
                                  style: AppTextStyles.bodyLarge.copyWith(
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                              ),
                            );
                          }),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Buttons
          Container(
            padding: EdgeInsets.all(20.w),
            child: Row(
              children: [
                // Cancel button
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => goBack(),
                    style: OutlinedButton.styleFrom(
                      backgroundColor: AppColors.buttonDisabled,
                      side: BorderSide(color: AppColors.textWhite.withOpacity(0.3)),
                      padding: EdgeInsets.symmetric(vertical: 16.h),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12.r),
                      ),
                    ),
                    child: Text(
                      'Hủy',
                      style: AppTextStyles.buttonMedium.copyWith(
                        color: AppColors.textWhite,
                      ),
                    ),
                  ),
                ),

                SizedBox(width: 16.w),

                // Confirm button
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      controller.setBirthDay(selectedDay.toString().padLeft(2, '0'));
                      controller.setBirthMonth(selectedMonth.toString().padLeft(2, '0'));
                      controller.setBirthYear(selectedYear.toString());
                      goBack();
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.buttonActive,
                      padding: EdgeInsets.symmetric(vertical: 16.h),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12.r),
                      ),
                    ),
                    child: Text(
                      'Chọn',
                      style: AppTextStyles.buttonMedium,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGenderButton(String text, String value) {
    final isSelected = controller.gender == value;
    return GestureDetector(
      onTap: () => controller.setGender(value),
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 16.h),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primaryTint : AppColors.background,
          borderRadius: BorderRadius.circular(25.r),
          border: isSelected ? Border.all(
            color: AppColors.primaryBlue,
            width: 2,
          ) : null,
        ),
        child: Text(
          text,
          style: AppTextStyles.bodyMedium.copyWith(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.w500,
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }

  Widget _buildOptionItem(String text, bool isSelected, VoidCallback onTap) {
    return Container(
      margin: EdgeInsets.only(bottom: 12.h),
      alignment: Alignment.center,
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          width: 280.w,
          padding: EdgeInsets.symmetric(vertical: 16.h, horizontal: 16.w),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.buttonActive.withOpacity(0.1) : AppColors.backgroundWhite,
            borderRadius: BorderRadius.circular(50.r),
            border: Border.all(
              color: isSelected ? AppColors.buttonActive : AppColors.progressLocked,
              width: 1.5,
            ),
          ),
          child: Text(
            text,
            textAlign: TextAlign.center,
            style: AppTextStyles.bodyMedium.copyWith(
              color: isSelected ? AppColors.buttonActive : AppColors.textPrimary,
              fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMascot({IconData fallbackIcon = Icons.person}) {
    return SizedBox(
      width: 60.w,
      height: 60.h,
      child: Image.asset(
        'assets/brand/mascot/prismo_hello.png',
        fit: BoxFit.contain,
        errorBuilder: (context, error, stackTrace) {
          return Container(
            decoration: BoxDecoration(
              color: AppColors.buttonActive,
              shape: BoxShape.circle,
            ),
            child: Icon(
              fallbackIcon,
              size: 30.sp,
              color: AppColors.textWhite,
            ),
          );
        },
      ),
    );
  }
}