import 'dart:async';

import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../data/models/api/vocab.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';
import '../../../data/services/tts_service.dart';
import '../../../routes/app_pages.dart';
import '../../add_vocabulary_category/bindings/add_vocabulary_category_binding.dart';
import '../../add_vocabulary_category/views/add_vocabulary_category_view.dart';
import '../../learning_session/controllers/learning_session_controller.dart';
import '../../vocabulary_topic/controllers/vocabulary_topic_controller.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

/// A topic in the learner's library (system topic with saved words, or a personal topic).
class VocabularyCategory {
  const VocabularyCategory({required this.topic});

  final Topic topic;

  int get id => topic.id;
  String get name => topic.nameVi;
  String get icon => topic.icon.isEmpty ? '📘' : topic.icon;
  bool get isSystem => topic.isSystem;
  int get wordCount => topic.isSystem ? topic.savedCount : topic.savedCount;
  double get progress => topic.savedCount == 0 ? 0 : (topic.learnedCount / topic.savedCount).clamp(0, 1).toDouble();
}

class VocabularySearchResult {
  const VocabularySearchResult({required this.card, required this.item});

  final WordCard card;
  final VocabularyTopicItem item;
  String get categoryName => '';
}

/// "Thư viện từ vựng" tab: saved topics, recommended system topics, search, start review.
class ReviewController extends GetxController {
  final searchController = TextEditingController();
  final RxList<VocabularyCategory> categories = <VocabularyCategory>[].obs;
  final RxList<VocabularyCategory> filteredCategories = <VocabularyCategory>[].obs;
  final RxList<VocabularySearchResult> searchResults = <VocabularySearchResult>[].obs;
  final RxBool isSearching = false.obs;
  final RxBool isSeedingDefault = false.obs;
  final RxString currentQuery = ''.obs;
  final RxList<Topic> recommendedTopics = <Topic>[].obs;
  final RxBool isLoadingRecommendations = false.obs;
  final RxSet<int> savingTopicIds = <int>{}.obs;
  final RxBool isLoading = false.obs;
  Timer? _debounce;

  @override
  void onInit() {
    super.onInit();
    loadCategories();
  }

  @override
  void onClose() {
    _debounce?.cancel();
    searchController.dispose();
    super.onClose();
  }

  /// Loads all topics once and splits them into "my library" and "recommended".
  Future<void> loadCategories({bool skipHydration = false}) async {
    if (!AuthService.to.isLoggedIn) return;
    isLoading.value = true;
    isLoadingRecommendations.value = true;
    try {
      final topics = await VocabRepository.topics();
      final mine = topics.where((t) => t.inLibrary).map((t) => VocabularyCategory(topic: t)).toList();
      categories.assignAll(mine);
      _applyFilter();
      recommendedTopics.assignAll(topics.where((t) => t.isSystem && t.savedCount == 0 && t.wordCount > 0));
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      isLoading.value = false;
      isLoadingRecommendations.value = false;
    }
  }

  Future<void> loadRecommendedTopics() => loadCategories();

  Future<void> ensureRecommendedTopicsLoaded() async {
    if (recommendedTopics.isEmpty && !isLoadingRecommendations.value) await loadCategories();
  }

  bool isTopicSaved(Topic topic) => topic.savedCount > 0 || categories.any((c) => c.id == topic.id);

  bool isTopicSaving(int topicId) => savingTopicIds.contains(topicId);

  Future<void> onSaveTopic(Topic topic) async {
    if (isTopicSaving(topic.id)) return;
    savingTopicIds.add(topic.id);
    try {
      final added = await VocabRepository.saveTopic(topic.id);
      Get.snackbar('Thành công', 'Đã lưu $added từ của chủ đề "${topic.nameVi}"', snackPosition: SnackPosition.BOTTOM);
      await loadCategories();
      GameService.to.refreshLibrary();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      savingTopicIds.remove(topic.id);
    }
  }

