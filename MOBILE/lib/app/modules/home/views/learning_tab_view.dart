import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../../../core/theme/app_colors.dart';
import '../../../routes/app_pages.dart';
import '../../camera_detection/controllers/camera_detection_controller.dart';
import '../../review/controllers/review_controller.dart';
import '../controllers/home_stats_controller.dart';
import '../../../core/utils/streak_asset_resolver.dart';
import '../../learning_session/controllers/learning_session_controller.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/models/api/game.dart';
import '../../../data/models/api/user.dart';
import '../controllers/learning_tab_controller.dart';
import '../../levels/levels_module.dart';
import '../../../core/widgets/prismo.dart';
import '../../../core/theme/theme_service.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/models/api/vocab.dart';
import '../../../core/widgets/target_word.dart';

const _monthNames = [
  'Một', 'Hai', 'Ba', 'Tư', 'Năm', 'Sáu', 'Bảy', 'Tám', 'Chín', 'Mười', 'Mười Một', 'Mười Hai',
];

/// Home tab, same structure as the web home page: "today" on the ink surface with the goal
/// drawn as light leaving Prismo, then the camera, the level path, shortcuts and quests.
class LearningTabView extends GetView<HomeStatsController> {
  const LearningTabView({super.key});

  @override
  Widget build(BuildContext context) {
    final devicePixelRatio = MediaQuery.of(context).devicePixelRatio;
    final progressController = Get.put(LearningTabController());

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Obx(() {
        final loading = controller.isLoading.value;
        final statsUser = controller.user.value;
        final streak = controller.streak.value;
        final unread = controller.unreadNotifications.value;
        if (loading) return const Center(child: CircularProgressIndicator());
        return AnnotatedRegion<SystemUiOverlayStyle>(
          value: SystemUiOverlayStyle.light,
          child: RefreshIndicator(
            color: AppColors.primary,
            onRefresh: progressController.refreshProgress,
            child: ListView(
              padding: EdgeInsets.zero,
              children: [
                // the prism: full-bleed ink that holds the header, the greeting and the day's light
                Obx(() => _buildTodayCard(
                      devicePixelRatio,
                      user: statsUser,
                      learned: progressController.newLearned.value,
                      target: progressController.newTarget.value,
                      due: progressController.dueNow.value,
                      header: _buildHeader(devicePixelRatio, user: statsUser, streak: streak, unreadNotifications: unread),
                    )),
                Padding(
                  padding: EdgeInsets.fromLTRB(16.w, 24.h, 16.w, 32.h),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                          const _TodayWord(),
                          SizedBox(height: 24.h),
                          _buildCameraCard(),
                          Align(
                            alignment: Alignment.centerRight,
                            child: TextButton.icon(
                              onPressed: () => Get.toNamed(Routes.liveCamera),
                              icon: const Icon(Icons.center_focus_strong_rounded, size: 18),
                              label: const Text('Camera trực tiếp (thử nghiệm)'),
                            ),
                          ),
                          SizedBox(height: 20.h),
                          const LevelPathCard(),
                          SizedBox(height: 12.h),
                          _buildQuickActions(),
                          SizedBox(height: 28.h),
                          _sectionTitle('Nhiệm vụ'),
                          SizedBox(height: 12.h),
                          Obx(() {
                            final monthly = progressController.monthlyQuest.value;
                            return _buildMonthlyQuest(
                              devicePixelRatio,
                              current: monthly?.completedCount ?? 0,
                              total: progressController.monthlyTarget,
                            );
                          }),
                          SizedBox(height: 12.h),
                          Obx(() => _buildDailyQuests(devicePixelRatio, progressController.dailyQuests)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      }),
    );
  }

  Widget _sectionTitle(String text) => Text(
        text,
        style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary, letterSpacing: -0.2),
      );

  /// Plain surface: a hairline, no shadow, no gradient.
  BoxDecoration _surface({double radius = 16}) => BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(radius.r),
        border: Border.fromBorderSide(BorderSide(color: AppColors.line)),
      );

  String _greeting() {
    final h = DateTime.now().hour;
    return h < 11 ? 'Chào buổi sáng' : h < 14 ? 'Chào buổi trưa' : h < 18 ? 'Chào buổi chiều' : 'Chào buổi tối';
  }

  // ---------------------------------------------------------------- today
  Widget _buildTodayCard(
    double devicePixelRatio, {
    required AppUser? user,
    required int learned,
    required int target,
    required int due,
    required Widget header,
  }) {
    final safeTarget = target <= 0 ? 10 : target;
    final done = learned >= safeTarget;
    final line = done
        ? 'Bạn đã đạt mục tiêu hôm nay. Ôn thêm vài từ để nhớ lâu hơn.'
        : learned > 0
            ? 'Còn ${safeTarget - learned} từ nữa là đạt mục tiêu hôm nay.'
            : due > 0
                ? '$due từ đến lịch ôn. Ôn trước, học từ mới sau.'
                : 'Năm phút là đủ cho một lượt học hôm nay.';
    final name = user?.displayName ?? '';

    return Container(
      decoration: BoxDecoration(
        color: AppColors.ink,
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(28.r)),
      ),
      padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 28.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SafeArea(bottom: false, child: Transform.translate(offset: Offset(-8.w, 0), child: header)),
          SizedBox(height: 12.h),
          if (user != null)
            Row(children: [
              _LangGlyph(user: user),
              SizedBox(width: 8.w),
              Text('Đang học ${user.languageLabel.toLowerCase()}',
                  style: TextStyle(color: Colors.white.withValues(alpha: 0.75), fontSize: 13.sp)),
            ]),
          SizedBox(height: 10.h),
          Text(
            name.isEmpty ? _greeting() : '${_greeting()},\n$name',
            style: TextStyle(color: Colors.white, fontSize: 34.sp, fontWeight: FontWeight.w800, height: 1.08, letterSpacing: -1.0),
          ),
          SizedBox(height: 10.h),
          Text(line, style: TextStyle(color: Colors.white.withValues(alpha: 0.72), fontSize: 15.sp, height: 1.4)),
          SizedBox(height: 18.h),
          // Prismo and the light it gives off: the day's goal
          Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Prismo(
                mood: done ? PrismoMood.celebrate : learned > 0 ? PrismoMood.happy : due > 0 ? PrismoMood.think : PrismoMood.wow,
                size: 78.w,
              ),
              Expanded(child: _GoalBeam(learned: learned, target: safeTarget)),
            ],
          ),
          SizedBox(height: 20.h),
          Row(children: [
            Expanded(
              flex: 3,
              child: _InkButton(
                label: 'Học ${math.min(10, math.max(1, safeTarget - learned))} từ mới',
                filled: true,
                onTap: _handleNewLearningTap,
              ),
            ),
            SizedBox(width: 10.w),
            Expanded(
              flex: 2,
              child: _InkButton(
                label: due > 0 ? 'Ôn $due từ' : 'Ôn tập',
                icon: Icons.replay_rounded,
                onTap: _handleReviewTap,
              ),
            ),
          ]),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------- camera
  Widget _buildCameraCard() {
    void open() {
      if (!Get.isRegistered<CameraDetectionController>()) {
        Get.lazyPut(() => CameraDetectionController());
      }
      CameraDetectionController.to.takePhoto();
    }

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: open,
        borderRadius: BorderRadius.circular(16.r),
        child: Ink(
          decoration: _surface(),
          padding: EdgeInsets.all(16.w),
          child: Row(children: [
            Container(
              width: 52.w,
              height: 52.w,
              decoration: BoxDecoration(color: AppColors.primary, borderRadius: BorderRadius.circular(14.r)),
              child: Icon(Icons.photo_camera_rounded, color: Colors.white, size: 26.sp),
            ),
            SizedBox(width: 14.w),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Chụp một đồ vật',
                    style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                SizedBox(height: 2.h),
                Text('Nhận ra vật trong ảnh, cho ngay từ Việt · Anh · Trung.',
                    style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary, height: 1.35)),
              ]),
            ),
            Icon(Icons.chevron_right_rounded, color: AppColors.textHint, size: 24.sp),
          ]),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------- shortcuts
  Widget _buildQuickActions() {
    Widget item(IconData icon, String label, String route) => Expanded(
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () => Get.toNamed(route),
              borderRadius: BorderRadius.circular(14.r),
              child: Ink(
                padding: EdgeInsets.symmetric(vertical: 14.h, horizontal: 4.w),
                decoration: _surface(radius: 14),
                child: Column(children: [
                  Icon(icon, size: 24.sp, color: AppColors.primary),
                  SizedBox(height: 6.h),
                  Text(label,
                      textAlign: TextAlign.center,
                      maxLines: 2,
                      style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w600, color: AppColors.textPrimary, height: 1.25)),
                ]),
              ),
            ),
          ),
        );
    final learningVietnamese = Get.find<AuthService>().currentUser?.activeLanguage == 'vi';
    return Column(children: [
      Row(children: [
        if (learningVietnamese)
          item(Icons.menu_book_rounded, 'Học đọc – viết', Routes.literacyMap)
        else
          item(Icons.edit_note_rounded, 'Luyện câu', Routes.sentencePractice),
        SizedBox(width: 8.w),
        item(Icons.record_voice_over_outlined, 'Luyện phát âm', Routes.speakPractice),
        SizedBox(width: 8.w),
        item(Icons.fact_check_outlined, 'Bài kiểm tra', Routes.examList),
      ]),
      SizedBox(height: 8.h),
      Row(children: [
        item(Icons.place_outlined, 'Học theo vị trí', Routes.poiMap),
        SizedBox(width: 8.w),
        item(Icons.forum_outlined, 'Hỏi giáo viên', Routes.supportChat),
        SizedBox(width: 8.w),
        item(Icons.insights_rounded, 'Thống kê', Routes.stats),
      ]),
    ]);
  }

  Future<void> _handleNewLearningTap() async {
    try {
      final auth = Get.find<AuthService>();
      if (!auth.isLoggedIn) {
        Get.snackbar(
          'Cần đăng nhập',
          'Bạn cần đăng nhập để bắt đầu học từ mới.',
          snackPosition: SnackPosition.BOTTOM,
        );
        return;
      }

      Get.log('LearningTab: Bắt đầu Học từ mới từ trang chủ');
      final progressCtrl = Get.find<LearningTabController>();
      final target = progressCtrl.newTarget.value > 0 ? progressCtrl.newTarget.value : 15;
      final learned = progressCtrl.newLearned.value;
      final remaining = math.max(0, target - learned);
      if (remaining <= 0) {
        await _showPostGoalDialog();
        return;
      }

      final takeCount = math.min(10, remaining);
      await _startNewLearningSession(takeCount);
    } catch (e, stack) {
      Get.log('LearningTab: Lỗi khi bắt đầu học từ mới - $e', isError: true);
      Get.log(stack.toString(), isError: true);
      Get.snackbar(
        'Không thể bắt đầu học',
        'Đã xảy ra lỗi: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }

  Future<void> _startNewLearningSession(int takeCount) async {
    Get.toNamed(Routes.learningSession, arguments: LearningSessionArguments(kind: 'learn', size: takeCount));
  }

  Future<void> _showPostGoalDialog() async {
    final selection = await Get.dialog<String>(
      Dialog(
        insetPadding: EdgeInsets.symmetric(horizontal: 20.w),
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24.r)),
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 24.h),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 60.w,
                height: 60.w,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.primary,
                ),
                child: const Icon(
                  Icons.celebration_outlined,
                  color: Colors.white,
                  size: 32,
                ),
              ),
              SizedBox(height: 16.h),
              Text(
                'Bạn đã đạt mục tiêu hôm nay!',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 20.sp,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              SizedBox(height: 10.h),
              Text(
                'Bạn muốn ôn tập ngay hay tiếp tục học thêm 10 từ mới?',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14.sp,
                  color: AppColors.textSecondary,
                ),
              ),
              SizedBox(height: 20.h),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Get.back(result: 'review'),
                      style: OutlinedButton.styleFrom(
                        padding: EdgeInsets.symmetric(vertical: 12.h),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14.r),
                        ),
                        side: BorderSide(color: AppColors.lineStrong, width: 1.5),
                        foregroundColor: AppColors.textPrimary,
                        textStyle: TextStyle(
                          fontWeight: FontWeight.w700,
                          fontSize: 14.sp,
                        ),
                      ),
                      child: const Text('Ôn tập ngay'),
                    ),
                  ),
                  SizedBox(width: 12.w),
                  Expanded(
                    child: FilledButton(
                      onPressed: () => Get.back(result: 'learn_more'),
                      style: FilledButton.styleFrom(
                        padding: EdgeInsets.symmetric(vertical: 12.h),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14.r)),
                        textStyle: TextStyle(fontWeight: FontWeight.w700, fontSize: 14.sp),
                      ),
                      child: const Text('Học thêm 10 từ'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
      barrierDismissible: true,
    );

    if (selection == 'learn_more') {
      await _startNewLearningSession(10);
    } else if (selection == 'review') {
      await _handleReviewTap();
    }
  }

  Future<void> _handleReviewTap() async {
    try {
      final reviewController = Get.isRegistered<ReviewController>()
          ? Get.find<ReviewController>()
          : Get.put(ReviewController());
      Get.log('LearningTab: Bắt đầu luồng Ôn tập ngay từ trang chủ');
      await reviewController.startReviewSession();
    } catch (e, stack) {
      Get.log('LearningTab: Lỗi khi bắt đầu ôn tập ngay - $e', isError: true);
      Get.log(stack.toString(), isError: true);
      Get.snackbar(
        'Không thể ôn tập ngay',
        'Đã xảy ra lỗi: $e',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }

  // ---------------------------------------------------------------- header
  Widget _buildHeader(
    double devicePixelRatio, {
    required AppUser? user,
    required int streak,
    required int unreadNotifications,
  }) {
    final scales = controller.scales.value;
    final gems = controller.gems.value;

    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
      child: Row(
        children: [
          _buildStatItem(StreakAssetResolver.assetByValue(streak), '$streak', 'Chuỗi ngày học', Routes.streak, devicePixelRatio),
          _buildStatItem('assets/brand/icons/scale.png', '$scales', 'Vảy', Routes.shop, devicePixelRatio),
          _buildStatItem('assets/brand/icons/gem.png', '$gems', 'Ngọc', Routes.shop, devicePixelRatio),
          const Spacer(),
          IconButton(
            tooltip: ThemeService.isDark ? 'Giao diện sáng' : 'Giao diện tối',
            onPressed: ThemeService.toggle,
            icon: Icon(ThemeService.isDark ? Icons.light_mode_outlined : Icons.dark_mode_outlined, size: 24.sp, color: Colors.white),
          ),
          Stack(
            clipBehavior: Clip.none,
            children: [
              IconButton(
                tooltip: 'Thông báo',
                onPressed: () => Get.toNamed(Routes.notification),
                icon: Icon(Icons.notifications_none_rounded, size: 26.sp, color: Colors.white),
              ),
              if (unreadNotifications > 0)
                Positioned(
                  right: 6,
                  top: 6,
                  child: Container(
                    padding: EdgeInsets.symmetric(horizontal: 5.w, vertical: 1.h),
                    decoration: BoxDecoration(color: AppColors.error, borderRadius: BorderRadius.circular(10.r)),
                    child: Text(
                      unreadNotifications > 99 ? '99+' : '$unreadNotifications',
                      style: TextStyle(color: Colors.white, fontSize: 10.sp, fontWeight: FontWeight.w700),
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(
    String imagePath,
    String value,
    String label,
    String route,
    double devicePixelRatio,
  ) {
    return Semantics(
      button: true,
      label: '$label: $value',
      child: InkWell(
        borderRadius: BorderRadius.circular(10.r),
        onTap: () async {
          try {
            await Get.toNamed(route);
          } catch (e) {
            Get.log('Navigate error: $e');
          }
        },
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 8.h),
          child: Row(
            children: [
              _buildOptimizedAsset(
                imagePath: imagePath,
                width: 24.w,
                height: 24.w,
                devicePixelRatio: devicePixelRatio,
                fit: BoxFit.contain,
                fallback: SizedBox(width: 24.w, height: 24.w),
              ),
              SizedBox(width: 5.w),
              Text(
                value,
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 15.sp,
                  color: Colors.white,
                  fontFeatures: const [FontFeature.tabularFigures()],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ---------------------------------------------------------------- quests
  Widget _buildQuestProgressBar({
    required int current,
    required int total,
    String? title,
    bool completed = false,
    String? actionLabel,
    VoidCallback? onTap,
  }) {
    final safeTotal = total <= 0 ? 1 : total;
    final safeCurrent = current.clamp(0, safeTotal);
    final content = Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (title != null) ...[
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w600,
                    color: completed ? AppColors.textHint : AppColors.textPrimary,
                    decoration: completed && actionLabel == null ? TextDecoration.lineThrough : null,
                  ),
                ),
                SizedBox(height: 8.h),
              ],
              ClipRRect(
                borderRadius: BorderRadius.circular(8.r),
                child: LinearProgressIndicator(
                  value: safeCurrent / safeTotal,
                  backgroundColor: AppColors.surfaceMuted,
                  valueColor: AlwaysStoppedAnimation(completed ? AppColors.beamMint : AppColors.primary),
                  minHeight: 8.h,
                ),
              ),
            ],
          ),
        ),
        SizedBox(width: 12.w),
        if (actionLabel != null)
          FilledButton(
            onPressed: onTap,
            style: FilledButton.styleFrom(
              minimumSize: Size(0, 36.h),
              padding: EdgeInsets.symmetric(horizontal: 14.w),
              textStyle: TextStyle(fontSize: 13.sp, fontWeight: FontWeight.w700),
            ),
            child: Text(actionLabel),
          )
        else
          Text(
            '$safeCurrent/$safeTotal',
            style: TextStyle(
              fontSize: 13.sp,
              fontWeight: FontWeight.w600,
              color: AppColors.textSecondary,
              fontFeatures: const [FontFeature.tabularFigures()],
            ),
          ),
      ],
    );
    return content;
  }

  Widget _buildMonthlyQuest(
    double devicePixelRatio, {
    required int current,
    required int total,
  }) {
    return Container(
      decoration: _surface(),
      padding: EdgeInsets.all(16.w),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Nhiệm vụ tháng ${_monthNames[DateTime.now().month - 1]}',
                  style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                ),
                SizedBox(height: 2.h),
                Text('Hoàn thành nhiệm vụ ngày để nhận ngọc cuối tháng.',
                    style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
                SizedBox(height: 12.h),
                _buildQuestProgressBar(current: current, total: total, completed: current >= total),
              ],
            ),
          ),
          SizedBox(width: 8.w),
          _buildOptimizedAsset(
            imagePath: 'assets/brand/mascot/prismo_explore.png',
            width: 72.w,
            height: 72.w,
            devicePixelRatio: devicePixelRatio,
            fit: BoxFit.contain,
          ),
        ],
      ),
    );
  }

  Widget _buildDailyQuests(
    double devicePixelRatio,
    List<DailyQuest> quests,
  ) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: _surface(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Nhiệm vụ hôm nay',
            style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
          ),
          SizedBox(height: 14.h),
          if (quests.isEmpty)
            Text('Hôm nay chưa có nhiệm vụ. Học một bài để mở nhiệm vụ mới.',
                style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary))
          else
            ...List.generate(quests.length, (index) {
              final quest = quests[index];
              final canClaim = quest.completed && !quest.rewardClaimed;
              return Padding(
                padding: EdgeInsets.only(bottom: index == quests.length - 1 ? 0 : 16.h),
                child: _buildQuestProgressBar(
                  current: quest.progress,
                  total: quest.target,
                  title: quest.title,
                  completed: quest.completed,
                  actionLabel: canClaim ? 'Nhận ${quest.rewardScales} vảy' : null,
                  onTap: canClaim ? () => Get.find<LearningTabController>().claim(quest) : null,
                ),
              );
            }),
        ],
      ),
    );
  }

  Widget _buildOptimizedAsset({
    required String imagePath,
    required double width,
    required double height,
    required double devicePixelRatio,
    Widget? fallback,
    BoxFit fit = BoxFit.cover,
  }) {
    final safeRatio = devicePixelRatio <= 0 ? 1.0 : devicePixelRatio;
    final targetWidthPx = (width * safeRatio).clamp(1, double.maxFinite).round();
    final targetHeightPx = (height * safeRatio).clamp(1, double.maxFinite).round();
    const maxDimensionPx = 512;

    final cacheWidth = targetWidthPx > maxDimensionPx
        ? maxDimensionPx
        : targetWidthPx;
    final cacheHeight = targetHeightPx > maxDimensionPx
        ? (targetHeightPx * (cacheWidth / targetWidthPx)).round()
        : targetHeightPx;

    return Image.asset(
      imagePath,
      width: width,
      height: height,
      fit: fit,
      cacheWidth: cacheWidth,
      cacheHeight: cacheHeight,
      filterQuality: FilterQuality.medium,
      errorBuilder: (context, error, stackTrace) => fallback ?? const SizedBox.shrink(),
    );
  }
}

