import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/theme/app_colors.dart';
import '../../community/controllers/community_controller.dart';
import '../controllers/community_detail_controller.dart';
import 'package:lingoprism/app/core/navigation/back.dart';
import 'package:lingoprism/app/core/widgets/sticker_picker.dart';

const int _minReportDescriptionLength = 10;

class CommunityDetailView extends GetView<CommunityDetailController> {
  const CommunityDetailView({super.key});

  @override
  Widget build(BuildContext context) {
    final post = controller.post;
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: const IconButton(
          icon: Icon(Icons.arrow_back_ios_new),
          onPressed: goBack,
        ),
        title: Text(
          post.authorName,
          style: TextStyle(
            fontSize: 16.sp,
            fontWeight: FontWeight.w600,
            color: AppColors.textPrimary,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.more_vert),
            onPressed: () => _onMorePressed(context, post),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(20.w),
        child: RepaintBoundary(
          child: _FeedCard(post: post),
        ),
      ),
    );
  }

  void _onMorePressed(BuildContext context, CommunityPost post) {
    if (!Get.isRegistered<CommunityController>()) return;
    final communityController = Get.find<CommunityController>();
    final isOwner = communityController.isPostOwner(post);
    if (isOwner) {
      _confirmDeletePost(context, communityController, post);
    } else {
      _showReportSheet(context, communityController, post);
    }
  }

  Future<void> _confirmDeletePost(
    BuildContext context,
    CommunityController controller,
    CommunityPost post,
  ) async {
    final confirmed = await Get.dialog<bool>(
      AlertDialog(
        title: const Text('Xoá bài viết'),
        content: const Text(
          'Bạn có chắc muốn xoá bài viết này? Hành động này không thể hoàn tác.',
        ),
        actions: [
          TextButton(
            onPressed: () => goBack(result: false),
            child: const Text('Huỷ'),
          ),
          TextButton(
            onPressed: () => goBack(result: true),
            child: const Text(
              'Xoá',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
      barrierDismissible: false,
    );

    if (confirmed == true) {
      await controller.deletePost(post);
      if (Get.isBottomSheetOpen ?? false) {
        goBack<void>();
      }
      goBack<void>();
    }
  }

  Future<void> _showReportSheet(
    BuildContext context,
    CommunityController communityController,
    CommunityPost post,
  ) async {
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
                                if (description.length <
                                    _minReportDescriptionLength) {
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

class _PostImage extends StatelessWidget {
  const _PostImage({required this.imageUrl});

  final String imageUrl;

  @override
  Widget build(BuildContext context) {
    Widget buildImageWidget() {
      if (imageUrl.startsWith('data:image')) {
        final commaIndex = imageUrl.indexOf(',');
        if (commaIndex != -1 && commaIndex < imageUrl.length - 1) {
          final dataPart = imageUrl.substring(commaIndex + 1);
          try {
            final bytes = base64Decode(dataPart);
            return Image.memory(
              bytes,
              width: double.infinity,
              fit: BoxFit.cover,
              frameBuilder: (context, child, frame, wasSynchronouslyLoaded) {
                if (wasSynchronouslyLoaded) return child;
                return AnimatedOpacity(
                  opacity: frame == null ? 0 : 1,
                  duration: const Duration(milliseconds: 200),
                  child: child,
                );
              },
            );
          } catch (e) {
            // Log error and fall through to fallback image
            debugPrint('Error decoding base64 image: $e');
          }
        }
      }
      if (imageUrl.startsWith('http')) {
        return Image.network(
          imageUrl,
          width: double.infinity,
          fit: BoxFit.cover,
          loadingBuilder: (context, child, loadingProgress) {
            if (loadingProgress == null) return child;
            return Center(
              child: CircularProgressIndicator(
                value: loadingProgress.expectedTotalBytes != null
                    ? loadingProgress.cumulativeBytesLoaded /
                        loadingProgress.expectedTotalBytes!
                    : null,
              ),
            );
          },
          errorBuilder: (context, error, stackTrace) {
            debugPrint('Error loading network image: $error');
            return _buildFallbackImage();
          },
        );
      }
      if (imageUrl.startsWith('assets/')) {
        return Image.asset(
          imageUrl,
          width: double.infinity,
          fit: BoxFit.cover,
          errorBuilder: (context, error, stackTrace) {
            debugPrint('Error loading asset image: $error');
            return _buildFallbackImage();
          },
        );
      }
      if (imageUrl.isNotEmpty) {
        final file = File(imageUrl);
        try {
          if (file.existsSync()) {
            return Image.file(
              file,
              width: double.infinity,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) {
                debugPrint('Error loading file image: $error');
                return _buildFallbackImage();
              },
            );
          }
        } catch (e) {
          debugPrint('Error accessing file: $e');
        }
      }
      return _buildFallbackImage();
    }

    return RepaintBoundary(child: buildImageWidget());
  }

  Widget _buildFallbackImage() {
    return Image.asset(
      'assets/brand/avatar/avatar_1.png',
      width: double.infinity,
      fit: BoxFit.cover,
      errorBuilder: (context, error, stackTrace) {
        return Container(
          width: double.infinity,
          height: 200,
          color: AppColors.lineStrong,
          child: Icon(
            Icons.error_outline,
            size: 50,
            color: AppColors.textHint,
          ),
        );
      },
    );
  }
}

class _AvatarImageProvider {
  static ImageProvider from(String avatar) {
    if (avatar.startsWith('data:image')) {
      final commaIndex = avatar.indexOf(',');
      if (commaIndex != -1 && commaIndex < avatar.length - 1) {
        final encoded = avatar.substring(commaIndex + 1);
        try {
          final bytes = base64Decode(encoded);
          return MemoryImage(bytes);
        } catch (_) {
          // Ignore decoding error and fall through to next strategy.
        }
      }
    }
    if (avatar.startsWith('http')) {
      return NetworkImage(avatar);
    }
    if (avatar.startsWith('assets/')) {
      return AssetImage(avatar);
    }
    if (avatar.isNotEmpty) {
      final file = File(avatar);
      if (file.existsSync()) {
        return FileImage(file);
      }
    }
    return const AssetImage('assets/brand/avatar/avatar_1.png');
  }
}

class _FeedCard extends StatelessWidget {
  const _FeedCard({required this.post});

  final CommunityPost post;

  @override
  Widget build(BuildContext context) {
    // Safe access to vocabulary items with comprehensive validation
    final allVocabularyItems = post.vocabularyItems ?? <CommunityVocabularyItem>[];
    final vocabularyItems = allVocabularyItems
        .where((item) {
          if (item.headword.isEmpty) return false;
          final trimmedHeadword = item.headword.trim();
          return trimmedHeadword.isNotEmpty &&
                 trimmedHeadword.toLowerCase() != 'từ vựng' &&
                 trimmedHeadword.length > 1; // Avoid single character words
        })
        .toList(growable: false);

    final primaryVocabulary =
        vocabularyItems.isNotEmpty ? vocabularyItems.first : null;
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20.r),
        border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
      padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 20.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _Header(post: post),
          SizedBox(height: 18.h),
          ClipRRect(
            borderRadius: BorderRadius.circular(26.r),
            child: Stack(
              children: [
                AspectRatio(
                  aspectRatio: 1,
                  child: _PostImage(imageUrl: post.imageUrl),
                ),
                if (primaryVocabulary != null)
                  Positioned(
                    left: 16.w,
                    top: 16.h,
                    child: _VocabularyTag(item: primaryVocabulary),
                ),
              ],
            ),
          ),
          SizedBox(height: 16.h),
          _ActionRow(post: post),
          if (vocabularyItems.isNotEmpty) ...[
            SizedBox(height: 22.h),
            _DetectedVocabularyList(items: vocabularyItems, post: post),
          ],
          SizedBox(height: 24.h),
          _CommentsSection(post: post),
          SizedBox(height: 16.h),
          _CommentComposer(post: post),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.post});

  final CommunityPost post;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        CircleAvatar(
          radius: 24.r,
          backgroundImage: _AvatarImageProvider.from(post.authorAvatar),
        ),
        SizedBox(width: 12.w),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              post.authorName,
              style: TextStyle(
                fontSize: 16.sp,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
            SizedBox(height: 4.h),
            Text(
              post.postedAt,
              style: TextStyle(
                fontSize: 12.sp,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _ActionRow extends StatelessWidget {
  const _ActionRow({required this.post});

  final CommunityPost post;

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<CommunityController>();
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 14.h),
      decoration: BoxDecoration(
        color: AppColors.primarySoft,
        borderRadius: BorderRadius.circular(24.r),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Obx(
            () => _StatButton(
              icon: post.isLiked.value ? Icons.favorite : Icons.favorite_border,
              color: post.isLiked.value ? AppColors.heartRed : AppColors.textSecondary,
              label: '${post.likes.value}',
              onTap: () => controller.toggleLike(post),
            ),
          ),
          Obx(
            () => _StatButton(
              icon: Icons.chat_bubble_outline,
              color: AppColors.primary,
              label: '${post.comments.value}',
              onTap: () => controller.showComments(post),
            ),
          ),
          Obx(
            () => _StatButton(
              icon: Icons.translate_rounded,
              color: post.isVocabularyExpanded.value ? AppColors.primary : AppColors.textSecondary,
              label: 'Từ vựng',
              onTap: () => controller.showVocabulary(post),
            ),
          ),
          Obx(
            () => _StatButton(
              icon: post.isSaved.value ? Icons.bookmark : Icons.bookmark_border,
              color: post.isSaved.value ? const Color(0xFFFFA800) : AppColors.textSecondary,
              label: post.isSaved.value ? 'Đã lưu' : 'Lưu',
              onTap: () => controller.toggleSave(post),
            ),
          ),
        ],
      ),
    );
  }
}


class _CommentsSection extends StatelessWidget {
  const _CommentsSection({required this.post});

  final CommunityPost post;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Bình luận nổi bật',
          style: TextStyle(
            fontSize: 15.sp,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        SizedBox(height: 12.h),
        Obx(() {
          final commentMessages = post.commentMessages;
          if (commentMessages.isEmpty) {
            return Padding(
              padding: EdgeInsets.symmetric(vertical: 16.h),
              child: Center(
                child: Text(
                  'Chưa có bình luận nào',
                  style: TextStyle(
                    fontSize: 14.sp,
                    color: AppColors.textSecondary,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
            );
          }

          // Create comments with better performance - use ListView.separated for better rendering
          return ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: commentMessages.length,
            separatorBuilder: (context, index) => SizedBox(height: 12.h),
            itemBuilder: (context, index) {
              final comment = commentMessages[index];
              return RepaintBoundary(
                child: _CommentItem(post: post, comment: comment),
              );
            },
          );
        }),
      ],
    );
  }
}

class _CommentComposer extends StatefulWidget {
  const _CommentComposer({required this.post});

  final CommunityPost post;

  @override
  State<_CommentComposer> createState() => _CommentComposerState();
}

class _CommentComposerState extends State<_CommentComposer> {
  late final TextEditingController _textController;
  late final CommunityController _communityController;

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController();
    _communityController = Get.find<CommunityController>();
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  void _submitComment() {
    final content = _textController.text.trim();
    if (content.isEmpty) return;

    try {
      _communityController.addComment(widget.post, content);
      _textController.clear();
      FocusScope.of(context).unfocus();

     
    } catch (e) {
      // Handle error gracefully
      debugPrint('Error adding comment: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Không thể thêm bình luận. Vui lòng thử lại.'),
          duration: Duration(seconds: 3),
          behavior: SnackBarBehavior.floating,
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: AppColors.primarySoft,
        borderRadius: BorderRadius.circular(24.r),
      ),
      child: Row(
        children: [
          StickerButton(onPick: (code) => _communityController.addStickerComment(widget.post, code)),
          Expanded(
            child: TextField(
              controller: _textController,
              decoration: const InputDecoration(
                hintText: 'Viết bình luận của bạn...',
                border: InputBorder.none,
              ),
              minLines: 1,
              maxLines: 3,
            ),
          ),
          SizedBox(width: 8.w),
          SizedBox(
            height: 48.h,
            child: ElevatedButton(
              onPressed: () => _submitComment(),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(18.r),
                ),
                padding: EdgeInsets.symmetric(horizontal: 16.w),
              ),
              child: Icon(Icons.send, color: Colors.white, size: 20.sp),
            ),
          ),
        ],
      ),
    );
  }
}

