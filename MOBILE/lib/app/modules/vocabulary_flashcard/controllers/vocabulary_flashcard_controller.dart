import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../data/services/tts_service.dart';
import '../../vocabulary_topic/controllers/vocabulary_topic_controller.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

/// Free browsing of a topic's flashcards (not graded – graded practice uses a study session).
class VocabularyFlashcardController extends GetxController {
  late final List<VocabularyTopicItem> items;
  late final String topicName;
  late final PageController pageController;

  final RxInt _currentIndex = 0.obs;
  final RxBool _showBack = false.obs;

  int get currentIndex => _currentIndex.value;
  bool get isBackVisible => _showBack.value;
  bool get canGoBack => _currentIndex.value > 0;
  bool get canGoNext => _currentIndex.value < total - 1;
  int get total => items.length;
  String get language => items.isNotEmpty ? items.first.language : 'en';

  @override
  void onInit() {
    super.onInit();
    pageController = PageController();
    final args = Get.arguments as Map<String, dynamic>?;
    final incoming = args?['items'];
    items = incoming is List<VocabularyTopicItem> ? incoming : <VocabularyTopicItem>[];
    topicName = args?['topicName'] as String? ?? 'Flashcard';
    if (items.isEmpty) Future.microtask(goBack);
  }

  @override
  void onClose() {
    TtsService.to.stop();
    pageController.dispose();
    super.onClose();
  }

  void onPageChanged(int index) {
    _currentIndex.value = index;
    _showBack.value = false;
  }

  void toggleSide() => _showBack.toggle();

  void toggleSideFor(int index) {
    if (_currentIndex.value != index) {
      pageController.animateToPage(index, duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
      return;
    }
    toggleSide();
  }

  void completeSession() {
    goBack();
    Get.snackbar('Flashcard', 'Bạn đã xem hết thẻ của "$topicName". Hãy luyện tập để ghi nhớ lâu hơn!',
        snackPosition: SnackPosition.BOTTOM);
  }

  Future<void> playAudio(VocabularyTopicItem item) => TtsService.to.speak(item.word, item.ttsLocale);

  void previousCard() {
    if (!canGoBack) return;
    _showBack.value = false;
    pageController.previousPage(duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
  }

  void nextCard() {
    if (!canGoNext) return;
    _showBack.value = false;
    pageController.nextPage(duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
  }
}
