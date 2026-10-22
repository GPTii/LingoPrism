import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/community_controller.dart';
import 'package:lingoprism/app/data/services/auth_service.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class StudyGroupTabView extends StatelessWidget {
  const StudyGroupTabView({
    super.key,
    required this.controller,
  });

  final CommunityController controller;

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final joined = controller.joinedGroupDetails.value;
      if (joined != null) {
        return JoinedGroupView(
          controller: controller,
          details: joined,
          onLeave: controller.leaveGroup,
          onOpenChat: controller.openChat,
          onMemberTap: controller.openGroupMemberProfile,
        );
      }
      return StudyGroupList(
        controller: controller,
        onGroupTap: (context, group) => _onGroupTap(context, group),
        onLeaderTap: (group) {
          final currentUserId = Get.isRegistered<AuthService>()
              ? AuthService.to.currentUserId
              : '';
          if (group.requireApproval && currentUserId == group.leaderId) {
            controller.showPendingJoinRequestsSheet(context, group.groupId);
          } else {
            controller.openStudyGroupLeaderProfile(group);
          }
        },
      );
    });
  }

  void _onGroupTap(BuildContext context, CommunityStudyGroup group) {
    if (group.requireApproval) {
      _showJoinRequestSheet(context, group);
    } else {
      controller.joinGroup(group);
    }
  }

  void _showJoinRequestSheet(BuildContext context, CommunityStudyGroup group) {
    final messageController = TextEditingController();
    Get.bottomSheet(
      Builder(
        builder: (sheetContext) {
          final bottomInset = MediaQuery.of(sheetContext).viewInsets.bottom;
          return SafeArea(
            child: SingleChildScrollView(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(32.r)),
                ),
                padding: EdgeInsets.only(
                  left: 20.w,
                  right: 20.w,
                  top: 24.h,
                  bottom: bottomInset + 20.h,
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Center(
                      child: Container(
                        width: 48.w,
                        height: 4.h,
                        decoration: BoxDecoration(
                          color: AppColors.line,
                          borderRadius: BorderRadius.circular(12.r),
                        ),
                      ),
                    ),
                    SizedBox(height: 18.h),
                    Text(
                      'Tham gia nhóm',
                      style: TextStyle(
                        fontSize: 18.sp,
                        fontWeight: FontWeight.w700,
                        color: AppColors.ink,
                      ),
                    ),
                    SizedBox(height: 16.h),
                    TextField(
                      controller: messageController,
                      maxLines: 4,
                      decoration: InputDecoration(
                        hintText: 'Giới thiệu bản thân với trưởng nhóm',
                        hintStyle: TextStyle(
                          fontSize: 14.sp,
                          color: AppColors.textHint,
                        ),
                        filled: true,
                        fillColor: AppColors.primarySoft,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18.r),
                          borderSide: BorderSide(
                            color: AppColors.primaryTint,
                            width: 1.2,
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18.r),
                          borderSide: BorderSide(
                            color: AppColors.primaryTint,
                            width: 1.2,
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18.r),
                          borderSide: BorderSide(
                            color: AppColors.primary,
                            width: 1.4,
                          ),
                        ),
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 16.w,
                          vertical: 14.h,
                        ),
                      ),
                    ),
                    SizedBox(height: 20.h),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          foregroundColor: Colors.white,
                          padding: EdgeInsets.symmetric(vertical: 14.h),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14.r),
                          ),
                        ),
                        onPressed: () {
                          goBack();
                          controller.submitJoinRequest(
                            group: group,
                            message: messageController.text,
                          );
                        },
                        child: Text(
                          'Gửi yêu cầu',
                          style: TextStyle(
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
      isScrollControlled: true,
    );
  }
}

class StudyGroupList extends StatelessWidget {
  const StudyGroupList({
    super.key,
    required this.controller,
    required this.onGroupTap,
    required this.onLeaderTap,
  });

