import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../vocabulary_flashcard/bindings/vocabulary_flashcard_binding.dart';
import '../../vocabulary_flashcard/views/vocabulary_flashcard_view.dart';
import '../../vocabulary_topic/controllers/vocabulary_topic_controller.dart';

/// Simple data model for previewing vocabulary content without backend data.
class VocabularyItem {
  VocabularyItem({
    required this.id,
    required this.word,
    required this.translation,
    this.phonetic,
    this.example,
    this.audioUrl,
    this.status = 'new',
    this.isFavorite = false,
  });

  final String id;
  final String word;
  final String translation;
  final String? phonetic;
  final String? example;
  final String? audioUrl;
  String status;
  bool isFavorite;
}

class VocabularyListController extends GetxController {
  static VocabularyListController get to => Get.find();

  String categoryName = 'Từ vựng mẫu';

  final _items = <VocabularyItem>[].obs;
  final _isLoading = false.obs;

  List<VocabularyItem> get vocabularies => _items;
  bool get isLoading => _isLoading.value;

  @override
  void onInit() {
    super.onInit();
    final args = Get.arguments;
    if (args != null) {
      categoryName = args['categoryName'] ?? categoryName;
    }
  }

  @override
  void onReady() {
    super.onReady();
    _loadMockData();
  }

  void _loadMockData() {
    _isLoading.value = true;
    _items.assignAll([
      VocabularyItem(
        id: '1',
        word: 'Hello',
        translation: 'Xin chào',
        phonetic: '/həˈləʊ/',
        example: 'Hello, nice to meet you!',
        status: 'learning',
        isFavorite: true,
      ),
      VocabularyItem(
        id: '2',
        word: 'Conversation',
        translation: 'Cuộc trò chuyện',
        phonetic: '/ˌkɒnvəˈseɪʃn/',
        example: 'We had a great conversation yesterday.',
        status: 'reviewing',
      ),
      VocabularyItem(
        id: '3',
        word: 'Fluent',
        translation: 'Trôi chảy',
        phonetic: '/ˈfluː.ənt/',
        example: 'She is fluent in three languages.',
        status: 'mastered',
      ),
    ]);
    _isLoading.value = false;
  }

  String getWordStatus(String vocabularyId) {
    return _items.firstWhere(
      (item) => item.id == vocabularyId,
      orElse: () => VocabularyItem(
        id: vocabularyId,
        word: '',
        translation: '',
      ),
    ).status;
  }

  Future<void> playPronunciation(String audioUrl) async {
    Get.snackbar(
      'Phát âm',
      'Chưa có âm thanh, đây chỉ là dữ liệu mẫu.',
      snackPosition: SnackPosition.BOTTOM,
      duration: const Duration(seconds: 1),
    );
  }

  void toggleFavorite(String vocabularyId) {
    final index = _items.indexWhere((item) => item.id == vocabularyId);
    if (index == -1) return;

    final current = _items[index];
    _items[index] = VocabularyItem(
      id: current.id,
      word: current.word,
      translation: current.translation,
      phonetic: current.phonetic,
      example: current.example,
      audioUrl: current.audioUrl,
      status: current.status,
      isFavorite: !current.isFavorite,
    );

    Get.snackbar(
      'Thành công',
      _items[index].isFavorite ? 'Đã thêm vào yêu thích' : 'Đã bỏ yêu thích',
      snackPosition: SnackPosition.BOTTOM,
      duration: const Duration(seconds: 1),
    );
  }

  Future<void> deleteWord(String vocabularyId) async {
    final confirmed = await Get.dialog<bool>(
      AlertDialog(
        title: const Text('Xác nhận'),
        content: const Text('Bạn có chắc muốn xóa từ này?'),
        actions: [
          TextButton(
            onPressed: () => Get.back(result: false),
            child: const Text('Hủy'),
          ),
          TextButton(
            onPressed: () => Get.back(result: true),
            child: const Text('Xóa', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      _items.removeWhere((item) => item.id == vocabularyId);
      Get.snackbar(
        'Thành công',
        'Đã xóa từ khỏi danh sách',
        snackPosition: SnackPosition.BOTTOM,
        duration: const Duration(seconds: 1),
      );
    }
  }

  void addNewWord() {
    Get.snackbar(
      'Demo',
      'Đây chỉ là màn hình demo, chưa thêm được từ mới.',
      snackPosition: SnackPosition.BOTTOM,
    );
  }

  void openFlashcard() {
    final flashcardItems = _toFlashcardItems();
    Get.to(
      () => const VocabularyFlashcardView(),
      binding: VocabularyFlashcardBinding(),
      arguments: {
        'items': flashcardItems,
        'topicName': categoryName,
      },
    );
  }

  void showWordOptions(VocabularyItem vocab) {
    Get.bottomSheet(
      Container(
        padding: const EdgeInsets.all(20),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: Icon(
                vocab.isFavorite ? Icons.favorite : Icons.favorite_border,
              ),
              title: Text(
                vocab.isFavorite
                    ? 'Bỏ khỏi yêu thích'
                    : 'Thêm vào yêu thích',
              ),
              onTap: () {
                Get.back();
                toggleFavorite(vocab.id);
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete, color: Colors.red),
              title: const Text('Xóa', style: TextStyle(color: Colors.red)),
              onTap: () {
                Get.back();
                deleteWord(vocab.id);
              },
            ),
          ],
        ),
      ),
    );
  }

  List<VocabularyTopicItem> _toFlashcardItems() {
    return _items
        .map(
          (item) => VocabularyTopicItem(
            word: item.word,
            ipa: item.phonetic ?? '',
            translation: item.translation,
            exampleEn: item.example ?? '',
            exampleVi: item.translation,
            status: _mapStatus(item.status),
          ),
        )
        .toList();
  }

  VocabularyLearningStatus _mapStatus(String status) {
    switch (status) {
      case 'learning':
      case 'reviewing':
        return VocabularyLearningStatus.learning;
      case 'mastered':
        return VocabularyLearningStatus.learned;
      default:
        return VocabularyLearningStatus.notStarted;
    }
  }
}