class _DetectedVocabularyList extends StatelessWidget {
  const _DetectedVocabularyList({required this.items, required this.post});

  final List<CommunityVocabularyItem> items;
  final CommunityPost post;

  @override
  Widget build(BuildContext context) {
    try {
      final communityController = Get.find<CommunityController>();
      return Obx(() {
        // Comprehensive validation and safe access
        if (items.isEmpty) {
          return const SizedBox.shrink();
        }

        final total = items.length;
        final rawIndex = post.currentVocabularyIndex.value;
        final currentIndex = rawIndex.clamp(0, total - 1);

        // Additional safety check
        if (currentIndex >= items.length) {
          debugPrint('Warning: vocabulary index $currentIndex out of bounds for ${items.length} items');
          return const SizedBox.shrink();
        }

        final vocabulary = items[currentIndex];

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Từ vựng đã nhận diện',
            style: TextStyle(
              fontSize: 15.sp,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          SizedBox(height: 12.h),
          Stack(
            clipBehavior: Clip.none,
            alignment: Alignment.center,
            children: [
              RepaintBoundary(
                child: _DetectedVocabularyItem(item: vocabulary, post: post),
              ),
              if (total > 1)
                Positioned(
                  left: -8.w,
                  child: _NavButton(
                    icon: Icons.chevron_left,
                    onTap: currentIndex > 0
                        ? () => communityController.goToPreviousVocabulary(post)
                        : null,
                  ),
                ),
              if (total > 1)
                Positioned(
                  right: -8.w,
                  child: _NavButton(
                    icon: Icons.chevron_right,
                    onTap: currentIndex < total - 1
                        ? () => communityController.goToNextVocabulary(post)
                        : null,
                  ),
                ),
            ],
          ),
          SizedBox(height: 12.h),
          Center(
            child: Text(
              '${currentIndex + 1}/$total',
              style: TextStyle(
                fontSize: 13.sp,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
              ),
            ),
          ),
          SizedBox(height: 16.h),
          _PrimaryActionButton(
            label: 'Lưu từ vựng',
            leadingIcon: Icons.bookmark_add_rounded,
            onTap: () => communityController.saveVocabulary(post, vocabulary),
          ),
        ],
      );
      });
    } catch (e) {
      debugPrint('Error in DetectedVocabularyList: $e');
      return Container(
        padding: EdgeInsets.all(16.w),
        child: Center(
          child: Text(
            'Không thể hiển thị từ vựng',
            style: TextStyle(
              fontSize: 14.sp,
              color: Colors.red,
            ),
          ),
        ),
      );
    }
  }
}