  final CommunityController controller;
  final void Function(BuildContext context, CommunityStudyGroup group)
      onGroupTap;
  final ValueChanged<CommunityStudyGroup> onLeaderTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        GroupSearchBar(controller: controller),
        SizedBox(height: 18.h),
        Expanded(
          child: Obx(
            () {
              final groups = controller.filteredStudyGroups;
              if (groups.isEmpty) {
                return Center(
                  child: Text(
                    'Không tìm thấy nhóm phù hợp.',
                    style: TextStyle(
                      fontSize: 14.sp,
                      color: AppColors.textSecondary,
                    ),
                  ),
                );
              }
              return ListView.separated(
                padding: EdgeInsets.only(bottom: 24.h),
                physics: const BouncingScrollPhysics(),
                itemCount: groups.length,
                separatorBuilder: (_, __) => SizedBox(height: 12.h),
                itemBuilder: (context, index) {
                  final group = groups[index];
                  return StudyGroupCard(
                    group: group,
                    onTap: () => onGroupTap(context, group),
                    onLeaderTap: () => onLeaderTap(group),
                  );
                },
              );
            },
          ),
        ),
      ],
    );
  }
}

class GroupSearchBar extends StatelessWidget {
  const GroupSearchBar({super.key, required this.controller});

  final CommunityController controller;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Container(
            height: 48.h,
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(28.r),
              border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
            alignment: Alignment.center,
            child: Obx(() {
              final hasText = controller.groupSearchQuery.value.isNotEmpty;
              return TextField(
                controller: controller.groupSearchController,
                onChanged: controller.onStudyGroupSearch,
                decoration: InputDecoration(
                  hintText: 'Tìm nhóm',
                  hintStyle: TextStyle(
                    fontSize: 14.sp,
                    color: AppColors.textHint,
                  ),
                  prefixIcon: Icon(
                    Icons.search_rounded,
                    color: AppColors.primary,
                    size: 22.sp,
                  ),
                  suffixIcon: hasText
                      ? IconButton(
                          icon: Icon(
                            Icons.close_rounded,
                            color: AppColors.textHint,
                            size: 20.sp,
                          ),
                          onPressed: () {
                            controller.groupSearchController.clear();
                            controller.onStudyGroupSearch('');
                            FocusScope.of(context).unfocus();
                          },
                          splashRadius: 18.r,
                        )
                      : null,
                  border: InputBorder.none,
                  enabledBorder: InputBorder.none,
                  focusedBorder: InputBorder.none,
                  contentPadding: EdgeInsets.symmetric(vertical: 12.h),
                ),
              );
            }),
          ),
        ),
        SizedBox(width: 14.w),
        GestureDetector(
          onTap: controller.onCreateGroup,
          child: Container(
            width: 52.w,
            height: 52.w,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.primary,
              boxShadow: [
                BoxShadow(
                  color: AppColors.primary.withValues(alpha: 0.28),
                  blurRadius: 14.r,
                  offset: Offset(0, 8.h),
                ),
              ],),
            child: Icon(
              Icons.add_rounded,
              color: Colors.white,
              size: 28.sp,
            ),
          ),
        ),
      ],
    );
  }
}

class JoinedGroupView extends StatelessWidget {
  const JoinedGroupView({
    super.key,
    required this.controller,
    required this.details,
    required this.onLeave,
    required this.onOpenChat,
    required this.onMemberTap,
  });

  final CommunityController controller;
  final CommunityGroupDetails details;
  final VoidCallback onLeave;
  final VoidCallback onOpenChat;
  final ValueChanged<CommunityGroupMemberScore> onMemberTap;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      padding: EdgeInsets.only(bottom: 24.h),
      child: Column(
        children: [
          GroupHeaderCard(
            controller: controller,
            details: details,
            onLeave: onLeave,
            onOpenChat: onOpenChat,
            onNotificationsTap: () => controller.showPendingJoinRequestsSheet(
              context,
              details.group.groupId,
            ),
          ),
          SizedBox(height: 16.h),
          MilestoneOverview(details: details),
          SizedBox(height: 16.h),
          LeaderboardList(
            members: details.memberScores,
            onMemberTap: onMemberTap,
          ),
        ],
      ),
    );
  }
}

class GroupHeaderCard extends StatelessWidget {
  const GroupHeaderCard({
    super.key,
    required this.controller,
    required this.details,
    required this.onLeave,
    required this.onOpenChat,
    this.onNotificationsTap,
  });

