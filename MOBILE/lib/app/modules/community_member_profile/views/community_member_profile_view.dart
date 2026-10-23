import '../../../core/widgets/prismo_avatar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../profile/controllers/profile_controller.dart';
import '../../profile/views/profile_view.dart';
import '../controllers/community_member_profile_controller.dart';
import '../../messages/messages_module.dart';
import '../../social/social_module.dart';
import '../../../data/models/api/social.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

class CommunityMemberProfileView
    extends GetView<CommunityMemberProfileController> {
  const CommunityMemberProfileView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primarySoft,
      appBar: AppBar(
        backgroundColor: AppColors.primarySoft,
        elevation: 0,
        leading: IconButton(
          onPressed: goBack,
          icon: Icon(Icons.arrow_back_ios_new_rounded,
              color: AppColors.textPrimary),
        ),
        titleSpacing: 0,
        actions: [
          Obx(() => controller.userId == 0 || !controller.showFollowButton.value && !controller.blocked.value
              ? const SizedBox()
              : PopupMenuButton<String>(
                  icon: Icon(Icons.more_vert_rounded, color: AppColors.textPrimary),
                  onSelected: (v) => v == 'report' ? controller.report() : controller.toggleBlock(),
                  itemBuilder: (_) => [
                    PopupMenuItem(value: 'block', child: Text(controller.blocked.value ? 'Bỏ chặn' : 'Chặn người này')),
                    const PopupMenuItem(value: 'report', child: Text('Báo cáo')),
                  ],
                )),
        ],
        title: Text(
          'Trang cá nhân',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 20.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      body: Obx(() {
        final ProfileSummary summary = controller.summary.value;
        final posts = controller.recentPosts.toList();
        final isFollowing = controller.isFollowing.value;
        final isFollowLoading = controller.isFollowLoading.value;
        final showFollowButton = controller.showFollowButton.value;

        return SingleChildScrollView(
          padding: EdgeInsets.only(
            left: 20.w,
            right: 20.w,
            bottom: 24.h,
            top: 16.h,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ProfileHeader(
                summary: summary,
                onSettingsTap: () {},
                showFollowButton: showFollowButton,
                isFollowing: isFollowing,
                onFollowToggle: showFollowButton ? controller.toggleFollow : null,
                showSettingsButton: false,
                isFollowLoading: isFollowLoading,
              ),
              SizedBox(height: 12.h),
              Row(children: [
                Expanded(
                  child: Row(children: [
                    if (controller.publicId.value.isNotEmpty) ...[
                      Text('ID ${controller.publicId.value}',
                          style: TextStyle(fontSize: 13.sp, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
                      CopyIdButton(id: controller.publicId.value),
                      Text('·  ', style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
                    ],
                    Flexible(
                      child: Text('${controller.friends.value} bạn bè',
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(fontSize: 13.sp, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
                    ),
                  ]),
                ),
                if (showFollowButton && controller.friendStatus.value != FriendStatus.incoming)
                  FriendButton(
                    userId: controller.userId,
                    name: summary.displayName,
                    status: controller.friendStatus.value,
                    requestId: controller.friendRequestId.value,
                    onChanged: (_) => controller.load(),
                  ),
              ]),
              if (showFollowButton && controller.friendStatus.value == FriendStatus.incoming) ...[
                SizedBox(height: 12.h),
                Container(
                  width: double.infinity,
                  padding: EdgeInsets.all(14.w),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(16.r),
                    border: Border.all(color: AppColors.primaryTint),
                  ),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('${summary.displayName} muốn kết bạn với bạn',
                        style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                    if (controller.friendMessage.value.isNotEmpty)
                      Padding(
                        padding: EdgeInsets.only(top: 4.h),
                        child: Text('“${controller.friendMessage.value}”', style: TextStyle(fontSize: 13.sp, color: AppColors.textPrimary)),
                      ),
                    SizedBox(height: 10.h),
                    FriendButton(
                      userId: controller.userId,
                      name: summary.displayName,
                      status: FriendStatus.incoming,
                      requestId: controller.friendRequestId.value,
                      onChanged: (_) => controller.load(),
                    ),
                  ]),
                ),
              ],
              if (controller.canMessage.value) ...[
                SizedBox(height: 12.h),
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () => MessagesRepository.openWith(controller.userId),
                    icon: const Icon(Icons.chat_bubble_outline_rounded),
                    label: const Text('Nhắn tin'),
                  ),
                ),
              ],
              SizedBox(height: 24.h),
              ProfileOverviewSection(summary: summary),
              if (controller.mascot.value != null) ...[
                SizedBox(height: 20.h),
                Row(children: [
                  PrismoAvatar(look: controller.mascot.value, size: 96.w, square: true),
                  SizedBox(width: 14.w),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text('Prismo của ${summary.displayName}', style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
                      Text(controller.mascot.value!.name,
                          style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
                    ]),
                  ),
                ]),
              ],
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
              if (posts.isEmpty)
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
            ],
          ),
        );
      }),
    );
  }
}
