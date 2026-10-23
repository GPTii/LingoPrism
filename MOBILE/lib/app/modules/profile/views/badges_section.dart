import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/theme/app_colors.dart';
import '../../../data/models/api/game.dart';

/// "Huy hiệu": the ones earned first, then the next to aim for; "Xem tất cả" opens every badge with its gem reward.
class BadgesSection extends StatelessWidget {
  const BadgesSection({super.key, required this.badges});

  final List<BadgeInfo> badges;

  @override
  Widget build(BuildContext context) {
    if (badges.isEmpty) return const SizedBox.shrink();
    final owned = badges.where((b) => b.owned).toList()..sort((a, b) => (b.awardedAt ?? DateTime(0)).compareTo(a.awardedAt ?? DateTime(0)));
    final next = badges.where((b) => !b.owned).take(8 - owned.length.clamp(0, 8));
    final shown = [...owned.take(8), ...next];
    return Container(
      padding: EdgeInsets.fromLTRB(14.w, 12.h, 6.w, 12.h),
      decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(16.r), border: Border.all(color: AppColors.line)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text('Huy hiệu', style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
          SizedBox(width: 6.w),
          Text('${owned.length}/${badges.length}', style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary, fontWeight: FontWeight.w600)),
          const Spacer(),
          TextButton(onPressed: () => _showAll(badges), child: const Text('Xem tất cả')),
        ]),
        SizedBox(
          height: 96.h,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: shown.length,
            separatorBuilder: (_, __) => SizedBox(width: 8.w),
            itemBuilder: (_, i) => SizedBox(width: 72.w, child: _Badge(badge: shown[i], compact: true)),
          ),
        ),
      ]),
    );
  }

  static void _showAll(List<BadgeInfo> badges) {
    Get.bottomSheet(
      Container(
        height: 0.85.sh,
        decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.vertical(top: Radius.circular(24.r))),
        padding: EdgeInsets.fromLTRB(16.w, 10.h, 16.w, 0),
        child: Column(children: [
          Container(width: 40.w, height: 4.h, decoration: BoxDecoration(color: AppColors.line, borderRadius: BorderRadius.circular(2.r))),
          SizedBox(height: 12.h),
          Text('Huy hiệu (${badges.where((b) => b.owned).length}/${badges.length})',
              style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
          Text('Mỗi huy hiệu mới tặng ngọc!', style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
          SizedBox(height: 10.h),
          Expanded(
            child: GridView.builder(
              padding: EdgeInsets.only(bottom: 24.h),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 3, mainAxisSpacing: 12.h, crossAxisSpacing: 8.w,
                  childAspectRatio: 0.62),
              itemCount: badges.length,
              itemBuilder: (_, i) => _Badge(badge: badges[i]),
            ),
          ),
        ]),
      ),
      isScrollControlled: true,
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.badge, this.compact = false});

  final BadgeInfo badge;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    Widget art = Image.asset(badge.icon, width: compact ? 56.w : 72.w, height: compact ? 56.w : 72.w,
        errorBuilder: (_, __, ___) => Icon(Icons.military_tech_rounded, size: 48.sp, color: AppColors.primary));
    if (!badge.owned) {
      art = Opacity(opacity: 0.4, child: ColorFiltered(colorFilter: const ColorFilter.matrix(_grey), child: art));
    }
    return Column(children: [
      art,
      SizedBox(height: 4.h),
      Text(badge.name, textAlign: TextAlign.center, maxLines: 2, overflow: TextOverflow.ellipsis,
          style: TextStyle(fontSize: compact ? 10.5.sp : 12.sp, height: 1.2, fontWeight: FontWeight.w700,
              color: badge.owned ? AppColors.textPrimary : AppColors.textSecondary)),
      if (!compact) ...[
        SizedBox(height: 2.h),
        Text(badge.description, textAlign: TextAlign.center, maxLines: 2, overflow: TextOverflow.ellipsis,
            style: TextStyle(fontSize: 10.5.sp, color: AppColors.textSecondary)),
        if (!badge.owned && badge.rewardGems > 0)
          Row(mainAxisSize: MainAxisSize.min, children: [
            Text('+${badge.rewardGems}', style: TextStyle(fontSize: 11.sp, fontWeight: FontWeight.w800, color: AppColors.primary)),
            Image.asset('assets/brand/icons/gem.png', width: 14.w),
          ]),
      ],
    ]);
  }
}

const _grey = <double>[
  0.2126, 0.7152, 0.0722, 0, 0, //
  0.2126, 0.7152, 0.0722, 0, 0, //
  0.2126, 0.7152, 0.0722, 0, 0, //
  0, 0, 0, 1, 0,
];