  final CommunityController controller;
  final CommunityGroupDetails details;
  final VoidCallback onLeave;
  final VoidCallback onOpenChat;
  final VoidCallback? onNotificationsTap;

  @override
  Widget build(BuildContext context) {
    final group = details.group;
    // show info chip inline below the leader name when approval is required

    return Container(
      padding: EdgeInsets.all(20.w),
      decoration: BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.circular(30.r),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withValues(alpha: 0.28),
            blurRadius: 24.r,
            offset: Offset(0, 14.h),
          ),
        ],),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                height: 120.h,
                width: 120.h,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(24.r),
                ),
                padding: EdgeInsets.all(10.w),
                child: GroupImage(path: group.assetImage, size: 56.w),
              ),
              SizedBox(width: 16.w),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Align(
                      alignment: Alignment.centerRight,
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Obx(() {
                            final count = controller.incomingJoinRequests
                                .where((r) => r.groupId == details.group.groupId)
                                .length;
                            return Stack(
                              clipBehavior: Clip.none,
                              children: [
                                _HeaderActionButton(
                                  icon: Icons.notifications_none_outlined,
                                  onTap: onNotificationsTap ?? () {},
                                  backgroundColor:
                                      Colors.white.withValues(alpha: 0.2),
                                  iconColor: AppColors.primary,
                                  borderColor:
                                      Colors.white.withValues(alpha: 0.55),
                                ),
                                if (count > 0)
                                  Positioned(
                                    right: -6.w,
                                    top: -6.h,
                                    child: Container(
                                      padding: EdgeInsets.symmetric(
                                        horizontal: 6.w,
                                        vertical: 2.h,
                                      ),
                                      decoration: BoxDecoration(
                                        color: AppColors.error,
                                        borderRadius:
                                            BorderRadius.circular(12.r),
                                        border: Border.all(
                                          color: Colors.white,
                                          width: 1.2,
                                        ),
                                      ),
                                      child: Text(
                                        count > 99 ? '99+' : '$count',
                                        style: TextStyle(
                                          color: Colors.white,
                                          fontSize: 10.sp,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                    ),
                                  ),
                              ],
                            );
                          }),
                          SizedBox(width: 12.w),
                          _HeaderActionButton(
                            icon: Icons.chat_bubble_outline_rounded,
                            onTap: onOpenChat,
                            backgroundColor:
                                Colors.white.withValues(alpha: 0.2),
                            iconColor: AppColors.primary,
                            borderColor:
                                Colors.white.withValues(alpha: 0.55),
                          ),
                          SizedBox(width: 12.w),
                          _HeaderActionButton(
                            icon: Icons.logout_rounded,
                            onTap: onLeave,
                            backgroundColor:
                                Colors.white.withValues(alpha: 0.2),
                            iconColor: AppColors.error,
                            borderColor:
                                Colors.white.withValues(alpha: 0.55),
                          ),
                        ],
                      ),
                    ),
                    SizedBox(height: 16.h),
                    Text(
                      group.name,
                      style: TextStyle(
                        fontSize: 20.sp,
                        fontWeight: FontWeight.w700,
                        color: Colors.white,
                      ),
                    ),
                    SizedBox(height: 6.h),
                    Text(
                      '${group.memberCount} thành viên',
                      style: TextStyle(
                        fontSize: 13.sp,
                        color: Colors.white.withValues(alpha: 0.9),
                      ),
                    ),
                    SizedBox(height: 4.h),
                    Text(
                      'Trưởng nhóm: ${group.leaderName}',
                      style: TextStyle(
                        fontSize: 12.sp,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (group.requireApproval) ...[
            SizedBox(height: 16.h),
            const _GroupInfoChip(
              icon: Icons.verified_user_outlined,
              label: 'Cần trưởng nhóm duyệt',
            ),
          ],
        ],
      ),
    );
  }
}

class _HeaderActionButton extends StatelessWidget {
  const _HeaderActionButton({
    required this.icon,
    required this.onTap,
    this.backgroundColor,
    this.iconColor,
    this.borderColor,
  });

