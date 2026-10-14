import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../controllers/streak_controller.dart';
import '../../../core/theme/app_widgets.dart';
import '../../../core/utils/streak_asset_resolver.dart';

class StreakView extends GetView<StreakController> {
  const StreakView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAFBFF),
      appBar: AppBar(
        backgroundColor: const Color(0xFFEAFBFF),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              color: Color(0xFF1B2B40)),
          onPressed: () => Get.back(),
        ),
        title: Text(
          'Streak',
          style: TextStyle(
            color: const Color(0xFF1B2B40),
            fontSize: 24.sp,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
      body: Obx(() {
        if (controller.isLoading.value) {
          return const Center(child: CircularProgressIndicator());
        }

        if (controller.errorMessage.value.isNotEmpty) {
          return Center(
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: 24.w),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    controller.errorMessage.value,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 16.sp,
                      color: const Color(0xFF1B2B40),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  SizedBox(height: 12.h),
                  ElevatedButton(
                    onPressed: controller.refreshStreakData,
                    child: const Text('Thử lại'),
                  ),
                ],
              ),
            ),
          );
        }

        return SingleChildScrollView(
          child: Padding(
            padding: EdgeInsets.all(20.w),
            child: Column(
              children: [
                _buildStreakHeader(),
                SizedBox(height: 16.h),

                _buildMonthNavigation(),
                SizedBox(height: 12.h),

                _buildStatisticsCards(),
                SizedBox(height: 12.h),

                _buildCalendar(),
              ],
            ),
          ),
        );
      }),
    );
  }

  Widget _buildStreakHeader() {
    return Obx(() {
      final asset = StreakAssetResolver.assetFor(
        streak: controller.currentStreak.value,
        hasActivityToday: controller.todayHasActivity.value,
      );
      return Container(
        width: double.infinity,
        padding: EdgeInsets.symmetric(vertical: 24.h, horizontal: 18.w),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFFFFF4E8), Color(0xFFE5F5FF)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(28.r),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.08),
              blurRadius: 18.r,
              offset: Offset(0, 12.h),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
              height: 100.h,
              padding: EdgeInsets.all(6.w),
              child: Image.asset(asset),
            ),
            SizedBox(width: 18.w),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Chuỗi hiện tại',
                    style: TextStyle(
                      fontSize: 16.sp,
                      color: const Color(0xFF60718C),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  SizedBox(height: 6.h),
                  Text(
                    '${controller.currentStreak.value}',
                    style: TextStyle(
                      fontSize: 56.sp,
                      fontWeight: FontWeight.w800,
                      color: const Color(0xFF3037B3),
                      height: 1.0,
                    ),
                  ),
                  Text(
                    'ngày streak liên tiếp',
                    style: TextStyle(
                      fontSize: 18.sp,
                      fontWeight: FontWeight.w600,
                      color: const Color(0xFF3037B3),
                    ),
                  ),
                ],
              ),
            )
          ],
        ),
      );
    });
  }

  Widget _buildMonthNavigation() {
    return Obx(() {
      final date = controller.currentMonth.value;
      final monthYear = _formatMonthYear(date);
      return Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            monthYear,
            style: TextStyle(
              fontSize: 24.sp,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          Row(
            children: [
              IconButton(
                onPressed: controller.previousMonth,
                icon: const Icon(Icons.chevron_left),
                color: Colors.black54,
              ),
              IconButton(
                onPressed: controller.nextMonth,
                icon: const Icon(Icons.chevron_right),
                color: Colors.black54,
              ),
            ],
          ),
        ],
      );
    });
  }

  Widget _buildStatisticsCards() {
    return Obx(() => Row(
          children: [
            Expanded(
              child: _buildStatCard(
                StreakAssetResolver.assetFor(
                  streak: controller.currentStreak.value,
                  hasActivityToday: controller.todayHasActivity.value,
                ),
                controller.studyDaysInMonth.value.toString(),
                'ngày học',
                const Color(0xFF1CB0F6),
              ),
            ),
            SizedBox(width: 12.w),
            Expanded(
              child: _buildStatCard(
                'assets/images/streak/streakbang.png',
                controller.freezeItemsUsed.value.toString(),
                'số đá băng\nđã dùng',
                const Color(0xFF1CB0F6),
                imageSize: 65.w,
              ),
            ),
          ],
        ));
  }

  Widget _buildStatCard(
    String iconPath,
    String number,
    String label,
    Color borderColor, {
    double? imageSize,
  }) {
    return Container(
      padding: EdgeInsets.all(6.w),
      decoration: AppWidgets.questGradientDecoration(),
      child: Row(
        children: [
          Image.asset(
            iconPath,
            width: imageSize ?? 85.w,
            height: imageSize ?? 85.h,
            errorBuilder: (context, error, stackTrace) {
              return Icon(Icons.local_fire_department, size: 50.sp);
            },
          ),
          SizedBox(width: 6.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  number,
                  style: TextStyle(
                    fontSize: 32.sp,
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFF4840B2),
                  ),
                ),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 12.sp,
                    color: const Color(0xFF4840B2),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCalendar() {
    return Obx(() {
      final month = controller.currentMonth.value;
      return Container(
        padding: EdgeInsets.all(16.w),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20.r),
        ),
        child: Column(
          children: [
            // Weekday headers
            _buildWeekdayHeaders(),
            SizedBox(height: 12.h),
            // Calendar days
            _buildCalendarDays(month),
          ],
        ),
      );
    });
  }

  Widget _buildWeekdayHeaders() {
    const weekdays = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: weekdays.map((day) {
        return Expanded(
          child: Center(
            child: Text(
              day,
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w600,
                color: Colors.black54,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildCalendarDays(DateTime month) {
    final firstDayOfMonth = DateTime(month.year, month.month, 1);
    final lastDayOfMonth = DateTime(month.year, month.month + 1, 0);
    final daysInMonth = lastDayOfMonth.day;
    final startWeekday = firstDayOfMonth.weekday % 7; // Convert to 0-6 (Sun-Sat)

    final days = <Widget>[];

    // Add empty cells for days before month starts
    for (int i = 0; i < startWeekday; i++) {
      days.add(const SizedBox());
    }

    // Add days of month
    for (int day = 1; day <= daysInMonth; day++) {
      final date = DateTime(month.year, month.month, day);
      days.add(_buildDayCell(date, day));
    }

    // Arrange in rows of 7
    final rows = <Widget>[];
    for (int i = 0; i < days.length; i += 7) {
      final rowChildren = days.sublist(
        i,
        i + 7 > days.length ? days.length : i + 7,
      );
      // Fill remaining cells in last row
      while (rowChildren.length < 7) {
        rowChildren.add(const SizedBox());
      }
      rows.add(
        Padding(
          padding: EdgeInsets.symmetric(vertical: 4.h),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: rowChildren.map((child) {
              return Expanded(child: child);
            }).toList(),
          ),
        ),
      );
    }

    return Column(children: rows);
  }

  Widget _buildDayCell(DateTime date, int day) {
    final isStudied = controller.isDayStudied(date);
    final isTodayDate = controller.isToday(date);

    Color backgroundColor;
    Color textColor;

    if (isStudied) {
      backgroundColor = const Color(0xFFFFA500); // Orange
      textColor = Colors.white;
    } else if (isTodayDate) {
      backgroundColor = const Color(0xFF5DDEF4); // Light blue (today)
      textColor = Colors.white;
    } else {
      backgroundColor = const Color(0xFFB8E6F0); // Very light blue
      textColor = const Color(0xFF5B4FFF);
    }

    return Center(
      child: Container(
        width: 40.w,
        height: 40.h,
        decoration: BoxDecoration(
          color: backgroundColor,
          shape: BoxShape.circle,
        ),
        child: Center(
          child: Text(
            '$day',
            style: TextStyle(
              fontSize: 16.sp,
              fontWeight: FontWeight.bold,
              color: textColor,
            ),
          ),
        ),
      ),
    );
  }

  String _formatMonthYear(DateTime date) {
    const months = [
      '', // Index 0 không dùng
      'tháng 1', 'tháng 2', 'tháng 3', 'tháng 4',
      'tháng 5', 'tháng 6', 'tháng 7', 'tháng 8',
      'tháng 9', 'tháng 10', 'tháng 11', 'tháng 12'
    ];
    return '${months[date.month]} năm ${date.year}';
  }
}
