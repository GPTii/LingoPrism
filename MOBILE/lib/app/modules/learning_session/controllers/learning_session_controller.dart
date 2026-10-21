import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../data/models/api/vocab.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/game_service.dart';
import '../../../data/services/tts_service.dart';

/// A word in the session, built from the server's session item.
class LearningWord {
  LearningWord({
    required this.vocabularyId,
    required this.word,
    required this.translation,
    this.personalWordId,
    this.phonetic,
    this.status,
    this.exampleEn,
    this.exampleVi,
    this.target,
    this.imageUrl,
    this.emoji = '',
  });

  final String vocabularyId;
  final String word; // text in the language being learned
  final String translation; // Vietnamese meaning
  final String? personalWordId;
  final String? phonetic; // IPA or pinyin
  final String? status; // new | learning | mastered
  final String? exampleEn; // example sentence in the target language
  final String? exampleVi;
  final TargetText? target;
  final String? imageUrl;
  final String emoji;

  String get language => target?.language ?? 'en';
  bool get isChinese => target?.isChinese == true;
  bool get isVietnamese => language == 'vi';

  factory LearningWord.fromItem(SessionItem item) {
    final c = item.card;
    final example = c.examples.isNotEmpty ? c.examples.first : null;
    return LearningWord(
      vocabularyId: c.id.toString(),
      word: c.text,
      translation: c.isVietnameseTarget
          ? (c.emoji.isNotEmpty ? c.emoji : '🔊')
          : (c.meaningVi.isNotEmpty ? c.meaningVi : (c.english ?? '')),
      personalWordId: item.personalWordId.toString(),
      phonetic: c.target?.reading,
      status: c.personal?.status,
      exampleEn: example?.text,
      exampleVi: example?.translationVi,
      target: c.target,
      imageUrl: c.image,
      emoji: c.emoji,
    );
  }
}

/// Arguments for the session screen. The server picks the words (learn: new words, review: due words).
class LearningSessionArguments {
  const LearningSessionArguments({this.kind = 'learn', this.topic, this.size, this.title});

  final String kind; // learn | review | practice
  final int? topic;
  final int? size;
  final String? title;
}

class RoundThreeResult {
  RoundThreeResult(this.word);

  final LearningWord word;
  int attempts = 0;
  bool? firstTryCorrect;
  final List<String> questionTypes = <String>[];

  void recordAttempt({required String questionType, required bool isFirstAttempt, required bool isCorrect}) {
    attempts += 1;
    questionTypes.add(questionType);
    if (isFirstAttempt) firstTryCorrect = isCorrect;
  }
}

class RoundThreeSummary {
  RoundThreeSummary({required this.total, required this.firstTryCorrect, required this.results, this.xpEarned = 0, this.scalesEarned = 0});

  final int total;
  final int firstTryCorrect;
  final List<RoundThreeResult> results;
  final int xpEarned;
  final int scalesEarned;

  int get firstTryAccuracyPercent => total == 0 ? 0 : ((firstTryCorrect * 100) / total).round();

  List<RoundThreeResult> get difficultResults =>
      results.where((r) => r.firstTryCorrect == false || r.firstTryCorrect == null).toList();

  RoundThreeSummary copyWith({int? xpEarned, int? scalesEarned}) => RoundThreeSummary(
        total: total,
        firstTryCorrect: firstTryCorrect,
        results: results,
        xpEarned: xpEarned ?? this.xpEarned,
        scalesEarned: scalesEarned ?? this.scalesEarned,
      );
}

/// Round 1: learn cards · Round 2: flashcards (remembered / forgotten) · Round 3: quiz.
/// The first answer for each word in round 3 is the graded one that updates the review schedule.
class LearningSessionController extends GetxController {
  static const int roundLearning = 1;
  static const int roundFlashcard = 2;
  static const int roundFinalCheck = 3;

  final RxList<LearningWord> _words = <LearningWord>[].obs;
  List<LearningWord> get words => _words;
  late final String sessionType;
  late final PageController pageController;
  StudySession? _session;

