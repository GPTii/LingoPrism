import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../data/models/api/vocab.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/game_service.dart';
import '../../../data/services/tts_service.dart';
import '../../../routes/app_pages.dart';
import '../../learning_session/controllers/learning_session_controller.dart';
import '../../vocabulary_flashcard/bindings/vocabulary_flashcard_binding.dart';
import '../../vocabulary_flashcard/views/vocabulary_flashcard_view.dart';

enum VocabularyLearningStatus { notStarted, learning, learned }

/// One verified word of a topic, as shown on the topic screen and flashcards.
class VocabularyTopicItem {
  VocabularyTopicItem({
    required this.word,
    required this.ipa,
    required this.translation,
    required this.exampleEn,
    required this.exampleVi,
    required this.status,
    this.card,
  });

  final String word;
  final String ipa; // IPA (English) or pinyin (Chinese)
  final String translation;
  final String exampleEn; // example in the target language
  final String exampleVi;
  final VocabularyLearningStatus status;
  final WordCard? card;

  String get language => card?.target?.language ?? 'en';
  String get ttsLocale => card?.target?.ttsLocale ?? 'en-US';

  factory VocabularyTopicItem.fromCard(WordCard c) {
    final ex = c.examples.isNotEmpty ? c.examples.first : null;
    final status = switch (c.personal?.status) {
      'learning' => VocabularyLearningStatus.learning,
      'mastered' => VocabularyLearningStatus.learned,
      _ => VocabularyLearningStatus.notStarted,
    };
    return VocabularyTopicItem(
      word: c.text,
      ipa: c.target?.reading ?? '',
      translation: c.isVietnameseTarget ? c.emoji : c.meaningVi,
      exampleEn: ex?.text ?? '',
      exampleVi: c.isVietnameseTarget
          ? ''
          : (ex?.translationVi.isNotEmpty ?? false) ? ex!.translationVi : (ex?.translationEn ?? ''),
      status: status,
      card: c,
    );
  }
}

class VocabularyTopicArguments {
  VocabularyTopicArguments({required this.topic});

  final Topic topic;
}

class VocabularyTopicController extends GetxController {
  late final Topic topic;
  String get topicName => topic.nameVi;
  final RxList<VocabularyTopicItem> items = <VocabularyTopicItem>[].obs;
  final RxBool isLoading = false.obs;

  int get totalWords => items.length;

  @override
  void onInit() {
    super.onInit();
    final args = Get.arguments;
    topic = args is VocabularyTopicArguments ? args.topic : (args as Topic);
    load();
  }

  Future<void> load() async {
    isLoading.value = true;
    try {
      final cards = topic.isSystem ? await VocabRepository.topicWords(topic.id) : await VocabRepository.myWords(topic: topic.id);
      items.assignAll(cards.where((c) => c.target != null).map(VocabularyTopicItem.fromCard));
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> playAudio(VocabularyTopicItem item) => TtsService.to.speak(item.word, item.ttsLocale);

  void onFlashcardPressed() {
    if (items.isEmpty) {
      Get.snackbar('Flashcard', 'Chưa có thẻ từ vựng để ôn tập.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    Get.to(() => const VocabularyFlashcardView(),
        binding: VocabularyFlashcardBinding(), arguments: {'items': items.toList(), 'topicName': topicName});
  }

  /// Practice the whole topic as a study session (flashcards + quiz, graded by the server).
  void onPracticePressed() {
    Get.toNamed(Routes.learningSession, arguments: LearningSessionArguments(kind: 'practice', topic: topic.id, size: 15));
  }

  /// Sentence practice with verified example sentences containing this topic's words.
  void onSentencePressed() {
    Get.toNamed(Routes.sentencePractice, arguments: {'topic': topic.id, 'title': 'Luyện câu · $topicName'});
  }

  Future<void> saveTopic() async {
    try {
      final added = await VocabRepository.saveTopic(topic.id);
      Get.snackbar('Đã lưu', 'Đã thêm $added từ vào thư viện của bạn', snackPosition: SnackPosition.BOTTOM);
      await load();
      GameService.to.refreshLibrary();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  /// Add verified words to this topic: search the vocabulary and tap to add.
  void onAddVocabularyPressed() {
    if (topic.isSystem) {
      saveTopic();
      return;
    }
    final query = TextEditingController();
    final results = <WordCard>[].obs;
    Get.bottomSheet(
      Container(
        height: Get.height * 0.75,
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
        decoration: const BoxDecoration(color: Colors.white, borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
        child: Column(
          children: [
            const Text('Thêm từ vào chủ đề', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            TextField(
              controller: query,
              autofocus: true,
              decoration: const InputDecoration(hintText: 'Tìm từ (Việt / Anh / Trung)…', prefixIcon: Icon(Icons.search)),
              onSubmitted: (v) async => results.assignAll(await VocabRepository.search(v.trim())),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: Obx(() => ListView(
                    children: [
                      for (final c in results)
                        ListTile(
                          title: Text(c.text, locale: null),
                          subtitle: Text('${c.target?.reading ?? ''}  ·  ${c.meaningVi}'),
                          trailing: const Icon(Icons.add_circle_outline),
                          onTap: () async {
                            try {
                              await VocabRepository.addWord(c.id, topic: topic.id);
                              Get.back();
                              await load();
                            } catch (e) {
                              Get.snackbar('Lỗi', ApiClient.toApiException(e).message);
                            }
                          },
                        ),
                    ],
                  )),
            ),
          ],
        ),
      ),
      isScrollControlled: true,
    );
  }

  /// Verified data is not edited by learners – they report errors instead.
  Future<void> onEditVocabulary(int index) async {
    final item = items[index];
    final card = item.card;
    if (card == null) return;
    const reasons = {
      'wrong_character': 'Sai mặt chữ',
      'wrong_pronunciation': 'Sai phiên âm / phát âm',
      'wrong_meaning': 'Sai nghĩa',
      'wrong_example': 'Câu ví dụ sai',
      'other': 'Khác',
    };
    final details = TextEditingController();
    final reason = await Get.dialog<String>(SimpleDialog(
      title: Text('Báo lỗi: ${item.word}'),
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: TextField(controller: details, decoration: const InputDecoration(hintText: 'Mô tả (không bắt buộc)')),
        ),
        for (final e in reasons.entries) SimpleDialogOption(onPressed: () => Get.back(result: e.key), child: Text(e.value)),
      ],
    ));
    if (reason == null) return;
    try {
      await VocabRepository.report(card.id, card.target?.id, reason, details.text.trim());
      Get.snackbar('Cảm ơn bạn!', 'Đội ngũ sẽ kiểm tra từ này sớm nhất.', snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  /// Remove the word from the learner's library.
  Future<void> onDeleteVocabulary(int index) async {
    final personal = items[index].card?.personal;
    if (personal == null) {
      Get.snackbar('Thông báo', 'Từ này chưa có trong thư viện của bạn.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    try {
      await VocabRepository.removeWord(personal.id);
      await load();
      GameService.to.refreshLibrary();
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  String statusLabel(VocabularyLearningStatus status) => switch (status) {
        VocabularyLearningStatus.notStarted => 'chưa học',
        VocabularyLearningStatus.learning => 'đang học',
        VocabularyLearningStatus.learned => 'đã học',
      };
}
