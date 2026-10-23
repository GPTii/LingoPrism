import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/profile_controller.dart';
import '../../community/controllers/community_controller.dart';
import '../../community_detail/controllers/community_detail_controller.dart';
import '../../../routes/app_pages.dart';
import '../../../core/utils/streak_asset_resolver.dart';
import '../../../core/widgets/app_icon.dart';
import '../../../data/services/auth_service.dart';
import '../../social/social_module.dart';
import 'badges_section.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';
import '../../../core/widgets/show_more.dart';

/// A big tappable tile with a colour icon: Bạn bè, Bài đã lưu.
class _ProfileShortcut extends StatelessWidget {
  const _ProfileShortcut({required this.icon, required this.label, required this.onTap});

  final String icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Material(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16.r),
        child: InkWell(
          borderRadius: BorderRadius.circular(16.r),
          onTap: onTap,
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(16.r), border: Border.all(color: AppColors.line)),
            child: Row(children: [
              AppIcon(icon, size: 30.w),
              SizedBox(width: 10.w),
              Expanded(child: Text(label, style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary))),
            ]),
          ),
        ),
      );
}

class ProfileView extends GetView<ProfileController> {
  const ProfileView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primarySoft,
      appBar: AppBar(
        backgroundColor: AppColors.primarySoft,
        elevation: 0,
        titleSpacing: 20.w,
        title: Text(
          'Trang cá nhân',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 20.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
        actions: [
          IconButton(
            onPressed: controller.loadProfile,
            icon: Icon(Icons.refresh_rounded, color: AppColors.primary),
            tooltip: 'Làm mới',
          ),
          SizedBox(width: 4.w),
        ],
      ),
      body: Obx(() {
        final profileSummary = controller.summary.value;
        final posts = controller.recentPosts.toList();
        final isLoading = controller.isLoading.value;
        final error = controller.errorMessage.value;

        return RefreshIndicator(
          onRefresh: controller.loadProfile,
          color: AppColors.primary,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: EdgeInsets.only(
              left: 20.w,
              right: 20.w,
              bottom: 24.h,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(height: 12.h),
                ProfileHeader(
                  summary: profileSummary,
                  onSettingsTap: () => controller.openSettings(),
                  showFollowButton: false,
                  onFollowToggle: null,
                  isFollowing: false,
                ),
                if (AuthService.to.currentUser?.isKid != true) ...[
                  SizedBox(height: 16.h),
                  const MyIdCard(),
                  SizedBox(height: 10.h),
                  Row(children: [
                    Expanded(child: _ProfileShortcut(icon: 'community', label: 'Bạn bè', onTap: () => Get.toNamed(Routes.friends))),
                    SizedBox(width: 10.w),
                    Expanded(child: _ProfileShortcut(icon: 'bookmark', label: 'Bài đã lưu', onTap: () => Get.toNamed(Routes.savedPosts))),
                  ]),
                ],
                SizedBox(height: 12.h),
                BadgesSection(badges: controller.badges.toList()),
                SizedBox(height: 24.h),
                ProfileOverviewSection(summary: profileSummary),
                SizedBox(height: 12.h),
                // the learner's own numbers: by day, question type, topic, hardest words
                Material(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(16.r),
                  child: ListTile(
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16.r),
                      side: BorderSide(color: AppColors.line),
                    ),
                    leading: Icon(Icons.insights_rounded, color: AppColors.primary),
                    title: Text('Thống kê học tập', style: TextStyle(fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                    subtitle: Text('Tỉ lệ đúng, tiến độ theo chủ đề, từ hay sai', style: TextStyle(color: AppColors.textSecondary)),
                    trailing: Icon(Icons.chevron_right_rounded, color: AppColors.textHint),
                    onTap: () => Get.toNamed(Routes.stats),
                  ),
                ),
                SizedBox(height: 28.h),
                Text(
                  'Các bài đăng gần đây',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 18.sp,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                SizedBox(height: 14.h),
                if (isLoading && posts.isEmpty)
                  Container(
                    padding: EdgeInsets.symmetric(vertical: 40.h),
                    alignment: Alignment.center,
                    child: const CircularProgressIndicator(),
                  )
                else if (posts.isEmpty)
                  Container(
                    width: double.infinity,
                    padding: EdgeInsets.symmetric(vertical: 36.h),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(20.r),
                      border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
                    child: Text(
                      'Chưa có bài đăng nào',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 15.sp,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  )
                else
                  RecentPostsGrid(images: posts),
                if (error.isNotEmpty) ...[
                  SizedBox(height: 20.h),
                  ProfileErrorBanner(message: error),
                ],
              ],
            ),
          ),
        );
      }),
    );
  }
}