class _DetectedVocabularyItem extends StatelessWidget {
  const _DetectedVocabularyItem({required this.item, required this.post});

  final CommunityVocabularyItem item;
  final CommunityPost post;

  @override
  Widget build(BuildContext context) {
    final communityController = Get.find<CommunityController>();
    final confidencePercent = (item.confidence * 100).clamp(0, 100);
    return Obx(() {
      final topic = item.topic.value?.trim() ?? '';
      final isSaved = item.isSelected.value;
      return Container(
        padding: EdgeInsets.all(18.w),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(28.r),
          color: AppColors.surface,
          border: Border.all(color: AppColors.primaryTint),),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                GestureDetector(
                  onTap: () =>
                      communityController.toggleSelection(post, item),
                  child: _SelectIndicator(isActive: isSaved),
                ),
                SizedBox(width: 12.w),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.headword,
                        style: TextStyle(
                          fontSize: 16.sp,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      if (item.translation.isNotEmpty) ...[
                        SizedBox(height: 4.h),
                        Text(
                          item.translation,
                          style: TextStyle(
                            fontSize: 14.sp,
                            fontWeight: FontWeight.w600,
                            color: const Color(0xFF02C39A),
                          ),
                        ),
                      ],
                      if (item.phonetic.isNotEmpty) ...[
                        SizedBox(height: 2.h),
                        Text(
                          item.phonetic,
                          style: TextStyle(
                            fontSize: 12.sp,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                      
                    ],
                  ),
                ),
                SizedBox(width: 12.w),
                Container(
                  width: 38.w,
                  height: 38.w,
                  decoration: BoxDecoration(
                    color: AppColors.primarySoft,
                    shape: BoxShape.circle,
                  ),
                  child: IconButton(
                    onPressed: () => communityController.speakWord(item.headword),
                    icon: Icon(
                      Icons.volume_up_rounded,
                      color: AppColors.primary,
                      size: 20.sp,
                    ),
                  ),
                ),
              ],
            ),
            SizedBox(height: 18.h),
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
                SizedBox(width: 10.w),
                Expanded(
                  child: _TopicButton(
                    label: topic.isEmpty ? 'Chọn chủ đề' : topic,
                    onPressed: () =>
                        _showTopicPicker(context, communityController, item),
                  ),
                ),
              ],
            ),
          ],
        ),
      );
    });
  }
}

