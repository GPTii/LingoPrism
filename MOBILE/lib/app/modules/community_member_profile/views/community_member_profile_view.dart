import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../profile/controllers/profile_controller.dart';
import '../../profile/views/profile_view.dart';
import '../controllers/community_member_profile_controller.dart';

class CommunityMemberProfileView
    extends GetView<CommunityMemberProfileController> {
  const CommunityMemberProfileView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE6F9FF),
      appBar: AppBar(
        backgroundColor: const Color(0xFFE6F9FF),
        elevation: 0,
        leading: IconButton(
          onPressed: Get.back,
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              color: Color(0xFF0B1D28)),
        ),
        titleSpacing: 0,
        title: Text(
          'Trang cá nhân',
          style: TextStyle(
            color: const Color(0xFF0B1D28),
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
              SizedBox(height: 24.h),
              ProfileOverviewSection(summary: summary),
              SizedBox(height: 28.h),
              Text(
                'Các bài đăng gần đây',
                style: TextStyle(
                  color: const Color(0xFF0B1D28),
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
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20.r),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.04),
                        blurRadius: 12.r,
                        offset: Offset(0, 6.h),
                      ),
                    ],
                  ),
                  child: Text(
                    'Chưa có bài đăng nào',
                    style: TextStyle(
                      color: const Color(0xFF60718C),
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