class ProfileHeader extends StatelessWidget {
  const ProfileHeader({
    super.key,
    required this.summary,
    required this.onSettingsTap,
    required this.showFollowButton,
    required this.isFollowing,
    this.onFollowToggle,
    this.showSettingsButton = true,
    this.isFollowLoading = false,
  });

  final ProfileSummary summary;
  final VoidCallback onSettingsTap;
  final bool showFollowButton;
  final bool isFollowing;
  final VoidCallback? onFollowToggle;
  final bool showSettingsButton;
  final bool isFollowLoading;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(20.w),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(28.r),
        border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ProfileAvatarImage(url: summary.avatarUrl),
              SizedBox(width: 16.w),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(
                          child: Text(
                            summary.displayName,
                            style: TextStyle(
                              color: AppColors.textPrimary,
                              fontWeight: FontWeight.w700,
                              fontSize: 20.sp,
                            ),
                          ),
                        ),
                        if (showSettingsButton)
                          IconButton(
                            onPressed: onSettingsTap,
                            icon: const Icon(Icons.settings_outlined),
                            color: AppColors.textPrimary,
                            tooltip: 'Chỉnh sửa hồ sơ',
                          )
                        else if (showFollowButton)
                          _FollowButton(
                            isFollowing: isFollowing,
                            isLoading: isFollowLoading,
                            onTap: onFollowToggle,
                          ),
                      ],
                    ),
                    SizedBox(height: 12.h),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                '${summary.posts}',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: AppColors.textPrimary,
                                  fontSize: 16.sp,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            SizedBox(width: 8.w),
                            Expanded(
                              child: Text(
                                '${summary.followers}',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: AppColors.textPrimary,
                                  fontSize: 16.sp,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            SizedBox(width: 8.w),
                            Expanded(
                              child: Text(
                                '${summary.following}',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: AppColors.textPrimary,
                                  fontSize: 16.sp,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ],
                        ),
                        SizedBox(height: 6.h),
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                'Ảnh đăng',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 12.sp,
                                ),
                              ),
                            ),
                            SizedBox(width: 8.w),
                            Expanded(
                              child: Text(
                                'Người theo dõi',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 12.sp,
                                ),
                              ),
                            ),
                            SizedBox(width: 8.w),
                            Expanded(
                              child: Text(
                                'Đang theo dõi',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 12.sp,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class ProfileOverviewSection extends StatelessWidget {
  const ProfileOverviewSection({super.key, required this.summary});

  final ProfileSummary summary;

  @override
  Widget build(BuildContext context) {
    final items = <ProfileOverviewItemData>[
      ProfileOverviewItemData(
        title: 'Rank hiện tại',
        value: summary.rankTitle,
        iconPath: summary.rankIcon,
        background: AppColors.primarySoft,
      ),
      ProfileOverviewItemData(
        title: 'Streak',
        value: summary.streak.toString(),
        iconPath: StreakAssetResolver.assetByValue(summary.streak),
        background: AppColors.tint(const Color(0xFFFFF3E9)),
      ),
      ProfileOverviewItemData(
        title: 'Nhóm',
        value: summary.groupName,
        iconPath: summary.groupIcon,
        background: AppColors.tint(const Color(0xFFEFF8EC)),
      ),
      ProfileOverviewItemData(
        title: 'Kinh nghiệm',
        value: summary.experience.toString(),
        iconPath: 'assets/brand/icons/xp.png',
        background: AppColors.primarySoft,
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Tổng quan',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 18.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
        SizedBox(height: 14.h),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 14.w,
            mainAxisSpacing: 14.h,
            childAspectRatio: 2.05,
          ),
          itemCount: items.length,
          itemBuilder: (_, index) {
            final item = items[index];
            return ProfileOverviewCard(data: item);
          },
        ),
      ],
    );
  }
}

