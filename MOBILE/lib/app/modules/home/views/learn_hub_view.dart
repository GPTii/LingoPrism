import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/app_icon.dart';
import '../../../core/widgets/quest_strip.dart';
import '../../../data/services/auth_service.dart';
import '../../../routes/app_pages.dart';
import '../../learning_session/controllers/learning_session_controller.dart';
import '../../review/controllers/review_controller.dart';
import '../controllers/learning_tab_controller.dart';

/// Tab "Học": every way to study in one place, most used first – today's new words and the review, then the
/// practice tools, then exploring. (Home keeps today's goal; the camera is the raised button; "Tôi" holds the
/// learner's own corner: achievements, shop, friends, messages, community.)
class LearnHubView extends StatelessWidget {
  const LearnHubView({super.key});

  Future<void> _review() async {
    final c = Get.isRegistered<ReviewController>() ? Get.find<ReviewController>() : Get.put(ReviewController());
    await c.startReviewSession();
  }

  @override
  Widget build(BuildContext context) {
    final progress = Get.isRegistered<LearningTabController>() ? Get.find<LearningTabController>() : Get.put(LearningTabController());
    final vi = AuthService.to.currentUser?.activeLanguage == 'vi';
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Học'),
        centerTitle: false,
        automaticallyImplyLeading: false,
        backgroundColor: AppColors.background,
        surfaceTintColor: Colors.transparent,
      ),
      body: ListView(
        padding: EdgeInsets.fromLTRB(16.w, 4.h, 16.w, 120.h),
        children: [
          const QuestStrip(),
          SizedBox(height: 14.h),
          Row(children: [
            Expanded(
              child: _BigAction(
                icon: 'sparkle',
                title: 'Học từ mới',
                subtitle: '10 từ một lượt',
                filled: true,
                onTap: () => Get.toNamed(Routes.learningSession, arguments: const LearningSessionArguments(kind: 'learn', size: 10)),
              ),
            ),
            SizedBox(width: 10.w),
            Expanded(
              child: Obx(() {
                final due = progress.dueNow.value;
                return _BigAction(
                  icon: 'review',
                  title: 'Ôn tập',
                  subtitle: due > 0 ? '$due từ đến hạn' : 'Không có từ đến hạn',
                  badge: due,
                  onTap: _review,
                );
              }),
            ),
          ]),
          _Section('Luyện tập', [
            const _Tile('mic', 'Luyện phát âm', Routes.speakPractice),
            vi ? const _Tile('pencil', 'Học đọc – viết', Routes.literacyMap) : const _Tile('tiles', 'Luyện câu', Routes.sentencePractice),
            const _Tile('game', 'Trò chơi', Routes.games),
            const _Tile('exam', 'Bài kiểm tra', Routes.examList),
          ]),
          const _Section('Khám phá', [
            _Tile('photo', 'Lịch sử ảnh', Routes.photoHistory),
            _Tile('pin', 'Học theo vị trí', Routes.poiMap),
            _Tile('camera', 'Camera trực tiếp', Routes.liveCamera),
            _Tile('chat', 'Dịch', Routes.translate),
          ]),
        ],
      ),
    );
  }
}

class _BigAction extends StatelessWidget {
  const _BigAction(
      {required this.icon, required this.title, required this.subtitle, required this.onTap, this.filled = false, this.badge = 0});
  final String icon, title, subtitle;
  final VoidCallback onTap;
  final bool filled;
  final int badge;

  @override
  Widget build(BuildContext context) {
    final fg = filled ? Colors.white : AppColors.textPrimary;
    return Material(
      color: filled ? AppColors.primary : AppColors.surface,
      borderRadius: BorderRadius.circular(18.r),
      child: InkWell(
        borderRadius: BorderRadius.circular(18.r),
        onTap: onTap,
        child: Container(
          padding: EdgeInsets.all(14.w),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18.r),
            border: filled ? null : Border.all(color: AppColors.line),
          ),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              AppIcon(icon, size: 34.sp),
              const Spacer(),
              if (badge > 0)
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 2.h),
                  decoration: BoxDecoration(color: AppColors.beamCoral, borderRadius: BorderRadius.circular(10.r)),
                  child: Text(badge > 99 ? '99+' : '$badge',
                      style: TextStyle(color: Colors.white, fontSize: 11.sp, fontWeight: FontWeight.w800)),
                ),
            ]),
            SizedBox(height: 10.h),
            Text(title, style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w800, color: fg)),
            Text(subtitle, style: TextStyle(fontSize: 12.sp, color: filled ? Colors.white70 : AppColors.textSecondary)),
          ]),
        ),
      ),
    );
  }
}

class _Tile {
  const _Tile(this.icon, this.label, this.route);
  final String icon, label, route;
}

class _Section extends StatelessWidget {
  const _Section(this.title, this.tiles);
  final String title;
  final List<_Tile> tiles;

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.only(top: 20.h),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
          SizedBox(height: 10.h),
          GridView.count(
            crossAxisCount: 4,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 8.h,
            crossAxisSpacing: 8.w,
            childAspectRatio: 0.82,
            children: [
              for (final t in tiles)
                Material(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(14.r),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(14.r),
                    onTap: () => Get.toNamed(t.route),
                    child: Container(
                      decoration: BoxDecoration(borderRadius: BorderRadius.circular(14.r), border: Border.all(color: AppColors.line)),
                      padding: EdgeInsets.symmetric(horizontal: 4.w, vertical: 8.h),
                      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                        AppIcon(t.icon, size: 32.sp),
                        SizedBox(height: 6.h),
                        Text(t.label,
                            textAlign: TextAlign.center,
                            maxLines: 2,
                            style: TextStyle(fontSize: 11.5.sp, fontWeight: FontWeight.w600, color: AppColors.textPrimary, height: 1.2)),
                      ]),
                    ),
                  ),
                ),
            ],
          ),
        ]),
      );
}
