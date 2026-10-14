import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/theme/app_colors.dart';
import '../controllers/vocabulary_list_controller.dart';

class VocabularyListView extends GetView<VocabularyListController> {
  const VocabularyListView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            _buildHeader(),

            // Vocabulary List
            Expanded(
              child: Obx(() {
                if (controller.isLoading) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (controller.vocabularies.isEmpty) {
                  return _buildEmptyState();
                }

                return ListView.builder(
                  padding: EdgeInsets.all(16.w),
                  itemCount: controller.vocabularies.length,
                  itemBuilder: (context, index) {
                    final vocab = controller.vocabularies[index];
                    return _buildVocabularyCard(vocab);
                  },
                );
              }),
            ),
          ],
        ),
      ),

      // FAB - Add new word
      floatingActionButton: FloatingActionButton(
        heroTag: 'vocabularyListFab',
        onPressed: controller.addNewWord,
        backgroundColor: const Color(0xFF1CB0F6),
        child: Icon(Icons.add, size: 30.sp, color: Colors.white),
      ),
    );
  }

  /// Header với back button, title và Flashcard button
  Widget _buildHeader() {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          // Back button
          IconButton(
            onPressed: () => Get.back(),
            icon: Icon(Icons.arrow_back, size: 24.sp),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),

          SizedBox(width: 12.w),

          // Title
          Expanded(
            child: Text(
              controller.categoryName,
              style: TextStyle(
                fontSize: 24.sp,
                fontWeight: FontWeight.bold,
                color: Colors.black,
              ),
            ),
          ),

          SizedBox(width: 12.w),

          // Flashcard button
          ElevatedButton(
            onPressed: controller.openFlashcard,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF1CB0F6),
              foregroundColor: Colors.white,
              padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 10.h),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20.r),
              ),
              elevation: 0,
            ),
            child: Text(
              'Flashcard',
              style: TextStyle(
                fontSize: 14.sp,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// Card hiển thị từ vựng
  Widget _buildVocabularyCard(VocabularyItem vocab) {
    final statusColor = _getStatusColor(vocab.status);
    final statusText = _getStatusText(vocab.status);

    return Container(
      margin: EdgeInsets.only(bottom: 12.h),
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: const Color(0xFFE5F8FF),
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(
          color: const Color(0xFF1CB0F6),
          width: 2,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Word + Audio + Menu
          Row(
            children: [
              // Word
              Expanded(
                child: Text(
                  vocab.word,
                  style: TextStyle(
                    fontSize: 24.sp,
                    fontWeight: FontWeight.bold,
                    color: Colors.black,
                  ),
                ),
              ),

              // Audio icon
              if (vocab.audioUrl != null && vocab.audioUrl!.isNotEmpty)
                IconButton(
                  onPressed: () => controller.playPronunciation(vocab.audioUrl!),
                  icon: Icon(
                    Icons.volume_up,
                    size: 24.sp,
                    color: const Color(0xFF1CB0F6),
                  ),
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),

              SizedBox(width: 12.w),

              // Status badge
              Container(
                padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 4.h),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12.r),
                ),
                child: Text(
                  statusText,
                  style: TextStyle(
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w600,
                    color: statusColor,
                  ),
                ),
              ),

              SizedBox(width: 8.w),

              // Menu button
              IconButton(
                onPressed: () => controller.showWordOptions(vocab),
                icon: Icon(
                  Icons.more_vert,
                  size: 24.sp,
                  color: Colors.black54,
                ),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ],
          ),

          SizedBox(height: 8.h),

          // Phonetic
          if (vocab.phonetic != null && vocab.phonetic!.isNotEmpty)
            Padding(
              padding: EdgeInsets.only(bottom: 4.h),
              child: Text(
                vocab.phonetic!,
                style: TextStyle(
                  fontSize: 14.sp,
                  color: Colors.black54,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ),

          // Translation
          Padding(
            padding: EdgeInsets.only(bottom: 4.h),
            child: Text(
              vocab.translation,
              style: TextStyle(
                fontSize: 14.sp,
                color: Colors.black87,
              ),
            ),
          ),

          // Example
          if (vocab.example != null && vocab.example!.isNotEmpty)
            Padding(
              padding: EdgeInsets.only(top: 4.h),
              child: Text(
                'VD: ${vocab.example}',
                style: TextStyle(
                  fontSize: 13.sp,
                  color: Colors.black54,
                ),
              ),
            ),
        ],
      ),
    );
  }

  /// Empty state
  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.book_outlined,
            size: 80.sp,
            color: Colors.grey,
          ),
          SizedBox(height: 16.h),
          Text(
            'Chưa có từ vựng nào',
            style: TextStyle(
              fontSize: 18.sp,
              color: Colors.grey,
            ),
          ),
          SizedBox(height: 8.h),
          Text(
            'Nhấn nút + để thêm từ mới',
            style: TextStyle(
              fontSize: 14.sp,
              color: Colors.grey,
            ),
          ),
        ],
      ),
    );
  }

  /// Lấy màu status
  Color _getStatusColor(String status) {
    switch (status) {
      case 'learning':
        return const Color(0xFFF59E0B); // Orange
      case 'reviewing':
        return const Color(0xFF3B82F6); // Blue
      case 'mastered':
        return const Color(0xFF10B981); // Green
      default:
        return Colors.grey;
    }
  }

  /// Lấy text status
  String _getStatusText(String status) {
    switch (status) {
      case 'learning':
        return 'đang học';
      case 'reviewing':
        return 'ôn tập';
      case 'mastered':
        return 'đã học';
      default:
        return 'mới';
    }
  }
}