class RecentPostsGrid extends StatelessWidget {
  const RecentPostsGrid({super.key, required this.images});

  final List<String> images;

  @override
  Widget build(BuildContext context) {
    return ShowMore(
      count: images.length,
      limit: 6,
      label: 'Xem thêm ảnh',
      builder: (_, shown) => GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        crossAxisSpacing: 12.w,
        mainAxisSpacing: 12.h,
        childAspectRatio: 1,
      ),
      itemCount: shown,
      itemBuilder: (_, index) {
        final imagePath = images[index];
        return GestureDetector(
          onTap: () => _openPostDetail(imagePath),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16.r),
            child: ProfileAdaptiveImage(imagePath: imagePath),
          ),
        );
      },
    ),
    );
  }

  void _openPostDetail(String imagePath) {
    CommunityPost? post;
    if (Get.isRegistered<CommunityController>()) {
      final community = Get.find<CommunityController>();
      for (final p in community.posts) {
        if (p.imageUrl == imagePath) {
          post = p;
          break;
        }
      }
    }
    if (post == null) {
      // Not found in memory: silently ignore or navigate to community tab
      Get.snackbar('Không tìm thấy bài', 'Bài đăng đã bị xoá hoặc chưa tải.');
      return;
    }
    Get.toNamed(
      Routes.communityDetail,
      arguments: CommunityDetailArguments(post: post),
    );
  }
}

class ProfileOverviewCard extends StatelessWidget {
  const ProfileOverviewCard({super.key, required this.data});

  final ProfileOverviewItemData data;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(22.r),
        border: Border.all(color: data.background, width: 2),),
      child: Row(
        children: [
          Container(
            width: 42.w,
            height: 42.w,
            decoration: BoxDecoration(
              color: data.background,
              borderRadius: BorderRadius.circular(16.r),
            ),
            padding: EdgeInsets.all(6.w),
            child: ProfileAdaptiveImage(imagePath: data.iconPath),
          ),
          SizedBox(width: 12.w),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  data.title,
                  style: TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w500,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                SizedBox(height: 4.h),
                Text(
                  data.value,
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15.sp,
                    fontWeight: FontWeight.w700,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class ProfileAvatarImage extends StatelessWidget {
  const ProfileAvatarImage({super.key, this.url});

  final String? url;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(22.r),
      child: Container(
        width: 84.w,
        height: 84.w,
        color: AppColors.primarySoft,
        child: _buildImage(),
      ),
    );
  }

  Widget _buildImage() {
    const placeholder = 'assets/brand/avatar/avatar_1.png';
    if (url == null || url!.isEmpty) {
      return Image.asset(placeholder, fit: BoxFit.cover);
    }
    final resolved = _resolveAvatarPath(url!);
    if (resolved.startsWith('http')) {
      return Image.network(
        resolved,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) =>
            Image.asset(placeholder, fit: BoxFit.cover),
      );
    }
    if (resolved.startsWith('assets/')) {
      return Image.asset(
        resolved,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) => Image.asset(placeholder, fit: BoxFit.cover),
      );
    }

    if (resolved.startsWith('content://') || resolved.startsWith('file://')) {
      try {
        final file = File.fromUri(Uri.parse(resolved));
        return Image.file(
          file,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) =>
              Image.asset(placeholder, fit: BoxFit.cover),
        );
      } catch (_) {
        return Image.asset(placeholder, fit: BoxFit.cover);
      }
    }

    // Local file path
    return Image.file(
      File(resolved),
      fit: BoxFit.cover,
      errorBuilder: (_, __, ___) => Image.asset(placeholder, fit: BoxFit.cover),
    );
  }

  String _resolveAvatarPath(String input) {
    final trimmed = input.trim();
    if (trimmed.isEmpty) {
      return trimmed;
    }

    String stripLeadingSlash(String path) =>
        path.startsWith('/') ? path.substring(1) : path;

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

    return trimmed;
  }
}