  final RxBool _isLoading = true.obs;
  final RxString error = ''.obs;
  final RxInt _currentIndex = 0.obs;
  final RxInt _round = RxInt(roundLearning);
  final RxList<LearningWord> _flashcardQueue = <LearningWord>[].obs;
  final RxInt _flashcardTotal = 0.obs;
  final RxBool _flashcardBackVisible = false.obs;
  final RxInt _flashcardVersion = 0.obs;
  final RxBool _awaitingRoundThree = false.obs;
  final Map<String, RoundThreeResult> _roundThreeResults = <String, RoundThreeResult>{};
  final Map<String, DateTime> _questionShownAt = {};
  int _xpEarned = 0;
  int _scalesEarned = 0;

  bool get isLoading => _isLoading.value;
  int get currentIndex => _currentIndex.value;
  int get total => _words.length;
  int get round => _round.value;
  bool get isFlashcardRound => round == roundFlashcard;
  bool get canPrevious => !isFlashcardRound && currentIndex > 0;
  bool get canNext => !isFlashcardRound && currentIndex < total - 1;
  bool get isOnLastCard => !isFlashcardRound && currentIndex >= total - 1;
  String get currentSessionType => sessionType;
  int get totalXpEarned => _xpEarned;
  int get totalScalesEarned => _scalesEarned;
  bool get hasFlashcards => _flashcardQueue.isNotEmpty;
  int get displayTotal => isFlashcardRound ? _flashcardTotal.value : total;

  int get displayPosition {
    if (!isFlashcardRound) return currentIndex + 1;
    final totalCards = _flashcardTotal.value;
    if (totalCards == 0) return 0;
    return (totalCards - _flashcardQueue.length + 1).clamp(1, totalCards);
  }

  bool get isFlashcardBackVisible => _flashcardBackVisible.value;
  int get flashcardVersion => _flashcardVersion.value;
  bool get isAwaitingRoundThree => _awaitingRoundThree.value;
  Map<String, RoundThreeResult> get roundThreeResults => _roundThreeResults;

  LearningWord get currentWord {
    if (isFlashcardRound && _flashcardQueue.isNotEmpty) return _flashcardQueue.first;
    return _words[currentIndex.clamp(0, _words.length - 1)];
  }

  @override
  void onInit() {
    super.onInit();
    pageController = PageController();
    final args = Get.arguments is LearningSessionArguments ? Get.arguments as LearningSessionArguments : const LearningSessionArguments();
    sessionType = args.kind;
    _start(args);
  }

  Future<void> _start(LearningSessionArguments args) async {
    _isLoading.value = true;
    try {
      _session = await LearningRepository.start(args.kind, topic: args.topic, size: args.size);
      _words.assignAll(_session!.items.map(LearningWord.fromItem).where((w) => w.word.trim().isNotEmpty));
      if (args.kind == 'review') {
        startFlashcardRound();
      } else {
        _round.value = roundLearning;
      }
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
      Get.back();
      Get.snackbar('Không thể bắt đầu', error.value, snackPosition: SnackPosition.BOTTOM);
    } finally {
      _isLoading.value = false;
    }
  }

  @override
  void onClose() {
    TtsService.to.stop();
    pageController.dispose();
    super.onClose();
  }

  void onPageChanged(int index) {
    if (!isFlashcardRound) _currentIndex.value = index;
  }

  void nextWord() {
    if (canNext) pageController.nextPage(duration: const Duration(milliseconds: 240), curve: Curves.easeOut);
  }

  void previousWord() {
    if (canPrevious) pageController.previousPage(duration: const Duration(milliseconds: 240), curve: Curves.easeOut);
  }

  void startFlashcardRound() {
    if (_words.isEmpty) return;
    _round.value = roundFlashcard;
    _flashcardQueue.assignAll(_words);
    _flashcardTotal.value = _words.length;
    _flashcardBackVisible.value = false;
    _currentIndex.value = 0;
    _flashcardVersion.value = 0;
    _awaitingRoundThree.value = false;
  }

