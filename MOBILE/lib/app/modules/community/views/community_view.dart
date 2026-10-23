import '../../../core/widgets/prismo_avatar.dart';
import 'package:lingoprism/app/core/widgets/app_icon.dart';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';

import '../controllers/community_controller.dart';
import '../../community_detail/controllers/community_detail_controller.dart';
import '../../community_detail/views/community_detail_view.dart';
import '../../community_detail/bindings/community_detail_binding.dart';
import '../../../data/services/auth_service.dart';
import '../../../routes/app_pages.dart';
import 'follow_suggestions.dart';
import 'study_group_tab_view.dart';
import 'community_leaderboard_view.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

// Constants for validation and configuration
const int _maxTopicLength = 50;
const int _minTopicLength = 2;
const int _minReportDescriptionLength = 10;
const double _listCacheExtent = 1000.0;
const double _leaderboardCacheExtent = 500.0;

/// Helper function for formatting remaining time
String _formatRemainingTime(int daysRemaining) {
  if (daysRemaining <= 0) {
    return 'Đã kết thúc';
  } else if (daysRemaining == 1) {
    return 'Còn 1 ngày';
  } else {
    return 'Còn $daysRemaining ngày';
  }
}

/// Main community view with three tabs: Timeline Feed, Study Groups, and Leaderboard
///
/// Features:
/// - Feed with interactive posts, comments, and vocabulary learning
/// - Study group discovery and management
/// - League leaderboard with rankings and achievements
/// - Performance optimizations with RepaintBoundary and caching
/// - Comprehensive error handling and input validation
class CommunityView extends GetView<CommunityController> {
  const CommunityView({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        backgroundColor: AppColors.backgroundLight,
        body: SafeArea(
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 20.w),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(height: 12.h),
                Row(children: [
                  Expanded(child: _buildTabBar()),
                  if (AuthService.to.currentUser?.isKid != true)
                    IconButton(
                      tooltip: 'Bạn bè',
                      onPressed: () => Get.toNamed(Routes.friends),
                      icon: AppIcon('community', size: 28.w),
                    ),
                  if (AuthService.to.currentUser?.isKid != true)
                    IconButton(
                      tooltip: 'Tin nhắn',
                      onPressed: () => Get.toNamed(Routes.messages),
                      icon: Icon(Icons.chat_bubble_outline_rounded, color: AppColors.textPrimary),
                    ),
                ]),
                SizedBox(height: 16.h),
                Expanded(
                  child: TabBarView(
                    physics: const BouncingScrollPhysics(),
                    children: [
                      _buildFeed(),
                      _buildStudyGroups(),
                      _buildLeaderboard(),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTabBar() {
    return TabBar(
      labelStyle: TextStyle(
        fontSize: 13.sp,
        fontWeight: FontWeight.w700,
      ),
      unselectedLabelStyle: TextStyle(
        fontSize: 12.sp,
        fontWeight: FontWeight.w500,
      ),
      labelColor: AppColors.primary,
      unselectedLabelColor: AppColors.textPrimary,
      indicator: UnderlineTabIndicator(
        borderSide: BorderSide(
          color: AppColors.primary,
          width: 3.h,
        ),
        insets: EdgeInsets.symmetric(horizontal: 12.w),
      ),
      indicatorPadding: EdgeInsets.zero,
      indicatorSize: TabBarIndicatorSize.label,
      tabs: const [
        Tab(text: 'Dòng thời gian'),
        Tab(text: 'Nhóm học tập'),
        Tab(text: 'Bảng xếp hạng'),
      ],
    );
  }

  Widget _buildFeed() {
    return Obx(
      () {
        final isLoading = controller.isPostsLoading.value;
        final error = controller.postsError.value;
        final posts = controller.posts;

        if (isLoading) {
          return const Center(
            child: CircularProgressIndicator(),
          );
        }

        return RefreshIndicator(
          onRefresh: controller.reloadPosts,
          child: posts.isEmpty
              ? ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: [
                    SizedBox(height: 80.h),
                    _EmptyFeedState(
                      message: error ??
                          'Chưa cập nhật được dữ liệu, hãy thử tải lại nhé!',
                      onRetry: controller.reloadPosts,
                      isError: error != null,
                    ),
                  ],
                )
              : ListView.builder(
                  padding: EdgeInsets.only(bottom: 24.h),
                  itemCount: posts.length + 1,
                  cacheExtent: _listCacheExtent,
                  physics: const BouncingScrollPhysics(
                    parent: AlwaysScrollableScrollPhysics(),
                  ),
                  itemBuilder: (context, index) {
                    if (index == 0) return const FollowSuggestions();
                    final post = posts[index - 1];
                    return RepaintBoundary(
                      child: _FeedCard(post: post),
                    );
                  },
                ),
        );
      },
    );
  }

  Widget _buildStudyGroups() {
    return StudyGroupTabView(controller: controller);
  }

  Widget _buildLeaderboard() {
    return CommunityLeaderboardView(controller: controller);
  }
}

class _EmptyFeedState extends StatelessWidget {
  const _EmptyFeedState({
    required this.message,
    required this.onRetry,
    this.isError = false,
  });

  final String message;
  final VoidCallback onRetry;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        if (isError)
          Icon(
            Icons.wifi_off_rounded,
            size: 48.w,
            color: AppColors.primary,
          )
        else
          Image.asset(
            'assets/brand/mascot/prismo_sorry.png',
            width: 150.w,
            
          ),
        SizedBox(height: 16.h),
        Padding(
          padding: EdgeInsets.symmetric(horizontal: 24.w),
          child: Text(
            message,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14.sp,
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
        SizedBox(height: 16.h),
        ElevatedButton(
          onPressed: onRetry,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primary,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14.r),
            ),
          ),
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 10.h),
            child: Text(
              isError ? 'Thử lại' : 'Tải mới',
              style: TextStyle(
                color: Colors.white,
                fontSize: 13.sp,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _JoinedHeader extends StatelessWidget {
  const _JoinedHeader({
    required this.details,
    required this.onLeave,
    required this.onOpenChat,
  });

  final CommunityGroupDetails details;
  final VoidCallback onLeave;
  final VoidCallback onOpenChat;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(26.r),
        border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
      child: Row(
        children: [
          Container(
            height: 62.h,
            width: 62.h,
            decoration: BoxDecoration(
              color: AppColors.primarySoft,
              borderRadius: BorderRadius.circular(20.r),
            ),
            padding: EdgeInsets.all(10.w),
            child: _GroupImage(path: details.group.assetImage, size: 62.w),
          ),
          SizedBox(width: 14.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  details.group.name,
                  style: TextStyle(
                    fontSize: 18.sp,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                SizedBox(height: 6.h),
                Text(
                  '${details.group.memberCount} thành viên • Trưởng nhóm: ${details.group.leaderName}',
                  style: TextStyle(
                    fontSize: 13.sp,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          Align(
            alignment: Alignment.topCenter,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    IconButton(
                      onPressed: onOpenChat,
                      icon: const Icon(Icons.chat_bubble_outline_rounded),
                      color: AppColors.primary,
                    ),
                    IconButton(
                      onPressed: onLeave,
                      icon: const Icon(Icons.logout_rounded),
                      color: AppColors.error,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MilestoneOverview extends StatelessWidget {
  const _MilestoneOverview({required this.details});

  final CommunityGroupDetails details;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(18.w),
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
                        color: AppColors.textPrimary,
                      ),
                    ),
                    SizedBox(height: 4.h),
                    Text(
                      details.currentMilestoneLabel,
                      style: TextStyle(
                        fontSize: 20.sp,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ),
              ),
              Text(
                _formatRemainingTime(details.daysRemaining),
                style: TextStyle(
                  fontSize: 13.sp,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
          SizedBox(height: 18.h),
          _MilestoneIcons(milestones: details.milestones),
          SizedBox(height: 18.h),
          Text(
            '${details.currentPoints}',
            style: TextStyle(
              fontSize: 28.sp,
              fontWeight: FontWeight.w800,
              color: AppColors.primary,
            ),
          ),
          Text(
            'Điểm tích luỹ',
            style: TextStyle(
              fontSize: 13.sp,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

class _MilestoneIcons extends StatelessWidget {
  const _MilestoneIcons({required this.milestones});

  final List<CommunityGroupMilestone> milestones;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: milestones
          .map(
            (milestone) => Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    height: 54.h,
                    margin: EdgeInsets.symmetric(horizontal: 4.w),
                    decoration: BoxDecoration(
                      color: milestone.isReached
                          ? AppColors.primary.withValues(alpha: 0.12)
                          : AppColors.primarySoft,
                      borderRadius: BorderRadius.circular(18.r),
                    ),
                    alignment: Alignment.center,
                    child: Icon(
                      Icons.emoji_events_rounded,
                      color: milestone.isReached
                          ? AppColors.primary
                          : AppColors.textHint,
                    ),
                  ),
                  SizedBox(height: 6.h),
                  Text(
                    '${milestone.requiredPoints}',
                    style: TextStyle(
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w600,
                      color: milestone.isReached
                          ? AppColors.primary
                          : AppColors.textHint,
                    ),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }
}

class _LeaderboardList extends StatelessWidget {
  const _LeaderboardList({required this.members, required this.onMemberTap});

  final List<CommunityGroupMemberScore> members;
  final ValueChanged<CommunityGroupMemberScore> onMemberTap;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: EdgeInsets.only(bottom: 24.h),
      itemCount: members.length,
      // Performance optimizations
      cacheExtent: _leaderboardCacheExtent,
      physics: const BouncingScrollPhysics(),
      separatorBuilder: (_, __) => SizedBox(height: 12.h),
      itemBuilder: (context, index) {
        final member = members[index];
        return RepaintBoundary(
          child: _LeaderboardCard(member: member, onTap: onMemberTap),
        );
      },
    );
  }
}

class _LeaderboardCard extends StatelessWidget {
  const _LeaderboardCard({required this.member, required this.onTap});

  final CommunityGroupMemberScore member;
  final ValueChanged<CommunityGroupMemberScore> onTap;

  Color _backgroundForRank(int rank) {
    switch (rank) {
      case 1:
        return AppColors.tint(const Color(0xFFFFF1AA));
      case 2:
        return AppColors.primarySoft;
      case 3:
        return AppColors.tint(const Color(0xFFFFDEBB));
      default:
        return AppColors.tint(const Color(0xFFE7FFE2));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: _backgroundForRank(member.rank),
        borderRadius: BorderRadius.circular(24.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 16.r,
            offset: Offset(0, 8.h),
          ),
        ],
      ),
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: AppColors.surface,
            radius: 26.r,
            backgroundImage: NetworkImage(member.avatarUrl),
          ),
          SizedBox(width: 14.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      '${member.rank}',
                      style: TextStyle(
                        fontSize: 16.sp,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    SizedBox(width: 10.w),
                    Expanded(
                      child: GestureDetector(
                        onTap: () => onTap(member),
                        child: Text(
                          member.displayName,
                          style: TextStyle(
                            fontSize: 15.sp,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textPrimary,
                            decoration: TextDecoration.underline,
                            decorationStyle: TextDecorationStyle.dotted,
                          ),
                        ),
                      ),
                    ),
                    if (member.isHighlighted)
                      Icon(Icons.star,
                          color: const Color(0xFFF7B500), size: 20.sp),
                  ],
                ),
                SizedBox(height: 6.h),
                Row(
                  children: [
                    Icon(Icons.water_drop,
                        color: AppColors.primary, size: 18.sp),
                    SizedBox(width: 4.w),
                    Text(
                      '${member.weeklyPoints}',
                      style: TextStyle(
                        fontSize: 13.sp,
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          SizedBox(width: 12.w),
          Text(
            '${member.totalPoints}',
            style: TextStyle(
              fontSize: 18.sp,
              fontWeight: FontWeight.w700,
              color: AppColors.primaryDark,
            ),
          ),
        ],
      ),
    );
  }
}

class _StudyGroupCard extends StatelessWidget {
  const _StudyGroupCard({
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
              child: _GroupImage(path: group.assetImage, size: 72.w),
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

class _GroupImage extends StatelessWidget {
  const _GroupImage({required this.path, required this.size});

  final String path;
  final double size;

  @override
  Widget build(BuildContext context) {
    if (path.isEmpty) {
      return Icon(
        Icons.group_outlined,
        size: size * 0.6,
        color: AppColors.textHint,
      );
    }

    final isNetwork = path.startsWith('http');
    final image = isNetwork
        ? Image.network(
            path,
            width: size,
            height: size,
            fit: BoxFit.contain,
            cacheWidth: (size * 2).round(), // Cache optimization
            loadingBuilder: (context, child, loadingProgress) {
              if (loadingProgress == null) return child;
              return SizedBox(
                width: size,
                height: size,
                child: Center(
                  child: CircularProgressIndicator(
                    strokeWidth: 2.0,
                    value: loadingProgress.expectedTotalBytes != null
                        ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                        : null,
                  ),
                ),
              );
            },
            errorBuilder: (context, error, stackTrace) {
              debugPrint('Failed to load group image: $error');
              return Icon(
                Icons.group_outlined,
                size: size * 0.6,
                color: AppColors.textHint,
              );
            },
          )
        : Image.asset(
            path,
            width: size,
            height: size,
            fit: BoxFit.contain,
            cacheWidth: (size * 2).round(), // Cache optimization
            errorBuilder: (context, error, stackTrace) {
              debugPrint('Failed to load asset image: $error');
              return Icon(
                Icons.group_outlined,
                size: size * 0.6,
                color: AppColors.textHint,
              );
            },
          );
    return RepaintBoundary(child: image);
  }
}

class _FeedCard extends StatelessWidget {
  const _FeedCard({required this.post});

  final CommunityPost post;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: _openPostDetail,
      behavior: HitTestBehavior.deferToChild,
      child: Container(
        margin: EdgeInsets.only(bottom: 20.h),
        padding: EdgeInsets.all(16.w),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(32.r),
          border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildHeader(context),
            SizedBox(height: 12.h),
            _buildImage(),
            SizedBox(height: 12.h),
            _buildActions(context),
            _buildCommentPreview(context),
            SizedBox(height: 16.h),
            _buildVocabularySection(context),
            SizedBox(height: 12.h),
            _buildSaveButton(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      children: [
        post.authorAvatar.isEmpty || post.authorMascot?.asAvatar == true
            ? PrismoAvatar(look: post.authorMascot, size: 44.r)
            : CircleAvatar(
                radius: 22.r,
                backgroundImage: _avatarProvider(),
              ),
        SizedBox(width: 12.w),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Align(
                alignment: Alignment.centerLeft,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Flexible(
                      child: GestureDetector(
                        onTap: () => _openAuthorProfile(context),
                        child: Text(
                          post.authorName,
                          style: TextStyle(
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textPrimary,
                            decoration: TextDecoration.underline,
                            decorationStyle: TextDecorationStyle.dotted,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ),
                    if (post.canFollowAuthor) SizedBox(width: 8.w),
                    if (post.canFollowAuthor)
                      Obx(() {
                        if (post.isFollowingAuthor.value) {
                          return const SizedBox.shrink();
                        }
                        return TextButton(
                          onPressed: post.isFollowActionPending.value
                              ? null
                              : () => Get.find<CommunityController>()
                                  .followAuthor(post),
                          style: TextButton.styleFrom(
                            padding: EdgeInsets.symmetric(
                              horizontal: 14.w,
                              vertical: 6.h,
                            ),
                            minimumSize: Size.zero,
                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14.r),
                            ),
                          ),
                          child: post.isFollowActionPending.value
                              ? SizedBox(
                                  height: 16.h,
                                  width: 16.w,
                                  child: const CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(
                                      Colors.white,
                                    ),
                                  ),
                                )
                              : Text(
                                  'Theo dõi',
                                  style: TextStyle(
                                    fontSize: 12.sp,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                        );
                      }),
                  ],
                ),
              ),
              SizedBox(height: 4.h),
              Text(
                post.postedAt,
                style: TextStyle(
                  fontSize: 12.sp,
                  color: AppColors.textHint,
                ),
              ),
            ],
          ),
        ),
        IconButton(
          icon: Icon(
            Icons.more_vert,
            color: AppColors.textSecondary,
            size: 22.sp,
          ),
          onPressed: () => _onPostMenuPressed(context),
          splashRadius: 24.r,
        ),
      ],
    );
  }

  Widget _buildImage() {
    return GestureDetector(
      onTap: _openPostDetail,
      child: Center(
        child: ClipRRect(
          borderRadius: BorderRadius.circular(40.r),
          child: SizedBox(
            width: 261.w,
            height: 261.h,
            child: Stack(
              fit: StackFit.expand,
              children: [
                _buildPostImage(),
                Obx(() {
                  final vocabulary = post.currentVocabulary;
                  return Positioned(
                    top: 16.h,
                    left: 16.w,
                    child: Container(
                      padding:
                          EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.6),
                        borderRadius: BorderRadius.circular(16.r),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            '${vocabulary.label} ',
                            style: TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 12.sp,
                            ),
                          ),
                          Text(
                            vocabulary.confidence.toStringAsFixed(2),
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 12.sp,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }),
              ],
            ),
          ),
        ),
      ),
    );
  }

  ImageProvider _avatarProvider() {
    try {
      final avatar = _normalizeImagePath(post.authorAvatar ?? '');
      if (avatar.isEmpty) {
        return const AssetImage('assets/brand/avatar/avatar_1.png');
      }

      if (avatar.startsWith('data:image')) {
        final commaIndex = avatar.indexOf(',');
        if (commaIndex != -1 && commaIndex < avatar.length - 1) {
          final encoded = avatar.substring(commaIndex + 1);
          try {
            final bytes = base64Decode(encoded);
            return MemoryImage(bytes);
          } catch (_) {
            // fall through to other strategies if base64 decoding fails
          }
        }
      }

      if (avatar.startsWith('http')) {
        return NetworkImage(avatar);
      }

      if (avatar.startsWith('assets/')) {
        return AssetImage(avatar);
      }

      if (avatar.startsWith('file://') || avatar.startsWith('content://')) {
        try {
          final file = File.fromUri(Uri.parse(avatar));
          if (file.existsSync()) {
            return FileImage(file);
          }
        } catch (_) {
          // fall through
        }
      }

      if (avatar.isNotEmpty) {
        final file = File(avatar);
        if (file.existsSync()) {
          return FileImage(file);
        }
      }
    } catch (e) {
      // Log error but don't crash
      debugPrint('Error loading avatar: $e');
    }

    return const AssetImage('assets/brand/avatar/avatar_1.png');
  }

  void _openAuthorProfile(BuildContext context) {
    final controller = Get.find<CommunityController>();
    controller.openPostAuthorProfile(post);
  }

  Widget _buildPostImage() {
    try {
      final url = _normalizeImagePath(post.imageUrl ?? '');

      if (url.isEmpty) {
        return _buildFallbackImage();
      }

      if (url.startsWith('data:image')) {
        final commaIndex = url.indexOf(',');
        if (commaIndex != -1 && commaIndex < url.length - 1) {
          final dataPart = url.substring(commaIndex + 1);
          try {
            final bytes = base64Decode(dataPart);
            return Image.memory(
              bytes,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) => _buildFallbackImage(),
            );
          } catch (_) {
            // fallthrough to other handlers
          }
        }
      }

      if (url.startsWith('http')) {
        return Image.network(
          url,
          fit: BoxFit.cover,
          loadingBuilder: (context, child, loadingProgress) {
            if (loadingProgress == null) return child;
            return Center(
              child: CircularProgressIndicator(
                value: loadingProgress.expectedTotalBytes != null
                    ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                    : null,
              ),
            );
          },
          errorBuilder: (context, error, stackTrace) => _buildFallbackImage(),
        );
      }

      if (url.startsWith('assets/')) {
        return Image.asset(
          url,
          fit: BoxFit.cover,
          errorBuilder: (context, error, stackTrace) => _buildFallbackImage(),
        );
      }

      if (url.startsWith('file://') || url.startsWith('content://')) {
        try {
          final file = File.fromUri(Uri.parse(url));
          if (file.existsSync()) {
            return Image.file(
              file,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) => _buildFallbackImage(),
            );
          }
        } catch (_) {
          // fall through
        }
      }

      if (url.isNotEmpty) {
        final file = File(url);
        if (file.existsSync()) {
          return Image.file(
            file,
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) => _buildFallbackImage(),
          );
        }
      }
    } catch (e) {
      debugPrint('Error loading post image: $e');
    }

    return _buildFallbackImage();
  }

  Widget _buildFallbackImage() {
    return Image.asset(
      'assets/brand/avatar/avatar_1.png',
      fit: BoxFit.cover,
    );
  }

  String _normalizeImagePath(String? input) {
    if (input == null) return '';

    final trimmed = input.trim();
    if (trimmed.isEmpty) {
      return trimmed;
    }

    String stripLeadingSlash(String path) =>
        path.startsWith('/') ? path.substring(1) : path;

    try {
      if (trimmed.startsWith('file://')) {
        try {
          final uri = Uri.parse(trimmed);
          final path = uri.path.isNotEmpty ? uri.path : uri.toFilePath();
          if (path.startsWith('/assets/')) {
            return stripLeadingSlash(path);
          }
          if (path.isNotEmpty) {
            return path;
          }
        } catch (_) {
          final fallback = trimmed.replaceFirst('file://', '');
          if (fallback.startsWith('/assets/')) {
            return stripLeadingSlash(fallback);
          }
          if (fallback.isNotEmpty) {
            return fallback;
          }
        }
      }

      if (trimmed.startsWith('/assets/')) {
        return stripLeadingSlash(trimmed);
      }

      if (trimmed.startsWith('asset://')) {
        final resolved = trimmed.replaceFirst('asset://', '');
        return stripLeadingSlash(resolved);
      }
    } catch (e) {
      debugPrint('Error normalizing image path: $e');
      return trimmed;
    }

    return trimmed;
  }

  Widget _buildActions(BuildContext context) {
    final communityController = Get.find<CommunityController>();
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        Obx(
          () => _ActionItem(
            icon: post.isLiked.value ? Icons.favorite : Icons.favorite_border,
            label: post.likes.value.toString(),
            color: post.isLiked.value
                ? const Color(0xFFFF3A30)
                : AppColors.textSecondary,
            onTap: () => communityController.toggleLike(post),
          ),
        ),
        Obx(() {
          final isExpanded = post.isCommentsExpanded.value;
          return _ActionItem(
            icon: isExpanded ? Icons.chat_bubble : Icons.chat_bubble_outline,
            label: post.comments.value.toString(),
            color:
                isExpanded ? AppColors.primary : AppColors.textSecondary,
            labelColor:
                isExpanded ? AppColors.primary : AppColors.textSecondary,
            onTap: () => communityController.showComments(post),
          );
        }),
        Obx(() {
          final isVocabulary = post.isVocabularyExpanded.value;
          final iconColor = isVocabulary ? AppColors.primary : AppColors.textSecondary;
          return _ActionItem(
            icon: Icons.translate_rounded,
            label: 'Từ vựng',
            color: iconColor,
            labelColor: iconColor,
            onTap: () => communityController.showVocabulary(post),
          );
        }),
        Obx(() {
          final saved = post.isSaved.value;
          final iconColor = saved ? const Color(0xFFFFA800) : AppColors.textSecondary;
          return _ActionItem(
            icon: saved ? Icons.bookmark : Icons.bookmark_border,
            label: saved ? 'Đã lưu' : 'Lưu',
            color: iconColor,
            labelColor: iconColor,
            onTap: () => communityController.toggleSave(post),
          );
        }),
      ],
    );
  }

  Widget _buildCommentPreview(BuildContext context) {
    return Obx(() {
      if (!post.isCommentsExpanded.value) {
        return const SizedBox.shrink();
      }

      final comments = post.commentMessages;
      final previewCount = comments.length < 2 ? comments.length : 2;
      final highlightComments = [
        for (var i = 0; i < previewCount; i++) comments[i],
      ];

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(height: 12.h),
          Container(
            width: double.infinity,
            padding: EdgeInsets.all(16.w),
            decoration: BoxDecoration(
              color: AppColors.primarySoft,
              borderRadius: BorderRadius.circular(20.r),
              border: Border.all(color: AppColors.primaryTint),
            ),
            child: highlightComments.isEmpty
                ? Text(
                    'Chưa có bình luận nào. Hãy chia sẻ cảm nghĩ của bạn nhé!',
                    style: TextStyle(
                      fontSize: 13.sp,
                      color: AppColors.textSecondary,
                    ),
                  )
                : Column(
                    children: [
                      for (var i = 0; i < highlightComments.length; i++) ...[
                        _CommentPreviewString(
                          comment: highlightComments[i],
                        ),
                        if (i < highlightComments.length - 1)
                          SizedBox(height: 12.h),
                      ],
                    ],
                  ),
          ),
          SizedBox(height: 12.h),
          _PrimaryActionButton(
            label: 'Thêm bình luận',
            leadingIcon: Icons.add_comment_rounded,
            onTap: _openPostDetail,
          ),
        ],
      );
    });
  }

  Widget _buildVocabularySection(BuildContext context) {
    final communityController = Get.find<CommunityController>();
    return Obx(() {
      final total = post.vocabularyItems.length;
      if (total == 0) {
        return const SizedBox.shrink();
      }
      if (!post.isVocabularyExpanded.value) {
        return const SizedBox.shrink();
      }
      final rawIndex = post.currentVocabularyIndex.value;
      final currentIndex =
          rawIndex < 0 ? 0 : (rawIndex >= total ? total - 1 : rawIndex);
      final vocabulary = post.vocabularyItems[currentIndex];
      final isSelected = vocabulary.isSelected.value;
      final selectedTopic = vocabulary.topic.value ?? 'chọn chủ đề';

      final borderColor = isSelected
          ? AppColors.primary
          : AppColors.primary.withValues(alpha: 0.6);
      final gradientColors = isSelected
          ? [AppColors.primarySoft, AppColors.primaryTint]
          : [AppColors.primarySoft, AppColors.primarySoft];
      final hasMultiple = total > 1;

      Widget card = Container(
        padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 16.h),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24.r),
          border: Border.all(color: borderColor, width: 1.8),
          color: (gradientColors).first,),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                GestureDetector(
                  onTap: () =>
                      communityController.toggleSelection(post, vocabulary),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    width: 24.w,
                    height: 24.w,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppColors.primary,
                        width: isSelected ? 2.4 : 2,
                      ),
                      color:
                          isSelected ? AppColors.primary : Colors.white,),
                    child: isSelected
                        ? Icon(
                            Icons.check,
                            color: Colors.white,
                            size: 14.sp,
                          )
                        : null,
                  ),
                ),
                SizedBox(width: 10.w),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        vocabulary.headword,
                        style: TextStyle(
                          fontSize: 16.sp,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      if (vocabulary.translation.isNotEmpty) ...[
                        SizedBox(height: 4.h),
                        Text(
                          vocabulary.translation,
                          style: TextStyle(
                            fontSize: 14.sp,
                            color: AppColors.primaryDark,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                      if (vocabulary.phonetic.isNotEmpty) ...[
                        SizedBox(height: 4.h),
                        Text(
                          vocabulary.phonetic,
                          style: TextStyle(
                            fontSize: 12.sp,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                GestureDetector(
                  onTap: () =>
                      communityController.speakWord(vocabulary.headword),
                  child: Container(
                    width: 40.w,
                    height: 40.w,
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(20.r),
                      border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
                    child: Icon(
                      Icons.volume_up_rounded,
                      color: AppColors.primary,
                      size: 22.sp,
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 12.h),
            Row(
              children: [
                Text(
                  'Chủ đề:',
                  style: TextStyle(
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textSecondary,
                  ),
                ),
                SizedBox(width: 8.w),
                GestureDetector(
                  onTap: () => _showTopicPicker(
                      context, communityController, vocabulary),
                  child: Container(
                    padding:
                        EdgeInsets.symmetric(horizontal: 16.w, vertical: 6.h),
                    decoration: BoxDecoration(
                      color: AppColors.primary,
                      borderRadius: BorderRadius.circular(18.r),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          selectedTopic,
                          style: TextStyle(
                            fontSize: 12.sp,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                        SizedBox(width: 6.w),
                        Icon(
                          Icons.keyboard_arrow_down_rounded,
                          color: Colors.white,
                          size: 16.sp,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      );

      return Column(
        children: [
          Stack(
            clipBehavior: Clip.none,
            alignment: Alignment.center,
            children: [
              card,
              if (hasMultiple)
                Positioned(
                  left: -6.w,
                  child: _NavButton(
                    icon: Icons.chevron_left,
                    onTap: currentIndex > 0
                        ? () => communityController.goToPreviousVocabulary(post)
                        : null,
                  ),
                ),
              if (hasMultiple)
                Positioned(
                  right: -6.w,
                  child: _NavButton(
                    icon: Icons.chevron_right,
                    onTap: currentIndex < total - 1
                        ? () => communityController.goToNextVocabulary(post)
                        : null,
                  ),
                ),
            ],
          ),
          if (hasMultiple)
            Padding(
              padding: EdgeInsets.only(top: 10.h),
              child: Text(
                '${currentIndex + 1}/$total',
                style: TextStyle(
                  fontSize: 12.sp,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textSecondary,
                ),
              ),
            ),
        ],
      );
    });
  }

  Widget _buildSaveButton() {
    final communityController = Get.find<CommunityController>();
    return Obx(() {
      if (post.vocabularyItems.isEmpty) {
        return const SizedBox.shrink();
      }
      if (!post.isVocabularyExpanded.value) {
        return const SizedBox.shrink();
      }
      final total = post.vocabularyItems.length;
      final rawIndex = post.currentVocabularyIndex.value;
      final currentIndex =
          rawIndex < 0 ? 0 : (rawIndex >= total ? total - 1 : rawIndex);
      final vocabulary = post.vocabularyItems[currentIndex];
      final isSelected = vocabulary.isSelected.value;

      return _PrimaryActionButton(
        label: 'Lưu từ vựng',
        onTap: () => communityController.saveVocabulary(post, vocabulary),
        active: isSelected,
      );
    });
  }

  void _showTopicPicker(
    BuildContext context,
    CommunityController controller,
    CommunityVocabularyItem vocabulary,
  ) {
    final textController =
        TextEditingController(text: vocabulary.topic.value ?? '');
    String? tempSelection = vocabulary.topic.value;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
      ),
      builder: (sheetContext) {
        final bottomInset = MediaQuery.of(sheetContext).viewInsets.bottom;
        return Padding(
          padding: EdgeInsets.only(
            bottom: bottomInset,
            left: 20.w,
            right: 20.w,
            top: 20.h,
          ),
          child: StatefulBuilder(
            builder: (context, setModalState) {
              return SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Center(
                      child: Container(
                        width: 42.w,
                        height: 4.h,
                        decoration: BoxDecoration(
                          color: AppColors.lineStrong,
                          borderRadius: BorderRadius.circular(2.r),
                        ),
                      ),
                    ),
                    SizedBox(height: 18.h),
                    Center(
                      child: Text(
                        'Chọn chủ đề',
                        style: TextStyle(
                          fontSize: 18.sp,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                    SizedBox(height: 20.h),
                    Text(
                      'Chủ đề gợi ý',
                      style: TextStyle(
                        fontSize: 14.sp,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textSecondary,
                      ),
                    ),
                    SizedBox(height: 12.h),
                    Wrap(
                      spacing: 10.w,
                      runSpacing: 10.h,
                      children: controller.availableTopics.map((topicOption) {
                        final isActive = tempSelection == topicOption;
                        return ChoiceChip(
                          label: Text(
                            topicOption,
                            style: TextStyle(
                              fontSize: 12.sp,
                              fontWeight: FontWeight.w600,
                              color: isActive
                                  ? Colors.white
                                  : AppColors.textPrimary,
                            ),
                          ),
                          selected: isActive,
                          onSelected: (_) {
                            setModalState(() {
                              tempSelection = topicOption;
                              textController.text = topicOption;
                              textController.selection =
                                  TextSelection.collapsed(
                                      offset: topicOption.length);
                            });
                          },
                          selectedColor: AppColors.primary,
                          backgroundColor: AppColors.primarySoft,
                          pressElevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20.r),
                            side: BorderSide(
                              color: isActive
                                  ? AppColors.primary
                                  : AppColors.primaryTint,
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                    SizedBox(height: 24.h),
                    Text(
                      'Hoặc tự nhập chủ đề phù hợp',
                      style: TextStyle(
                        fontSize: 13.sp,
                        fontWeight: FontWeight.w500,
                        color: AppColors.textSecondary,
                      ),
                    ),
                    SizedBox(height: 8.h),
                    TextField(
                      controller: textController,
                      decoration: InputDecoration(
                        hintText: 'Nhập chủ đề...',
                        contentPadding: EdgeInsets.symmetric(
                          horizontal: 16.w,
                          vertical: 12.h,
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16.r),
                          borderSide:
                              BorderSide(color: AppColors.primarySoft),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16.r),
                          borderSide:
                              BorderSide(color: AppColors.primary),
                        ),
                      ),
                    ),
                    SizedBox(height: 20.h),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {
                          try {
                            final manualTopic = textController.text.trim();

                            // Enhanced validation
                            if (manualTopic.isEmpty &&
                                (tempSelection == null ||
                                    tempSelection!.trim().isEmpty)) {
                              Get.snackbar(
                                'Thiếu thông tin',
                                'Hãy chọn hoặc nhập một chủ đề.',
                                snackPosition: SnackPosition.BOTTOM,
                              );
                              return;
                            }

                            final newTopic = manualTopic.isNotEmpty
                                ? manualTopic
                                : tempSelection!;

                            // Topic validation
                            if (newTopic.length < _minTopicLength) {
                              Get.snackbar(
                                'Chủ đề quá ngắn',
                                'Chủ đề phải có ít nhất $_minTopicLength ký tự.',
                                snackPosition: SnackPosition.BOTTOM,
                              );
                              return;
                            }

                            if (newTopic.length > _maxTopicLength) {
                              Get.snackbar(
                                'Chủ đề quá dài',
                                'Chủ đề không được quá $_maxTopicLength ký tự.',
                                snackPosition: SnackPosition.BOTTOM,
                              );
                              return;
                            }

                            controller.updateTopic(vocabulary, newTopic);
                            Navigator.of(sheetContext).pop();
                          } catch (e) {
                            debugPrint('Error updating topic: $e');
                            Get.snackbar(
                              'Lỗi',
                              'Không thể cập nhật chủ đề. Hãy thử lại.',
                              snackPosition: SnackPosition.BOTTOM,
                            );
                          }
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(18.r),
                          ),
                          padding: EdgeInsets.symmetric(vertical: 14.h),
                        ),
                        child: Text(
                          'Áp dụng',
                          style: TextStyle(
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                    SizedBox(height: 20.h),
                  ],
                ),
              );
            },
          ),
        );
      },
    ).whenComplete(() => textController.dispose());
  }

  void _openPostDetail() {
    try {
      if (!Get.isRegistered<CommunityController>()) {
        Get.snackbar(
          'Lỗi',
          'Không thể tải thông tin bài viết. Hãy thử lại sau.',
          snackPosition: SnackPosition.BOTTOM,
        );
        return;
      }

      final communityController = Get.find<CommunityController>();

      // Validate post data
      if (post.id.isEmpty) {
        Get.snackbar(
          'Lỗi',
          'Bài viết không hợp lệ.',
          snackPosition: SnackPosition.BOTTOM,
        );
        return;
      }

      communityController.markPostAsViewed(post);
      Get.to(
        () => const CommunityDetailView(),
        binding: CommunityDetailBinding(),
        arguments: CommunityDetailArguments(post: post),
      );
    } catch (e) {
      debugPrint('Error opening post detail: $e');
      Get.snackbar(
        'Lỗi',
        'Không thể mở chi tiết bài viết. Hãy thử lại sau.',
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }

  void _onPostMenuPressed(BuildContext context) {
    final communityController = Get.find<CommunityController>();
    final isOwner = communityController.isPostOwner(post);
    if (isOwner) {
      _confirmDeletePost(context, communityController);
    } else {
      _showReportSheet(context);
    }
  }

  void _confirmDeletePost(
    BuildContext context,
    CommunityController controller,
  ) {
    Get.defaultDialog(
      title: 'Xoá bài viết',
      middleText: 'Bạn có chắc muốn xoá bài viết này?\nHành động này không thể hoàn tác.',
      textCancel: 'Huỷ',
      textConfirm: 'Xoá',
      confirmTextColor: Colors.white,
      onConfirm: () {
        goBack<void>();
        controller.deletePost(post);
      },
    );
  }

  Future<void> _showReportSheet(BuildContext context) async {
    final communityController = Get.find<CommunityController>();
    const reasons = CommunityController.reportReasons;
    final noteController = TextEditingController();
    final alreadyReported = communityController.hasReportedPost(post.id);
    String selectedReason = reasons.first;

    await Get.bottomSheet<void>(
      StatefulBuilder(
        builder: (sheetContext, setState) {
          final bottomInset = MediaQuery.of(sheetContext).viewInsets.bottom;
          return Container(
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.vertical(top: Radius.circular(32.r)),
            ),
            padding: EdgeInsets.only(
              left: 24.w,
              right: 24.w,
              top: 20.h,
              bottom: bottomInset + 24.h,
            ),
            child: SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
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
                    'Báo cáo vi phạm',
                    style: TextStyle(
                      fontSize: 18.sp,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  SizedBox(height: 14.h),
                  if (alreadyReported)
                    Container(
                      width: double.infinity,
                      padding: EdgeInsets.all(12.w),
                      margin: EdgeInsets.only(bottom: 12.h),
                      decoration: BoxDecoration(
                        color: AppColors.tint(const Color(0xFFFFF3B0)),
                        borderRadius: BorderRadius.circular(16.r),
                        border: Border.all(color: const Color(0xFFFFD57E)),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.info_outline,
                              color: const Color(0xFF8C6E02), size: 20.sp),
                          SizedBox(width: 10.w),
                          Expanded(
                            child: Text(
                              'Bạn đã gửi báo cáo cho bài đăng này. '
                              'Đội ngũ kiểm duyệt sẽ xem xét sớm nhất.',
                              style: TextStyle(
                                fontSize: 13.sp,
                                color: const Color(0xFF6B5600),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ...List<Widget>.generate(
                    reasons.length,
                    (index) {
                      final reason = reasons[index];
                      final isSelected = selectedReason == reason;
                      return Padding(
                        padding: EdgeInsets.symmetric(vertical: 6.h),
                        child: InkWell(
                          onTap: alreadyReported
                              ? null
                              : () {
                                  setState(() => selectedReason = reason);
                                },
                          borderRadius: BorderRadius.circular(16.r),
                          child: Ink(
                            padding: EdgeInsets.symmetric(
                              horizontal: 12.w,
                              vertical: 10.h,
                            ),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(16.r),
                              color: isSelected
                                  ? AppColors.primarySoft
                                  : Colors.white,
                              border: Border.all(
                                color: isSelected
                                    ? AppColors.primary
                                    : AppColors.line,
                                width: 1.2,
                              ),
                            ),
                            child: Row(
                              children: [
                                Container(
                                  width: 20.w,
                                  height: 20.w,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    border: Border.all(
                                      color: isSelected
                                          ? AppColors.primary
                                          : AppColors.textHint,
                                      width: 2,
                                    ),
                                  ),
                                  alignment: Alignment.center,
                                  child: AnimatedContainer(
                                    duration: const Duration(milliseconds: 180),
                                    width: 10.w,
                                    height: 10.w,
                                    decoration: BoxDecoration(
                                      color: isSelected
                                          ? AppColors.primary
                                          : Colors.transparent,
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                ),
                                SizedBox(width: 12.w),
                                Expanded(
                                  child: Text(
                                    reason,
                                    style: TextStyle(
                                      fontSize: 14.sp,
                                      fontWeight: FontWeight.w500,
                                      color: AppColors.textPrimary,
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
                  if (selectedReason == 'Khác') ...[
                    SizedBox(height: 12.h),
                    TextField(
                      controller: noteController,
                      maxLines: 3,
                      enabled: !alreadyReported,
                      decoration: InputDecoration(
                        hintText: 'Mô tả chi tiết hơn...',
                        hintStyle: TextStyle(
                          fontSize: 13.sp,
                          color: AppColors.textHint,
                        ),
                        filled: true,
                        fillColor: AppColors.primarySoft,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18.r),
                          borderSide: BorderSide(
                            color: AppColors.line,
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(18.r),
                          borderSide: BorderSide(
                            color: AppColors.primary,
                            width: 1.4,
                          ),
                        ),
                      ),
                    ),
                  ],
                  SizedBox(height: 22.h),
                  SizedBox(
                    width: double.infinity,
                    height: 52.h,
                    child: ElevatedButton(
                      onPressed: alreadyReported
                          ? null
                          : () {
                              // Enhanced validation
                              if (selectedReason.trim().isEmpty) {
                                Get.snackbar(
                                  'Lỗi',
                                  'Hãy chọn lý do báo cáo.',
                                  snackPosition: SnackPosition.BOTTOM,
                                );
                                return;
                              }

                              if (selectedReason == 'Khác') {
                                final description = noteController.text.trim();
                                if (description.isEmpty) {
                                  Get.snackbar(
                                    'Thiếu thông tin',
                                    'Hãy mô tả chi tiết khi chọn lý do "Khác".',
                                    snackPosition: SnackPosition.BOTTOM,
                                  );
                                  return;
                                }
                                if (description.length < _minReportDescriptionLength) {
                                  Get.snackbar(
                                    'Mô tả quá ngắn',
                                    'Hãy mô tả chi tiết ít nhất $_minReportDescriptionLength ký tự.',
                                    snackPosition: SnackPosition.BOTTOM,
                                  );
                                  return;
                                }
                              }

                              try {
                                Navigator.of(sheetContext).pop();
                                communityController.submitPostReport(
                                  post: post,
                                  reason: selectedReason,
                                  description: selectedReason == 'Khác'
                                      ? noteController.text.trim()
                                      : null,
                                );
                              } catch (e) {
                                debugPrint('Error submitting report: $e');
                                Get.snackbar(
                                  'Lỗi',
                                  'Không thể gửi báo cáo. Hãy thử lại sau.',
                                  snackPosition: SnackPosition.BOTTOM,
                                );
                              }
                            },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: alreadyReported
                            ? AppColors.line
                            : AppColors.error,
                        foregroundColor: Colors.white,
                        disabledForegroundColor: Colors.white,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14.r),
                        ),
                        textStyle: TextStyle(
                          fontSize: 15.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      child: const Text('Báo cáo'),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
    ).whenComplete(() => noteController.dispose());
  }
}

class _NavButton extends StatelessWidget {
  const _NavButton({
    required this.icon,
    this.onTap,
  });

  final IconData icon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    return Material(
      color: AppColors.surface,
      shape: const CircleBorder(),
      elevation: 0,
      child: InkWell(
        onTap: onTap,
        customBorder: const CircleBorder(),
        child: SizedBox(
          width: 38.w,
          height: 38.w,
          child: Icon(
            icon,
            color: enabled ? AppColors.primary : AppColors.textHint,
            size: 20.sp,
          ),
        ),
      ),
    );
  }
}

class _CommentPreviewString extends StatelessWidget {
  const _CommentPreviewString({
    required this.comment,
  });

  final CommunityPostComment comment;

  @override
  Widget build(BuildContext context) {
    final content = comment.content.trim();
    final userName = comment.userName.trim().isNotEmpty
        ? comment.userName.trim()
        : 'Thành viên';
    final initial =
        userName.isNotEmpty ? userName.characters.first.toUpperCase() : 'T';

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        CircleAvatar(
          radius: 18.r,
          backgroundColor: AppColors.primaryTint,
          child: Text(
            initial,
            style: TextStyle(
              fontSize: 13.sp,
              fontWeight: FontWeight.w700,
              color: AppColors.primary,
            ),
          ),
        ),
        SizedBox(width: 12.w),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                userName,
                style: TextStyle(
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              SizedBox(height: 4.h),
              Text(
                content.isNotEmpty ? content : 'Bình luận không có nội dung',
                style: TextStyle(
                  fontSize: 13.sp,
                  color: AppColors.textSecondary,
                  height: 1.3,
                  fontStyle: content.isEmpty ? FontStyle.italic : FontStyle.normal,
                ),
              ),
            ],
          ),
        ),
        SizedBox(width: 12.w),
        Icon(
          Icons.favorite_border,
          color: AppColors.textHint,
          size: 18.sp,
        ),
      ],
    );
  }
}

ImageProvider? _resolveAvatar(String avatarUrl) {
  if (avatarUrl.isEmpty) {
    return null;
  }
  if (avatarUrl.startsWith('http')) {
    return NetworkImage(avatarUrl);
  }
  if (avatarUrl.startsWith('assets/')) {
    return AssetImage(avatarUrl);
  }
  return null;
}

class _ActionItem extends StatelessWidget {
  const _ActionItem({
    required this.icon,
    required this.label,
    required this.color,
    Color? labelColor,
    this.onTap,
  }) : labelColor = labelColor ?? color;

  final IconData icon;
  final String label;
  final Color color;
  final Color labelColor;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Row(
        children: [
          Icon(icon, color: color, size: 22.sp),
          SizedBox(width: 6.w),
          Text(
            label,
            style: TextStyle(
              fontSize: 13.sp,
              color: labelColor,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _PrimaryActionButton extends StatelessWidget {
  const _PrimaryActionButton({
    required this.label,
    this.leadingIcon,
    this.onTap,
    bool? active,
  }) : isActive = active ?? true;

  final String label;
  final IconData? leadingIcon;
  final VoidCallback? onTap;
  final bool isActive;

  @override
  Widget build(BuildContext context) {
    final colors = isActive
        ? [AppColors.primary, AppColors.primary]
        : [AppColors.primaryTint, AppColors.primaryLight];
    final shadowColor =
        isActive ? AppColors.primary : AppColors.primaryLight;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: EdgeInsets.symmetric(vertical: 14.h),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(32.r),
          color: (colors).first,
          boxShadow: [
            BoxShadow(
              color: shadowColor.withValues(alpha: isActive ? 0.3 : 0.18),
              blurRadius: 20.r,
              offset: Offset(0, 12.h),
            ),
          ],),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (leadingIcon != null) ...[
              Icon(leadingIcon, color: Colors.white, size: 18.sp),
              SizedBox(width: 8.w),
            ],
            Text(
              label,
              style: TextStyle(
                fontSize: 16.sp,
                fontWeight: FontWeight.w700,
                color: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