  final IconData icon;
  final VoidCallback onTap;
  final Color? backgroundColor;
  final Color? iconColor;
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    final resolvedBackground = backgroundColor ?? Colors.white;
    final resolvedBorder = borderColor ?? (iconColor ?? AppColors.primary);
    final resolvedIcon = iconColor ?? resolvedBorder;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 44.w,
        height: 44.w,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: resolvedBackground,
          border: Border.all(color: resolvedBorder, width: 1.4),),
        alignment: Alignment.center,
        child: Icon(icon, color: resolvedIcon, size: 20.sp),
      ),
    );
  }
}

class _GroupInfoChip extends StatelessWidget {
  const _GroupInfoChip({
    required this.icon,
    required this.label,
  });

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(20.r),
        border: Border.all(color: Colors.white.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16.sp, color: Colors.white),
          SizedBox(width: 6.w),
          Text(
            label,
            style: TextStyle(
              fontSize: 12.sp,
              color: Colors.white,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class MilestoneOverview extends StatelessWidget {
  const MilestoneOverview({super.key, required this.details});

  final CommunityGroupDetails details;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(22.w),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(28.r),
        border: Border.all(color: AppColors.primaryLight, width: 1.2),),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Mốc hiện tại',
                      style: TextStyle(
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primaryDark,
                      ),
                    ),
                    SizedBox(height: 6.h),
                    Text(
                      details.currentMilestoneLabel,
                      style: TextStyle(
                        fontSize: 22.sp,
                        fontWeight: FontWeight.w800,
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ),
              ),
              _InfoBadge(
                icon: Icons.timer_outlined,
                label: '${details.daysRemaining} ngày còn lại',
              ),
            ],
          ),
          SizedBox(height: 20.h),
          ProgressMilestones(
            milestones: details.milestones,
            currentPoints: details.currentPoints,
          ),
          SizedBox(height: 20.h),
          _PointsSummary(points: details.currentPoints),
        ],
      ),
    );
  }
}

class _InfoBadge extends StatelessWidget {
  const _InfoBadge({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 8.h),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(18.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16.sp, color: AppColors.primary),
          SizedBox(width: 6.w),
          Text(
            label,
            style: TextStyle(
              fontSize: 12.sp,
              fontWeight: FontWeight.w600,
              color: AppColors.primary,
            ),
          ),
        ],
      ),
    );
  }
}

class _PointsSummary extends StatelessWidget {
  const _PointsSummary({required this.points});