class _FollowButton extends StatelessWidget {
  const _FollowButton({
    required this.isFollowing,
    required this.isLoading,
    required this.onTap,
  });

  final bool isFollowing;
  final bool isLoading;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final borderRadius = BorderRadius.circular(22.r);
    return SizedBox(
      width: 118.w,
      height: 40.h,
      child: DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: borderRadius,
          color: isFollowing ? AppColors.primarySoft : AppColors.primary,
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: isLoading ? null : onTap,
            borderRadius: borderRadius,
            child: Center(
              child: isLoading
                  ? SizedBox(
                      height: 16.h,
                      width: 16.h,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          isFollowing
                              ? AppColors.primary
                              : Colors.white,
                        ),
                      ),
                    )
                  : Text(
                      isFollowing ? 'Đang theo dõi' : 'Theo dõi',
                      style: TextStyle(
                        color:
                            isFollowing ? AppColors.primary : Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 14.sp,
                      ),
                    ),
            ),
          ),
        ),
      ),
    );
  }
}

class ProfileAdaptiveImage extends StatelessWidget {
  const ProfileAdaptiveImage({super.key, required this.imagePath});

  final String imagePath;

  @override
  Widget build(BuildContext context) {
    final trimmedPath = imagePath.trim();
    if (trimmedPath.isEmpty) {
      return const SizedBox.shrink();
    }
    if (trimmedPath.startsWith('data:image')) {
      final commaIndex = trimmedPath.indexOf(',');
      if (commaIndex != -1 && commaIndex < trimmedPath.length - 1) {
        try {
          final bytes = base64Decode(trimmedPath.substring(commaIndex + 1));
          return Image.memory(bytes, fit: BoxFit.cover);
        } catch (_) {
          // fall through
        }
      }
    }
    if (trimmedPath.startsWith('http')) {
      return Image.network(
        trimmedPath,
        fit: BoxFit.cover,
        errorBuilder: (_, __, ___) {
          return Image.asset(
            'assets/brand/mascot/prismo_ok.png',
            fit: BoxFit.cover,
          );
        },
      );
    }
    if (trimmedPath.startsWith('assets/')) {
      return Image.asset(
        trimmedPath,
        fit: BoxFit.cover,
      );
    }
    return Image.file(
      File(trimmedPath),
      fit: BoxFit.cover,
      errorBuilder: (_, __, ___) => Image.asset(
        'assets/brand/mascot/prismo_ok.png',
        fit: BoxFit.cover,
      ),
    );
  }
}

class ProfileOverviewItemData {
  const ProfileOverviewItemData({
    required this.title,
    required this.value,
    required this.iconPath,
    required this.background,
  });

  final String title;
  final String value;
  final String iconPath;
  final Color background;
}

class ProfileErrorBanner extends StatelessWidget {
  const ProfileErrorBanner({super.key, required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: AppColors.tint(const Color(0xFFFFF2F2)),
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: const Color(0xFFFF6B6B)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Color(0xFFE63946)),
          SizedBox(width: 12.w),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: const Color(0xFFE63946),
                fontSize: 13.sp,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