/// The day's goal as light leaving Prismo: the three beams (one per language) grow with the
/// words learned today and reach the end when the goal is met.
class _GoalBeam extends StatelessWidget {
  const _GoalBeam({required this.learned, required this.target});

  final int learned;
  final int target;

  static const _bands = [AppColors.beamAmber, AppColors.beamMint, AppColors.beamCoral];

  @override
  Widget build(BuildContext context) {
    final pct = (learned / target).clamp(0.0, 1.0);
    return Semantics(
      label: 'Mục tiêu hôm nay: $learned trên $target từ mới',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // light leaving the prism: three beams, as long as today's progress
          for (var i = 0; i < 3; i++) ...[
            if (i > 0) SizedBox(height: 3.h),
            ClipRRect(
              borderRadius: BorderRadius.horizontal(right: Radius.circular(10.r)),
              child: Container(
                height: 9.h,
                color: _bands[i].withValues(alpha: 0.16),
                alignment: Alignment.centerLeft,
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: math.max(pct, 0.03)),
                  duration: Duration(milliseconds: 900 + i * 80),
                  curve: Curves.easeOutCubic,
                  builder: (context, v, _) => FractionallySizedBox(
                    widthFactor: v,
                    child: ColoredBox(color: _bands[i], child: const SizedBox.expand()),
                  ),
                ),
              ),
            ),
          ],
          SizedBox(height: 8.h),
          Text.rich(
            TextSpan(children: [
              TextSpan(
                text: '$learned/$target',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15.sp),
              ),
              TextSpan(text: '  từ mới hôm nay', style: TextStyle(color: Colors.white.withValues(alpha: 0.7), fontSize: 13.sp)),
            ]),
            style: const TextStyle(fontFeatures: [FontFeature.tabularFigures()]),
          ),
        ],
      ),
    );
  }
}