  final int points;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 16.h),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(24.r),
      ),
      child: Row(
        children: [
          Container(
            width: 48.w,
            height: 48.w,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.surface,
              border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
            alignment: Alignment.center,
            child: Image.asset(
              'assets/brand/icons/xp.png',
              width: 26.w,
              height: 26.w,
              fit: BoxFit.contain,
            ),
          ),
          SizedBox(width: 16.w),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$points',
                style: TextStyle(
                  fontSize: 26.sp,
                  fontWeight: FontWeight.w800,
                  color: AppColors.primary,
                ),
              ),
              SizedBox(height: 4.h),
              Text(
                'XP tích luỹ của nhóm',
                style: TextStyle(
                  fontSize: 13.sp,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class ProgressMilestones extends StatelessWidget {
  const ProgressMilestones({
    super.key,
    required this.milestones,
    required this.currentPoints,
  });

  final List<CommunityGroupMilestone> milestones;
  final int currentPoints;

  @override
  Widget build(BuildContext context) {
    if (milestones.isEmpty) {
      return const SizedBox.shrink();
    }
    final nextIndex = milestones.indexWhere(
      (milestone) => !(milestone.isReached || currentPoints >= milestone.requiredPoints),
    );
    return SizedBox(
      height: 170.h,
      child: ListView.separated(
        padding: EdgeInsets.symmetric(horizontal: 4.w),
        scrollDirection: Axis.horizontal,
        physics: const BouncingScrollPhysics(),
        itemCount: milestones.length,
        separatorBuilder: (_, __) => SizedBox(width: 16.w),
        itemBuilder: (context, index) {
          final milestone = milestones[index];
          return ProgressStep(
            index: index,
            milestone: milestone,
            currentPoints: currentPoints,
            isNext: nextIndex != -1 && index == nextIndex,
          );
        },
      ),
    );
  }
}

class ProgressStep extends StatelessWidget {
  const ProgressStep({
    super.key,
    required this.index,
    required this.milestone,
    required this.currentPoints,
    required this.isNext,
  });

  final int index;
  final CommunityGroupMilestone milestone;
  final int currentPoints;
  final bool isNext;

  bool get _isUnlocked => milestone.isReached || currentPoints >= milestone.requiredPoints;

  @override
  Widget build(BuildContext context) {
    final isCurrent = isNext && !_isUnlocked;
    final nhomIndex = (index % 5) + 1;
    final imagePath = _isUnlocked
        ? 'assets/brand/group/group_$nhomIndex.png'
        : 'assets/brand/rank/rank_locked.png';
    final textColor = _isUnlocked ? AppColors.primary : AppColors.textSecondary;
    final textWeight = _isUnlocked || isCurrent ? FontWeight.w700 : FontWeight.w600;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Container(
          width: 96.w,
          height: 96.w,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(28.r),
            color: _isUnlocked ? Colors.white : AppColors.primarySoft,
            border: Border.all(
              color: _isUnlocked ? Colors.white : AppColors.primaryTint,
              width: 1.1,
            ),),
          padding: EdgeInsets.all(12.w),
          child: Image.asset(
            imagePath,
            fit: BoxFit.contain,
          ),
        ),
        SizedBox(height: 12.h),
        Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text(
              '${milestone.requiredPoints}',
              style: TextStyle(
                fontSize: isCurrent ? 16.sp : 14.sp,
                fontWeight: textWeight,
                color: textColor,
              ),
            ),
            SizedBox(width: 6.w),
            Image.asset(
              'assets/brand/icons/xp.png',
              width: 18.w,
              height: 18.w,
              fit: BoxFit.contain,
            ),
          ],
        ),
        SizedBox(height: 6.h),
        Text(
          milestone.label,
          style: TextStyle(
            fontSize: 12.sp,
            color: AppColors.textSecondary,
            fontWeight: FontWeight.w600,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class LeaderboardList extends StatelessWidget {
  const LeaderboardList({
    super.key,
    required this.members,
    required this.onMemberTap,
  });

  final List<CommunityGroupMemberScore> members;
  final ValueChanged<CommunityGroupMemberScore> onMemberTap;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      physics: const NeverScrollableScrollPhysics(),
      shrinkWrap: true,
      itemCount: members.length,
      padding: EdgeInsets.only(bottom: 24.h),
      separatorBuilder: (_, __) => SizedBox(height: 12.h),
      itemBuilder: (context, index) {
        final member = members[index];
        return LeaderboardTile(
          member: member,
          index: index,
          onTap: () => onMemberTap(member),
        );
      },
    );
  }
}

class LeaderboardTile extends StatelessWidget {
  const LeaderboardTile({
    super.key,
    required this.member,
    required this.index,
    required this.onTap,
  });

  final CommunityGroupMemberScore member;
  final int index;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = _resolveColors();
    final isHighlighted = member.isHighlighted;
    final borderColor = isHighlighted ? AppColors.primary : colors.border;
    final shadowColor = isHighlighted
        ? AppColors.primary.withValues(alpha: 0.28)
        : colors.shadow.withValues(alpha: 0.24);
  // badgeBackground not used directly (kept for future styling)

    Widget buildAvatar() {
      final avatarBorderColor =
          isHighlighted ? AppColors.primary : Colors.white.withValues(alpha: 0.7);
      final avatarUrl = member.avatarUrl.trim();

      Widget avatarContent;
      if (avatarUrl.isEmpty) {
        avatarContent = Icon(
          Icons.person_rounded,
          size: 22.sp,
          color: colors.secondary,
        );
      } else if (avatarUrl.startsWith('http')) {
        avatarContent = ClipOval(
          child: Image.network(
            avatarUrl,
            width: 44.w,
            height: 44.w,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Icon(
              Icons.person_rounded,
              size: 22.sp,
              color: colors.secondary,
            ),
          ),
        );
      } else if (avatarUrl.startsWith('assets/')) {
        avatarContent = ClipOval(
          child: Image.asset(
            avatarUrl,
            width: 44.w,
            height: 44.w,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Icon(
              Icons.person_rounded,
              size: 22.sp,
              color: colors.secondary,
            ),
          ),
        );
      } else {
        avatarContent = ClipOval(
          child: Image.file(
            File(avatarUrl),
            width: 44.w,
            height: 44.w,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Icon(
              Icons.person_rounded,
              size: 22.sp,
              color: colors.secondary,
            ),
          ),
        );
      }

      return Container(
        padding: EdgeInsets.all(2.w),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: avatarBorderColor,
            width: isHighlighted ? 2 : 1.2,
          ),
        ),
        child: Container(
          width: 48.w,
          height: 48.w,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: AppColors.surface,
          ),
          alignment: Alignment.center,
          child: avatarContent,
        ),
      );
    }

    Widget buildRankBadge() {
      return Container(
        width: 34.w,
        height: 34.w,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: AppColors.surface,
          border: Border.all(
            color: colors.primary.withValues(alpha: 0.18),
            width: 1.2,
          ),
        ),
        alignment: Alignment.center,
        child: Text(
          '${index + 1}',
          style: TextStyle(
            fontSize: 15.sp,
            fontWeight: FontWeight.w800,
            color: colors.primary,
          ),
        ),
      );
    }

    Widget buildPointPill() {
      return Container(
        padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 9.h),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(22.r),
          border: Border.all(
            color: colors.primary.withValues(alpha: 0.12),
            width: 1,
          ),),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset(
              'assets/brand/icons/xp.png',
              width: 20.w,
              height: 20.w,
              fit: BoxFit.contain,
            ),
            SizedBox(width: 8.w),
            Text(
              '${member.totalPoints}',
              style: TextStyle(
                fontSize: 15.sp,
                fontWeight: FontWeight.w700,
                color: colors.primary,
              ),
            ),
          ],
        ),
      );
    }

  

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 18.h),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24.r),
          color: (colors.background).first,
          border: Border.all(color: borderColor, width: isHighlighted ? 1.6 : 1.2),),
        child: Row(
          children: [
            buildRankBadge(),
            SizedBox(width: 12.w),
            buildAvatar(),
            SizedBox(width: 14.w),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      SizedBox(width: 6.w),
                      Expanded(
                        child: Text(
                          member.displayName,
                          style: TextStyle(
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w700,
                            color: colors.primary,
                          ),
                        ),
                      ),
                      if (isHighlighted)
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 6.h),
                          decoration: BoxDecoration(
                            color: colors.primary.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(16.r),
                            border: Border.all(
                              color: colors.primary.withValues(alpha: 0.25),
                              width: 1,
                            ),
                          ),
                          child: Text(
                            'Bạn',
                            style: TextStyle(
                              fontSize: 12.sp,
                              fontWeight: FontWeight.w600,
                              color: colors.primary,
                            ),
                          ),
                        ),
                    ],
                  ),
                  SizedBox(height: 10.h),
                  buildPointPill(),
                      
                    
                  
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  _LeaderboardColors _resolveColors() {
    switch (index) {
      case 0:
        return _LeaderboardColors(
          background: [AppColors.tint(const Color(0xFFFFF4D8)), const Color(0xFFFFD58D)],
          primary: const Color(0xFF7F4A00),
          secondary: const Color(0xFFB47305),
          shadow: const Color(0xFFFFD06A),
          border: const Color(0xFFFFCB59),
          badgeBackground: AppColors.tint(const Color(0xFFFFF1D9)),
        );
      case 1:
        return _LeaderboardColors(
          background: [AppColors.primarySoft, AppColors.primaryTint],
          primary: AppColors.ink,
          secondary: AppColors.textSecondary,
          shadow: AppColors.primaryLight,
          border: AppColors.primaryTint,
          badgeBackground: AppColors.primarySoft,
        );
      case 2:
        return _LeaderboardColors(
          background: [AppColors.tint(const Color(0xFFFFECD9)), const Color(0xFFFFCFA0)],
          primary: const Color(0xFF6E3600),
          secondary: const Color(0xFF9C5A26),
          shadow: const Color(0xFFFFB574),
          border: const Color(0xFFFFB168),
          badgeBackground: AppColors.tint(const Color(0xFFFFECD9)),
        );
      default:
        return _LeaderboardColors(
          background: [AppColors.primarySoft, AppColors.primarySoft],
          primary: AppColors.primaryDark,
          secondary: AppColors.textSecondary,
          shadow: AppColors.primaryTint,
          border: AppColors.primaryTint,
          badgeBackground: AppColors.primarySoft,
        );
    }
  }
}

