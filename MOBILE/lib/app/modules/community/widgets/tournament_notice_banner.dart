import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../models/community_models.dart';

class TournamentNoticeBanner extends StatelessWidget {
  const TournamentNoticeBanner({super.key, required this.notice});

  final TournamentNotice notice;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 16.h),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFFFE0B2), Color(0xFFFFF3E0)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 18.r,
            offset: Offset(0, 10.h),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 36.w,
                height: 36.w,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  color: Color(0xFFFF9800),
                ),
                child: const Icon(
                  Icons.local_fire_department_rounded,
                  color: Colors.white,
                ),
              ),
              SizedBox(width: 12.w),
              Expanded(
                child: Text(
                  notice.headline,
                  style: TextStyle(
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w800,
                    color: const Color(0xFF4A2C00),
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 12.h),
          _NoticeLine(
            icon: Icons.emoji_events_outlined,
            text: notice.leaderboardText,
          ),
          SizedBox(height: 8.h),
          _NoticeLine(
            icon: Icons.group_work_outlined,
            text: notice.groupText,
          ),
          SizedBox(height: 8.h),
          _NoticeLine(
            icon: Icons.card_giftcard_outlined,
            text: notice.rewardText,
          ),
        ],
      ),
    );
  }
}

class _NoticeLine extends StatelessWidget {
  const _NoticeLine({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(
          icon,
          size: 20.sp,
          color: const Color(0xFFB76E00),
        ),
        SizedBox(width: 8.w),
        Expanded(
          child: Text(
            text,
            style: TextStyle(
              fontSize: 13.sp,
              color: const Color(0xFF5A3200),
              height: 1.3,
            ),
          ),
        ),
      ],
    );
  }
}