void _showTopicPicker(
  BuildContext context,
  CommunityController controller,
  CommunityVocabularyItem vocabulary,
) {
  if (!context.mounted) return; // Ensure context is still valid

  final initialTopic = vocabulary.topic.value?.trim() ?? '';
  final textController = TextEditingController(text: initialTopic);
  String? tempSelection = initialTopic.isNotEmpty ? initialTopic : null;

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
                            textController.selection = TextSelection.collapsed(
                              offset: topicOption.length,
                            );
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
                        borderSide: BorderSide(color: AppColors.primarySoft),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16.r),
                        borderSide: BorderSide(color: AppColors.primary),
                      ),
                    ),
                  ),
                  SizedBox(height: 20.h),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () {
                        final manualTopic = textController.text.trim();
                        final selectedTopic = tempSelection?.trim();

                        // Enhanced validation
                        if (manualTopic.isEmpty &&
                            (selectedTopic == null || selectedTopic.isEmpty)) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Vui lòng chọn hoặc nhập chủ đề'),
                              duration: Duration(seconds: 2),
                            ),
                          );
                          return;
                        }

                        final newTopic = manualTopic.isNotEmpty
                            ? manualTopic
                            : selectedTopic!;

                        // Additional validation for topic length
                        if (newTopic.length > 50) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Tên chủ đề quá dài (tối đa 50 ký tự)'),
                              duration: Duration(seconds: 2),
                            ),
                          );
                          return;
                        }

                        try {
                          controller.updateTopic(vocabulary, newTopic);
                          Navigator.of(sheetContext).pop();
                        } catch (e) {
                          debugPrint('Error updating topic: $e');
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Không thể cập nhật chủ đề. Vui lòng thử lại.'),
                              duration: Duration(seconds: 2),
                              backgroundColor: Colors.red,
                            ),
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
                  SizedBox(height: 10.h),
                ],
              ),
            );
          },
        ),
      );
    },
  );
}