class StudyGroupCard extends StatelessWidget {
  const StudyGroupCard({
    super.key,
    required this.group,
    required this.onTap,
    required this.onLeaderTap,
  });

  final CommunityStudyGroup group;
  final VoidCallback onTap;
  final VoidCallback onLeaderTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(26.r),
          color: AppColors.surface,
          border: Border.all(
            color: AppColors.primaryLight,
            width: 1.2,
          ),),
        padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 16.h),
        child: Row(
          children: [
            Container(
              height: 56.h,
              width: 56.w,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(18.r),
                color: AppColors.surface,
              ),
              padding: EdgeInsets.all(6.w),
              child: GroupImage(path: group.assetImage, size: 72.w),
            ),
            SizedBox(width: 14.w),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          group.name,
                          style: TextStyle(
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w700,
                            color: AppColors.primaryDark,
                          ),
                        ),
                      ),
                      if (group.requireApproval)
                        Container(
                          padding: EdgeInsets.symmetric(
                            horizontal: 10.w,
                            vertical: 4.h,
                          ),
                          decoration: BoxDecoration(
                            color:
                                AppColors.primary.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(16.r),
                          ),
                          child: Text(
                            'Cần duyệt',
                            style: TextStyle(
                              fontSize: 11.sp,
                              fontWeight: FontWeight.w600,
                              color: AppColors.primary,
                            ),
                          ),
                        ),
                    ],
                  ),
                  SizedBox(height: 6.h),
                  Text(
                    'Yêu cầu: ${group.requirement}',
                    style: TextStyle(
                      fontSize: 13.sp,
                      color: AppColors.textSecondary,
                    ),
                  ),
                  SizedBox(height: 4.h),
                  GestureDetector(
                    onTap: onLeaderTap,
                    child: Text(
                      'Trưởng nhóm: ${group.leaderName}',
                      style: TextStyle(
                        fontSize: 12.sp,
                        color: AppColors.primary,
                        decoration: TextDecoration.underline,
                        decorationStyle: TextDecorationStyle.dotted,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(width: 12.w),
            Container(
              width: 42.w,
              height: 42.w,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.surface,
                border: Border.all(
                  color: AppColors.primary,
                  width: 1.6,
                ),),
              alignment: Alignment.center,
              child: Text(
                '${group.memberCount}',
                style: TextStyle(
                  fontSize: 15.sp,
                  fontWeight: FontWeight.w700,
                  color: AppColors.primary,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class GroupImage extends StatelessWidget {
  const GroupImage({super.key, required this.path, required this.size});

  final String path;
  final double size;

  @override
  Widget build(BuildContext context) {
    final fallback = Image.asset(
      'assets/brand/group/group_1.png',
      width: size,
      height: size,
      fit: BoxFit.contain,
    );

    if (path.isEmpty) {
      return fallback;
    }

    if (path.startsWith('http')) {
      return Image.network(
        path,
        width: size,
        height: size,
        fit: BoxFit.contain,
        errorBuilder: (_, __, ___) => fallback,
      );
    }

    return Image.asset(
      path,
      width: size,
      height: size,
      fit: BoxFit.contain,
      errorBuilder: (_, __, ___) => fallback,
    );
  }
}

class _LeaderboardColors {
  _LeaderboardColors({
    required this.background,
    required this.primary,
    required this.secondary,
    required this.shadow,
    required this.border,
    required this.badgeBackground,
  });

  final List<Color> background;
  final Color primary;
  final Color secondary;
  final Color shadow;
  final Color border;
  final Color badgeBackground;
}