/// Buttons on the ink surface: white filled for the main action, a quiet tint for the other.
class _InkButton extends StatelessWidget {
  const _InkButton({required this.label, required this.onTap, this.filled = false, this.icon});

  final String label;
  final VoidCallback onTap;
  final bool filled;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    const fg = Colors.white;
    return Material(
      color: filled ? AppColors.primary : Colors.white.withValues(alpha: 0.1),
      borderRadius: BorderRadius.circular(14.r),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14.r),
        child: SizedBox(
          height: 52.h,
          child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            if (icon != null) ...[Icon(icon, size: 18.sp, color: fg), SizedBox(width: 6.w)],
            Flexible(
              child: Text(label,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(color: fg, fontWeight: FontWeight.w700, fontSize: 15.sp)),
            ),
          ]),
        ),
      ),
    );
  }
}

/// The language's own letters on its beam colour (same as the web): EN, 简 / 繁, VI.
class _LangGlyph extends StatelessWidget {
  const _LangGlyph({required this.user});

  final AppUser user;

  @override
  Widget build(BuildContext context) {
    final lang = user.activeLanguage;
    final color = lang == 'zh' ? AppColors.beamCoral : lang == 'vi' ? AppColors.beamMint : AppColors.beamAmber;
    final text = lang == 'zh' ? (user.zhScript == 'hant' ? '繁' : '简') : lang.toUpperCase();
    return Container(
      width: 20.w,
      height: 20.w,
      alignment: Alignment.center,
      decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(5.r)),
      child: Text(
        text,
        style: TextStyle(
          color: AppColors.ink,
          fontWeight: FontWeight.w700,
          fontSize: lang == 'zh' ? 12.sp : 9.sp,
          height: 1,
          locale: lang == 'zh' ? Locale.fromSubtags(languageCode: 'zh', scriptCode: user.zhScript == 'hant' ? 'Hant' : 'Hans') : null,
        ),
      ),
    );
  }
}