  void onSearchChanged(String query) {
    currentQuery.value = query.trim();
    _applyFilter();
    _debounce?.cancel();
    if (currentQuery.value.isEmpty) {
      searchResults.clear();
      isSearching.value = false;
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 350), () async {
      isSearching.value = true;
      try {
        final cards = await VocabRepository.search(currentQuery.value);
        searchResults.assignAll(cards
            .where((c) => c.target != null)
            .map((c) => VocabularySearchResult(card: c, item: VocabularyTopicItem.fromCard(c))));
      } catch (_) {
        searchResults.clear();
      } finally {
        isSearching.value = false;
      }
    });
  }

  void _applyFilter() {
    final q = currentQuery.value.toLowerCase();
    filteredCategories.assignAll(q.isEmpty ? categories : categories.where((c) => c.name.toLowerCase().contains(q)));
  }

  Future<void> onCategoryTap(VocabularyCategory category) async {
    await Get.toNamed(Routes.vocabularyTopic, arguments: VocabularyTopicArguments(topic: category.topic));
    loadCategories();
  }

  Future<void> onAddCategory() async {
    final result = await Get.to(() => const AddVocabularyCategoryView(), binding: AddVocabularyCategoryBinding());
    if (result is! Map) return;
    try {
      final topic = await VocabRepository.createTopic(result['name'] as String, icon: result['icon'] as String? ?? '📘');
      await loadCategories();
      Get.toNamed(Routes.vocabularyTopic, arguments: VocabularyTopicArguments(topic: topic));
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> onEditCategory(VocabularyCategory category) async {
    if (category.isSystem) {
      Get.snackbar('Thông báo', 'Không thể sửa chủ đề hệ thống.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    final result = await Get.to(() => const AddVocabularyCategoryView(),
        binding: AddVocabularyCategoryBinding(), arguments: {'name': category.name, 'icon': category.icon});
    if (result is! Map) return;
    try {
      await ApiClient.to.patch('/topics/${category.id}/', data: {'name_vi': result['name'], 'icon': result['icon']});
      await loadCategories();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> onDeleteCategory(VocabularyCategory category) async {
    if (category.isSystem) {
      Get.snackbar('Thông báo', 'Chủ đề hệ thống không xoá được. Bạn có thể xoá từng từ trong chủ đề.',
          snackPosition: SnackPosition.BOTTOM);
      return;
    }
    final confirmed = await Get.dialog<bool>(AlertDialog(
      title: const Text('Xoá chủ đề'),
      content: Text('Xoá chủ đề "${category.name}"? Các từ vẫn còn trong thư viện của bạn.'),
      actions: [
        TextButton(onPressed: () => goBack<bool>(result: false), child: const Text('Huỷ')),
        TextButton(onPressed: () => goBack<bool>(result: true), child: const Text('Xoá')),
      ],
    ));
    if (confirmed != true) return;
    try {
      await VocabRepository.deleteTopic(category.id);
      await loadCategories();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> onSearchResultTap(VocabularySearchResult result) async {
    final card = result.card;
    if (card.personal != null) {
      Get.snackbar('Đã có', '"${card.text}" đã có trong thư viện của bạn (${card.personal!.statusLabel}).',
          snackPosition: SnackPosition.BOTTOM);
      return;
    }
    try {
      await VocabRepository.addWord(card.id);
      Get.snackbar('Đã lưu', 'Đã thêm "${card.text}" vào thư viện', snackPosition: SnackPosition.BOTTOM);
      onSearchChanged(currentQuery.value);
      GameService.to.refreshLibrary();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  Future<void> speakWord(String word) async {
    final match = searchResults.firstWhereOrNull((r) => r.item.word == word);
    await TtsService.to.speak(word, match?.item.ttsLocale ?? 'en-US');
  }

  /// "Ôn tập ngay": the server picks the words that are due.
  Future<void> startReviewSession() async {
    await GameService.to.refreshLibrary();
    if (GameService.to.library.value.due == 0) {
      Get.snackbar('Chưa có từ để ôn tập', 'Bạn đã ôn hết các từ đến hạn. Hãy học thêm từ mới nhé!',
          snackPosition: SnackPosition.BOTTOM);
      return;
    }
    Get.toNamed(Routes.learningSession, arguments: const LearningSessionArguments(kind: 'review'));
  }
}
