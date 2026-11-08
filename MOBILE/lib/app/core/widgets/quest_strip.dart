import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../data/models/api/game.dart';
import '../../data/services/game_service.dart';
import '../theme/app_colors.dart';
import 'app_icon.dart';

/// The phone's answer to the web's right-hand rail (FE SideRail): a slim strip – streak, today's XP, gems and
/// "Nhiệm vụ x/n" – at the top of the learning screens; tapping it opens the daily quests in a bottom sheet
/// (progress, chest, "Nhận"), plus the month's challenge. One tap away, never in the way of the screen itself.
class QuestStrip extends StatelessWidget {
  const QuestStrip({super.key});

  @override
  Widget build(BuildContext context) {
    final game = GameService.to;
    return Obx(() {
      final s = game.summary.value;
      final quests = game.quests;
      final done = quests.where((q) => q.completed).length;
      final toClaim = quests.where((q) => q.completed && !q.rewardClaimed).length;
      return Material(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16.r),
        child: InkWell(
          borderRadius: BorderRadius.circular(16.r),
          onTap: () => showQuestSheet(),
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(16.r), border: Border.all(color: AppColors.line)),
            child: Row(children: [
              _Stat(
                  icon: Icon(Icons.local_fire_department_rounded,
                      color: s.studiedToday ? const Color(0xFFFF9600) : AppColors.textHint, size: 22.sp),
                  value: '${s.streak}'),
              _Stat(icon: AppIcon('sparkle', size: 20.sp), value: '${s.todayXp} XP'),
              _Stat(icon: Image.asset('assets/brand/icons/gem.png', width: 20.sp, height: 20.sp), value: '${s.gems}'),
              const Spacer(),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 5.h),
                decoration: BoxDecoration(
                  color: toClaim > 0 ? AppColors.beamAmber : AppColors.primarySoft,
                  borderRadius: BorderRadius.circular(12.r),
                ),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  AppIcon('chest', size: 18.sp),
                  SizedBox(width: 4.w),
                  Text(toClaim > 0 ? 'Nhận thưởng' : 'Nhiệm vụ $done/${quests.length}',
                      style:
                          TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w800, color: toClaim > 0 ? Colors.white : AppColors.primary)),
                ]),
              ),
            ]),
          ),
        ),
      );
    });
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.icon, required this.value});
  final Widget icon;
  final String value;

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.only(right: 12.w),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          icon,
          SizedBox(width: 3.w),
          Text(value, style: TextStyle(fontSize: 13.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
        ]),
      );
}

const _questIcon = {
  'save_words': 'camera',
  'reach_learn_goal': 'sparkle',
  'reach_review_goal': 'review',
  'win_games': 'game',
  'post_community_image': 'photo',
  'engage_community': 'community',
};

/// The daily quests (rewards to collect first) and the month's challenge, in a bottom sheet.
void showQuestSheet() {
  GameService.to.refreshQuests();
  Get.bottomSheet(
    const _QuestSheet(),
    isScrollControlled: true,
    backgroundColor: AppColors.surface,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20.r))),
  );
}

class _QuestSheet extends StatelessWidget {
  const _QuestSheet();

  int _rank(DailyQuest q) => q.completed && !q.rewardClaimed ? 0 : (!q.completed ? 1 : 2);

  Future<void> _claim(DailyQuest q) async {
    try {
      final (scales, gems) = await GameService.to.claimQuest(q);
      Get.snackbar('Đã nhận thưởng', '+$scales vảy${gems > 0 ? ', +$gems ngọc' : ''}',
          snackPosition: SnackPosition.BOTTOM, duration: const Duration(seconds: 2));
    } catch (_) {
      Get.snackbar('Chưa nhận được', 'Thử lại sau ít giây nhé.', snackPosition: SnackPosition.BOTTOM);
    }
  }

  @override
  Widget build(BuildContext context) {
    final game = GameService.to;
    return ConstrainedBox(
      constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * 0.8),
      child: SafeArea(
        top: false,
        child: Obx(() {
          final quests = [...game.quests]..sort((a, b) => _rank(a) - _rank(b));
          final m = game.monthly.value;
          return ListView(shrinkWrap: true, padding: EdgeInsets.fromLTRB(16.w, 14.h, 16.w, 20.h), children: [
            Text('Nhiệm vụ hằng ngày', style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
            SizedBox(height: 12.h),
            if (quests.isEmpty) Text('Học một bài để mở nhiệm vụ hôm nay.', style: TextStyle(color: AppColors.textSecondary)),
            for (final q in quests)
              Padding(
                padding: EdgeInsets.only(bottom: 14.h),
                child: Row(children: [
                  AppIcon(_questIcon[q.kind] ?? 'target', size: 36.sp),
                  SizedBox(width: 10.w),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(q.title,
                          style: TextStyle(
                              fontSize: 14.sp,
                              fontWeight: FontWeight.w700,
                              color: q.rewardClaimed ? AppColors.textHint : AppColors.textPrimary)),
                      SizedBox(height: 4.h),
                      Stack(alignment: Alignment.center, children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(8.r),
                          child: LinearProgressIndicator(
                            value: q.ratio,
                            minHeight: 14.h,
                            backgroundColor: AppColors.surfaceMuted,
                            color: q.completed ? AppColors.success : const Color(0xFFFFC800),
                          ),
                        ),
                        Text('${q.progress.clamp(0, q.target)} / ${q.target}',
                            style: TextStyle(fontSize: 10.sp, fontWeight: FontWeight.w800, color: AppColors.textSecondary)),
                      ]),
                    ]),
                  ),
                  SizedBox(width: 10.w),
                  if (q.completed && !q.rewardClaimed)
                    FilledButton(onPressed: () => _claim(q), child: const Text('Nhận'))
                  else
                    Opacity(opacity: q.rewardClaimed ? 0.4 : 1, child: AppIcon('chest', size: 30.sp)),
                ]),
              ),
            if (m != null) ...[
              SizedBox(height: 6.h),
              Text('Thử thách tháng', style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
              SizedBox(height: 8.h),
              Row(children: [
                AppIcon('calendar', size: 34.sp),
                SizedBox(width: 10.w),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Hoàn thành ${m.target} nhiệm vụ trong tháng', style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
                    SizedBox(height: 4.h),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8.r),
                      child: LinearProgressIndicator(
                        value: m.target == 0 ? 0 : (m.completedCount / m.target).clamp(0, 1).toDouble(),
                        minHeight: 10.h,
                        backgroundColor: AppColors.surfaceMuted,
                        color: const Color(0xFFA78BFA),
                      ),
                    ),
                  ]),
                ),
                SizedBox(width: 10.w),
                Text('${m.completedCount}/${m.target}', style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
              ]),
            ],
          ]);
        }),
      ),
    );
  }
}