/// "Từ của hôm nay": one verified word seen through all three beams – English, Chinese
/// (in the learner's script) and Vietnamese – the same word for everyone on the same day.
class _TodayWord extends StatefulWidget {
  const _TodayWord();

  @override
  State<_TodayWord> createState() => _TodayWordState();
}

class _TodayWordState extends State<_TodayWord> {
  late final Future<(WordCard, WordCard?)?> _future = _load();

  static int get _day => DateTime.now().difference(DateTime(2026)).inDays;

  Future<(WordCard, WordCard?)?> _load() async {
    final script = AuthService.to.user.value?.zhScript ?? 'hans';
    final (count, _) = await VocabRepository.wordPage('zh', script, 1, pageSize: 1);
    if (count == 0) return null;
    final pages = (count / 50).ceil();
    final (_, list) = await VocabRepository.wordPage('zh', script, _day % pages + 1);
    if (list.isEmpty) return null;
    final start = _day % list.length;
    final ordered = [...list.sublist(start), ...list.sublist(0, start)];
    final zh = ordered.firstWhere((w) => w.image != null && w.partOfSpeech == 'noun',
        orElse: () => ordered.firstWhere((w) => w.image != null, orElse: () => ordered.first));
    final en = await VocabRepository.word(zh.id, 'en');
    return (zh, en);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<(WordCard, WordCard?)?>(
      future: _future,
      builder: (context, snap) {
        final data = snap.data;
        if (data == null) return const SizedBox.shrink();
        final (zh, en) = data;
        final rows = [
          ('EN', 'Tiếng Anh', AppColors.beamAmber, en?.target?.text ?? zh.english ?? '', (en?.target?.ipa ?? '').isEmpty ? '' : '/${en!.target!.ipa}/', en?.target),
          (zh.target?.language == 'zh-Hant' ? '繁' : '简', 'Tiếng Trung', AppColors.beamCoral, zh.target?.text ?? '', zh.target?.pinyin ?? '', zh.target),
          ('VI', 'Tiếng Việt', AppColors.beamMint, zh.meaningVi, '', null),
        ];
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Từ của hôm nay',
                style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary, letterSpacing: -0.2)),
            SizedBox(height: 12.h),
            Container(
              padding: EdgeInsets.all(16.w),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(20.r),
                border: Border.fromBorderSide(BorderSide(color: AppColors.line)),
              ),
              child: Column(children: [
                if (zh.image != null)
                  ClipRRect(
                    borderRadius: BorderRadius.circular(14.r),
                    child: Image.network(zh.image!, height: 150.h, width: double.infinity, fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => const SizedBox.shrink()),
                  ),
                for (final r in rows)
                  Container(
                    margin: EdgeInsets.only(top: 14.h),
                    padding: EdgeInsets.only(top: 10.h),
                    decoration: BoxDecoration(border: Border(top: BorderSide(color: r.$3, width: 3))),
                    child: Row(children: [
                      Container(
                        width: 22.w,
                        height: 22.w,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(color: r.$3, borderRadius: BorderRadius.circular(5.r)),
                        child: Text(r.$1, style: TextStyle(color: AppColors.ink, fontWeight: FontWeight.w700, fontSize: r.$1.length > 1 ? 9.sp : 12.sp, height: 1)),
                      ),
                      SizedBox(width: 12.w),
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(r.$4.isEmpty ? '—' : r.$4,
                              style: TextStyle(
                                fontSize: 26.sp,
                                fontWeight: FontWeight.w700,
                                color: AppColors.textPrimary,
                                height: 1.15,
                                locale: r.$6 != null && r.$6!.language.startsWith('zh') ? localeFor(r.$6!.language) : null,
                              )),
                          if (r.$5.isNotEmpty) Text(r.$5, style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
                        ]),
                      ),
                      Text(r.$2, style: TextStyle(fontSize: 12.sp, color: AppColors.textHint)),
                    ]),
                  ),
              ]),
            ),
          ],
        );
      },
    );
  }
}
