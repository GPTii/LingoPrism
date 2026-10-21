import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_slidable/flutter_slidable.dart';
import 'package:get/get.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_widgets.dart';
import '../controllers/vocabulary_topic_controller.dart';
import '../../levels/levels_module.dart' show levelColors;
import '../../../core/widgets/word_picture.dart';

class VocabularyTopicView extends GetView<VocabularyTopicController> {
  const VocabularyTopicView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: _buildAppBar(),
      body: Obx(() => ListView.builder(
            padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
            itemCount: controller.items.length,
            itemBuilder: (context, index) {
              final item = controller.items[index];
              return _VocabularyCard(
                item: item,
                controller: controller,
                index: index,
              );
            },
          )),
      floatingActionButton: FloatingActionButton(
        heroTag: 'vocabularyTopicFab',
        onPressed: controller.onAddVocabularyPressed,
        backgroundColor: AppColors.primary,
        child: Icon(Icons.add, size: 28.sp, color: Colors.white),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: AppColors.appBarBackground,
      elevation: 0,
      leading: IconButton(
        onPressed: () => Get.back(),
        icon: Icon(Icons.arrow_back, size: 24.sp, color: AppColors.textPrimary),
      ),
      titleSpacing: 0,
      title: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            controller.topicName,
            style: TextStyle(
              fontSize: 18.sp,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          SizedBox(height: 4.h),
          Text(
            '${controller.totalWords} từ vựng',
            style: TextStyle(
              fontSize: 13.sp,
              color: AppColors.textSecondary,
            ),
          ),
          
        ],
      ),
      actions: [
        IconButton(
          tooltip: 'Luyện câu',
          onPressed: controller.onSentencePressed,
          icon: Icon(Icons.edit_note_rounded, size: 28.sp, color: AppColors.primary),
        ),
        Padding(
          padding: EdgeInsets.only(right: 16.w),
          child: ElevatedButton(
            onPressed: controller.onFlashcardPressed,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 10.h),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14.r),
              ),
              elevation: 0,
            ),
            child: Text(
              'Flashcard',
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _VocabularyCard extends StatelessWidget {
  const _VocabularyCard({
    required this.item,
    required this.controller,
    required this.index,
  });

  final VocabularyTopicItem item;
  final VocabularyTopicController controller;
  final int index;

  Color _statusColor(VocabularyLearningStatus status) {
    switch (status) {
      case VocabularyLearningStatus.notStarted:
        return AppColors.primary;
      case VocabularyLearningStatus.learning:
        return const Color(0xFFF6A609);
      case VocabularyLearningStatus.learned:
        return const Color(0xFF028A3D);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: 12.h),
      child: Slidable(
        key: ValueKey(item.word),
        endActionPane: ActionPane(
          motion: const StretchMotion(),
          extentRatio: 0.7,
          children: [
            _ActionButton(
              label: 'Sửa',
              icon: Icons.edit_outlined,
              backgroundColor: AppColors.tint(const Color(0xFFFFE9F0)),
              foregroundColor: const Color(0xFFE64980),
              onTap: () => controller.onEditVocabulary(index),
            ),
            _ActionButton(
              label: 'Xoá',
              icon: Icons.delete_outline,
              backgroundColor: AppColors.tint(const Color(0xFFFFF2E5)),
              foregroundColor: const Color(0xFFF97316),
              onTap: () => controller.onDeleteVocabulary(index),
            ),
          ],
        ),
        child: Container(
          padding: EdgeInsets.all(16.w),
          decoration: AppWidgets.questGradientDecoration().copyWith(
            borderRadius: BorderRadius.circular(18.r),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 8,
                offset: Offset(0, 4.h),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (item.card != null) ...[
                    WordPicture(imageUrl: item.card!.image, emoji: item.card!.emoji, size: 64.w),
                    SizedBox(width: 12.w),
                  ],
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Wrap(
                          spacing: 8.w,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            Text(
                              item.word,
                              style: TextStyle(
                                fontSize: 20.sp,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            Text(
                              item.ipa,
                              style: TextStyle(
                                fontSize: 14.sp,
                                color: AppColors.primaryDark,
                              ),
                            ),
                            if (item.card?.level != null)
                              Container(
                                padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 2.h),
                                decoration: BoxDecoration(
                                  color: levelColors[item.card!.level! - 1],
                                  borderRadius: BorderRadius.circular(8.r),
                                ),
                                child: Text('Cấp ${item.card!.level}',
                                    style: TextStyle(fontSize: 11.sp, color: Colors.white, fontWeight: FontWeight.w700)),
                              ),
                            IconButton(
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(),
                              onPressed: () => controller.playAudio(item),
                              icon: Icon(
                                Icons.volume_up,
                                size: 20.sp,
                                color: AppColors.primary,
                              ),
                            ),
                          ],
                        ),
                        Text(
                          item.translation,
                          style: TextStyle(
                            fontSize: 14.sp,
                            color: const Color(0xFF006A6A),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding:
                        EdgeInsets.symmetric(horizontal: 12.w, vertical: 6.h),
                    decoration: BoxDecoration(
                      color: _statusColor(item.status).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12.r),
                    ),
                    child: Text(
                      controller.statusLabel(item.status),
                      style: TextStyle(
                        fontSize: 12.sp,
                        fontWeight: FontWeight.bold,
                        color: _statusColor(item.status),
                      ),
                    ),
                  ),
                ],
              ),
              Text(
                'EX: ${item.exampleEn}',
                style: TextStyle(
                  fontSize: 13.sp,
                  color: AppColors.textSecondary,
                ),
              ),
              Text(
                'VD: ${item.exampleVi}',
                style: TextStyle(
                  fontSize: 13.sp,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.label,
    required this.icon,
    required this.backgroundColor,
    required this.foregroundColor,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final Color backgroundColor;
  final Color foregroundColor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return CustomSlidableAction(
      onPressed: (_) => onTap(),
      padding: EdgeInsets.zero,
      backgroundColor: AppColors.backgroundLight,
      child: Container(
        width: 110.w,
        margin: EdgeInsets.symmetric(horizontal: 6.w),
        padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 18.h),
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.circular(18.r),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: foregroundColor, size: 22.sp),
            SizedBox(height: 6.h),
            Text(
              label,
              style: TextStyle(
                fontSize: 13.sp,
                fontWeight: FontWeight.w600,
                color: foregroundColor,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