class _CommentItem extends StatelessWidget {
  const _CommentItem({required this.post, required this.comment});

  final CommunityPost post;
  final CommunityPostComment comment;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(22.r),
        border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 22.r,
            backgroundColor: AppColors.primarySoft,
            backgroundImage: comment.avatarUrl.isNotEmpty
                ? _AvatarImageProvider.from(comment.avatarUrl)
                : null,
            child: comment.avatarUrl.isEmpty
                ? Text(
                    _initialsFrom(comment.userName),
                    style: TextStyle(
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary,
                    ),
                  )
                : null,
          ),
          SizedBox(width: 12.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  comment.userName,
                  style: TextStyle(
                    fontSize: 14.sp,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                SizedBox(height: 4.h),
                if (comment.content.startsWith('assets/rewards/stickers/'))
                  Image.asset(comment.content, width: 96.w, height: 100.w, fit: BoxFit.contain,
                      errorBuilder: (_, __, ___) => const Icon(Icons.emoji_emotions_outlined))
                else
                  Text(
                    comment.content,
                    style: TextStyle(
                      fontSize: 13.5.sp,
                      height: 1.38,
                      color: AppColors.textSecondary,
                    ),
                  ),
              ],
            ),
          ),
          SizedBox(width: 12.w),
          comment.isPending
              ? SizedBox(
                  width: 18.w,
                  height: 18.w,
                  child: const CircularProgressIndicator(strokeWidth: 2.0),
                )
              : comment.canDelete
                  ? IconButton(
                      tooltip: 'Xoá bình luận',
                      visualDensity: VisualDensity.compact,
                      onPressed: () => Get.find<CommunityController>().deleteComment(post, comment),
                      icon: Icon(Icons.delete_outline_rounded, color: AppColors.textSecondary, size: 20.sp),
                    )
                  : const SizedBox.shrink(),
        ],
      ),
    );
  }

  String _initialsFrom(String name) {
    final words = name.trim().split(RegExp(r'\s+')).where((w) => w.isNotEmpty).toList();
    if (words.isEmpty) return '??';
    final first = words.first;
    final last = words.length > 1 ? words.last : '';
    final firstInitial = first.isNotEmpty ? first[0] : '';
    final lastInitial = last.isNotEmpty ? last[0] : '';
    return (firstInitial + lastInitial).toUpperCase();
  }
}

