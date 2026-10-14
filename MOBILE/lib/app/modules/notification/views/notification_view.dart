import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/notification_controller.dart';
import '../../../core/theme/app_widgets.dart';
import '../../../data/models/notification_item.dart';

class NotificationView extends GetView<NotificationController> {
  const NotificationView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE5FFFD),
      appBar: AppBar(
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: () => Get.back(),
        ),
        title: Text(
          'Thông báo',
          style: TextStyle(
            color: Colors.black,
            fontSize: 24.sp,
            fontWeight: FontWeight.bold,
          ),
        ),
        actions: [
          Obx(() {
            final hasUnread =
                controller.notifications.any((element) => !element.isRead);
            if (!hasUnread) {
              return const SizedBox.shrink();
            }
            return TextButton(
              onPressed: controller.markAllAsRead,
              child: Text(
                'Đánh dấu đã đọc',
                style: TextStyle(
                  color: Colors.black87,
                  fontSize: 14.sp,
                ),
              ),
            );
          }),
        ],
      ),
      body: Obx(() {
        if (controller.isLoading.value) {
          return const Center(
            child: CircularProgressIndicator(),
          );
        }

        final error = controller.error.value;
        if (error != null && error.isNotEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.error_outline,
                  size: 48.w,
                  color: Colors.red.shade300,
                ),
                SizedBox(height: 16.h),
                Text(
                  error,
                  style: TextStyle(
                    fontSize: 16.sp,
                    color: Colors.black54,
                  ),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 16.h),
                TextButton(
                  onPressed: () => controller.loadNotifications(),
                  child: Text(
                    'Thử lại',
                    style: TextStyle(
                      fontSize: 14.sp,
                      color: const Color(0xFF1CB0F6),
                    ),
                  ),
                ),
              ],
            ),
          );
        }

        if (controller.notifications.isEmpty) {
          return Center(
            child: Text(
              'Chưa có thông báo',
              style: TextStyle(
                fontSize: 16.sp,
                color: Colors.black54,
              ),
            ),
          );
        }

        final notifications = controller.notifications;
        return RefreshIndicator(
          onRefresh: () => controller.loadNotifications(),
          color: const Color(0xFF1CB0F6),
          backgroundColor: Colors.white,
          child: ListView.builder(
            padding: EdgeInsets.all(20.w),
            itemCount: notifications.length,
            // Use physics for better scroll performance
            physics: const BouncingScrollPhysics(
              parent: AlwaysScrollableScrollPhysics(),
            ),
            // Cache extent for smooth scrolling
            cacheExtent: 500,
            itemBuilder: (context, index) {
              final notification = notifications[index];
              return RepaintBoundary(
                child: Padding(
                  padding: EdgeInsets.only(bottom: 12.h),
                  child: _buildNotificationCard(notification),
                ),
              );
            },
          ),
        );
      }),
    );
  }

  Widget _buildNotificationCard(NotificationItem notification) {
    // Cache expensive calculations
    final isFollow = notification.type == NotificationType.follow;
    final opacity = notification.isRead ? 0.65 : 1.0;

    final card = isFollow
        ? _buildFollowCard(notification)
        : _buildDefaultCard(notification);

    return GestureDetector(
      onTap: () => controller.onNotificationTap(notification),
      child: AnimatedOpacity(
        duration: const Duration(milliseconds: 200),
        opacity: opacity,
        child: card,
      ),
    );
  }

  Widget _buildFollowCard(NotificationItem notification) {
    final imagePath = _resolveImagePath(notification);
    final fallbackAsset = _fallbackAsset(notification);
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: AppWidgets.questGradientDecoration(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (imagePath != null)
                _buildNotificationImage(
                  imagePath,
                  fallbackPath: fallbackAsset,
                  width: 43.w,
                  height: 43.h,
                ),
              SizedBox(width: 12.w),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            notification.title,
                            style: TextStyle(
                              fontSize: 14.sp,
                              fontWeight: FontWeight.bold,
                              color: Colors.black87,
                            ),
                          ),
                        ),
                        SizedBox(width: 8.w),
                        _buildUnreadDot(notification.isRead),
                      ],
                    ),
                    SizedBox(height: 4.h),
                    Text(
                      notification.formattedDate,
                      style: TextStyle(
                        fontSize: 12.sp,
                        color: Colors.black54,
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(width: 12.w),
              if (notification.hasAction)
                AppWidgets.actionButton(
                  text: notification.actionText ?? 'Xem',
                  onPressed: () => controller.onActionTap(notification),
                ),
            ],
          ),
          if (notification.subtitle != null) ...[
            SizedBox(height: 12.h),
            Text(
              notification.subtitle!,
              style: TextStyle(
                fontSize: 12.sp,
                color: Colors.black87,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDefaultCard(NotificationItem notification) {
    final imagePath = _resolveImagePath(notification);
    final fallbackAsset = _fallbackAsset(notification);
    return Container(
      padding: EdgeInsets.all(12.w),
      decoration: AppWidgets.questGradientDecoration(),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (imagePath != null)
            _buildNotificationImage(
              imagePath,
              fallbackPath: fallbackAsset,
              width: 70.h,
              height: 70.h,
            ),
          SizedBox(width: 12.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        notification.title,
                        style: TextStyle(
                          fontSize: 14.sp,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                    SizedBox(width: 8.w),
                    _buildUnreadDot(notification.isRead),
                  ],
                ),
                SizedBox(height: 6.h),
                Text(
                  notification.formattedDate,
                  style: TextStyle(
                    fontSize: 12.sp,
                    color: Colors.black54,
                  ),
                ),
                if (notification.subtitle != null) ...[
                  SizedBox(height: 8.h),
                  Text(
                    notification.subtitle!,
                    style: TextStyle(
                      fontSize: 12.sp,
                      color: Colors.black87,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUnreadDot(bool isRead) {
    if (isRead) {
      return const SizedBox.shrink();
    }
    return Container(
      width: 10.w,
      height: 10.w,
      decoration: const BoxDecoration(
        color: Color(0xFF00AFA0),
        shape: BoxShape.circle,
      ),
    );
  }

  Widget _buildNotificationImage(
    String path, {
    String? fallbackPath,
    double? width,
    double? height,
  }) {
    // Safety check for empty path
    if (path.trim().isEmpty) {
      if (fallbackPath != null && fallbackPath.trim().isNotEmpty) {
        return _buildNotificationImage(
          fallbackPath,
          width: width,
          height: height,
        );
      }
      return _buildPlaceholderImage(width, height);
    }

    final isNetwork = path.startsWith('http');
    final resolvedHeight = height ?? width ?? 50.h;
    final resolvedWidth = width ?? resolvedHeight;
    final borderRadius = BorderRadius.circular(12.r);

    final imageWidget = isNetwork
        ? Image.network(
            path,
            width: resolvedWidth,
            height: resolvedHeight,
            fit: BoxFit.cover,
            loadingBuilder: (context, child, loadingProgress) {
              if (loadingProgress == null) return child;
              return SizedBox(
                width: resolvedWidth,
                height: resolvedHeight,
                child: Center(
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    value: loadingProgress.expectedTotalBytes != null
                        ? loadingProgress.cumulativeBytesLoaded /
                            loadingProgress.expectedTotalBytes!
                        : null,
                  ),
                ),
              );
            },
            errorBuilder: (_, __, ___) => fallbackPath != null
                ? _buildNotificationImage(
                    fallbackPath,
                    width: width,
                    height: height,
                  )
                : _buildErrorImage(width, height),
          )
        : Image.asset(
            path,
            width: resolvedWidth,
            height: resolvedHeight,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => fallbackPath != null
                ? _buildNotificationImage(
                    fallbackPath,
                    width: width,
                    height: height,
                  )
                : _buildErrorImage(width, height),
          );

    return ClipRRect(
      borderRadius: borderRadius,
      child: imageWidget,
    );
  }

  Widget _buildPlaceholderImage(double? width, double? height) {
    final resolvedHeight = height ?? width ?? 50.h;
    final resolvedWidth = width ?? resolvedHeight;
    return Container(
      width: resolvedWidth,
      height: resolvedHeight,
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Icon(
        Icons.image,
        size: resolvedWidth * 0.5,
        color: Colors.grey.shade400,
      ),
    );
  }

  Widget _buildErrorImage(double? width, double? height) {
    final resolvedHeight = height ?? width ?? 50.h;
    final resolvedWidth = width ?? resolvedHeight;
    return Container(
      width: resolvedWidth,
      height: resolvedHeight,
      decoration: BoxDecoration(
        color: Colors.grey.shade200,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Icon(
        Icons.broken_image,
        size: resolvedWidth * 0.5,
        color: Colors.grey.shade400,
      ),
    );
  }

  String? _resolveImagePath(NotificationItem notification) {
    final path = notification.imagePath;
    if (path != null && path.trim().isNotEmpty) {
      return path;
    }
    final fallback = _fallbackAsset(notification);
    if (fallback != null && fallback.trim().isNotEmpty) return fallback;
    return null;
  }

  String? _fallbackAsset(NotificationItem notification) {
    if (notification.type == NotificationType.follow) {
      return 'assets/images/chimcanhcut/chim_xinchao.png';
    }
    if (notification.type == NotificationType.postReaction) {
      return 'assets/images/chimcanhcut/chim_yeu.png';
    }
    if (notification.type == NotificationType.postComment) {
      return 'assets/images/chimcanhcut/chim_hocnhom.png';
    }
    return null;
  }
}