  void _logFlashcard(LearningWord w, bool remembered) {
    final s = _session;
    if (s == null || w.personalWordId == null) return;
    LearningRepository.answer(s.id,
            personalWord: int.parse(w.personalWordId!), questionType: 'flashcard', correct: remembered, firstTry: true)
        .catchError((_) {});
  }

  void markRemembered() {
    if (!isFlashcardRound || _flashcardQueue.isEmpty) return;
    final entry = _flashcardQueue.removeAt(0);
    _logFlashcard(entry, true);
    _flashcardBackVisible.value = false;
    _flashcardVersion.value++;
    if (_flashcardQueue.isEmpty) _awaitingRoundThree.value = true;
  }

  void markForgotten() {
    if (!isFlashcardRound || _flashcardQueue.isEmpty) return;
    final entry = _flashcardQueue.removeAt(0);
    _logFlashcard(entry, false);
    _flashcardQueue.add(entry);
    _flashcardBackVisible.value = false;
    _flashcardVersion.value++;
  }

  void proceedToRoundThree() {
    _awaitingRoundThree.value = false;
    _round.value = roundFinalCheck;
  }

  void toggleFlashcardSide() {
    if (isFlashcardRound && _flashcardQueue.isNotEmpty) _flashcardBackVisible.toggle();
  }

  Future<void> speakWord(LearningWord word) async {
    if (word.word.trim().isEmpty) return;
    await TtsService.to.speak(word.word, word.target?.ttsLocale ?? 'en-US');
  }

  void markQuestionShown(LearningWord word) => _questionShownAt[word.vocabularyId] = DateTime.now();

  void recordRoundThreeResult({
    required LearningWord word,
    required String questionType,
    required bool isFirstAttempt,
    required bool isCorrect,
  }) {
    final key = word.personalWordId ?? word.vocabularyId;
    _roundThreeResults.putIfAbsent(key, () => RoundThreeResult(word))
        .recordAttempt(questionType: questionType, isFirstAttempt: isFirstAttempt, isCorrect: isCorrect);
    final s = _session;
    if (s == null || word.personalWordId == null) return;
    final shown = _questionShownAt[word.vocabularyId];
    LearningRepository.answer(
      s.id,
      personalWord: int.parse(word.personalWordId!),
      questionType: questionType,
      correct: isCorrect,
      firstTry: isFirstAttempt,
      graded: isFirstAttempt,
      responseMs: shown == null ? null : DateTime.now().difference(shown).inMilliseconds,
    ).catchError((_) {});
  }

  RoundThreeSummary buildRoundThreeSummary() {
    for (final w in _words) {
      _roundThreeResults.putIfAbsent(w.personalWordId ?? w.vocabularyId, () => RoundThreeResult(w));
    }
    final entries = _roundThreeResults.values.toList(growable: false);
    final firstTry = entries.where((r) => r.firstTryCorrect == true).length;
    return RoundThreeSummary(total: entries.length, firstTryCorrect: firstTry, results: entries);
  }

  /// XP is computed by the server when the session is finished.
  Future<void> awardXp({required int amount, required String sourceType, required String action, int wordsCount = 1,
      Map<String, dynamic>? metadata, String? sourceId}) async {}

  Future<RoundThreeSummary> finalizeRoundThree() async {
    final summary = buildRoundThreeSummary();
    final s = _session;
    if (s == null) return summary;
    try {
      // let pending answer requests land before closing the session
      await Future.delayed(const Duration(milliseconds: 300));
      final result = await LearningRepository.finish(s.id);
      _xpEarned = result.xp;
      _scalesEarned = result.correctFirstTry;
      GameService.to.refreshAll();
    } catch (_) {}
    return summary.copyWith(xpEarned: _xpEarned, scalesEarned: _scalesEarned);
  }
}