class _VocabularyTag extends StatelessWidget {
  const _VocabularyTag({required this.item});

  final CommunityVocabularyItem item;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 8.h),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(18.r),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            item.label.toUpperCase(),
            style: TextStyle(
              fontSize: 11.sp,
              letterSpacing: 0.8,
              fontWeight: FontWeight.w700,
              color: Colors.lightGreenAccent,
            ),
          ),
          SizedBox(height: 4.h),
          Text(
            '${(item.confidence * 100).toStringAsFixed(0)}%',
            style: TextStyle(
              fontSize: 10.sp,
              color: Colors.white70,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatButton extends StatelessWidget {
  const _StatButton({
    required this.icon,
    required this.color,
    required this.label,
    this.onTap,
  });

  final IconData icon;
  final Color color;
  final String label;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Icon(icon, color: color, size: 24.sp),
          SizedBox(height: 6.h),
          Text(
            label,
            style: TextStyle(
              fontSize: 13.sp,
              fontWeight: FontWeight.w600,
              color: color,
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
  });

  final String label;
  final IconData? leadingIcon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: EdgeInsets.symmetric(vertical: 16.h),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(30.r),
          color: AppColors.primaryLight,
          boxShadow: [
            BoxShadow(
              color: AppColors.primary.withValues(alpha: 0.25),
              blurRadius: 20.r,
              offset: Offset(0, 10.h),
            ),
          ],),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (leadingIcon != null) ...[
              Icon(leadingIcon, color: Colors.white, size: 20.sp),
              SizedBox(width: 10.w),
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

class _NavButton extends StatelessWidget {
  const _NavButton({required this.icon, this.onTap});

  final IconData icon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 44.w,
        height: 44.w,
        decoration: BoxDecoration(
          color: AppColors.surface,
          shape: BoxShape.circle,
          border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
        child: Icon(
          icon,
          color: AppColors.textSecondary,
          size: 26.sp,
        ),
      ),
    );
  }
}

class _SelectIndicator extends StatelessWidget {
  const _SelectIndicator({required this.isActive});

  final bool isActive;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 28.w,
      height: 28.w,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: isActive ? AppColors.primary : AppColors.textHint,
          width: 2,
        ),
        color: isActive ? AppColors.primary : Colors.transparent,
      ),
      child: isActive
          ? Icon(Icons.check, color: Colors.white, size: 16.sp)
          : null,
    );
  }
}

class _TopicButton extends StatelessWidget {
  const _TopicButton({required this.label, required this.onPressed});

  final String label;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14.r),
        ),
        padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 10.h),
        elevation: 0,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 13.sp,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Icon(
            Icons.keyboard_arrow_down_rounded,
            color: Colors.white,
            size: 20.sp,
          ),
        ],
      ),
    );
  }
}
