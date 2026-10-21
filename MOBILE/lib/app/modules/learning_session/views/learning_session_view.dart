import 'dart:math' as math;

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/widgets/target_word.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_text_styles.dart';
import '../controllers/learning_session_controller.dart';
import '../../home/controllers/learning_tab_controller.dart';
import '../../../core/widgets/word_picture.dart';
import '../../../core/widgets/prismo.dart';
import '../../../core/widgets/prism_effects.dart';

// --- Start of Round 3 Models ---
// Note: These model classes should ideally be in their own file (e.g., in app/data/models).
// They are placed here for simplicity of this implementation.

/// Base class for a question in Round 3.
abstract class RoundThreeQuestion {
  RoundThreeQuestion({required this.learningWord})
      : wordKey = learningWord.word,
        vocabularyId = learningWord.vocabularyId,
        personalWordId = learningWord.personalWordId;

  final LearningWord learningWord;
  final String wordKey; // dùng để gom các câu cùng một từ
  final String vocabularyId;
  final String? personalWordId;
}

/// Model for a Multiple Choice question.
class MultipleChoiceQuestion extends RoundThreeQuestion {
  final String questionWord; // The word to be translated (e.g., in English)
  final List<String> options; // A list of 4 possible translations
  final String correctOption; // The correct translation

  MultipleChoiceQuestion({
    required super.learningWord,
    required this.questionWord,
    required this.options,
    required this.correctOption,
  });
}

/// Model for a Matching question.
class MatchingQuestion extends RoundThreeQuestion {
  /// A map of word pairs to be matched. Key is the source word, value is the target word.
  final Map<String, String> pairs;

  MatchingQuestion({required super.learningWord, required this.pairs});
}

/// Model for a Scramble (word formation) question.
class ScrambleQuestion extends RoundThreeQuestion {
  final String correctWord; // The word in its correct form
  final String scrambledWord; // The word with its letters scrambled

  ScrambleQuestion({
    required super.learningWord,
    required this.correctWord,
    required this.scrambledWord,
  });
}

/// Model for a Listen & Type question.
class ListenAndTypeQuestion extends RoundThreeQuestion {
  ListenAndTypeQuestion({required super.learningWord});
}

// --- End of Round 3 Models ---

class LearningSessionView extends GetView<LearningSessionController> {
  const LearningSessionView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primarySoft,
      appBar: AppBar(
        backgroundColor: AppColors.primarySoft,
        elevation: 0,
        leading: IconButton(
          onPressed: Get.back,
          icon: Icon(Icons.arrow_back_ios_new_rounded,
              color: AppColors.textPrimary),
        ),
        titleSpacing: 0,
        title: Obx(
          () => Text(
            controller.currentSessionType == 'review'
                ? 'Ôn tập: vòng ${controller.round}'
                : 'Học từ mới: vòng ${controller.round}',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 20.sp,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
      body: Obx(
        () {
          if (controller.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (controller.words.isEmpty) {
            return Center(
              child: Text(
                'Không có từ nào để học',
                style: TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 16.sp,
                ),
              ),
            );
          }

          final showProgress =
              controller.round != LearningSessionController.roundFinalCheck;

          // Every text in the session inherits the learned language's locale (correct CJK glyphs).
          return DefaultTextStyle.merge(
            style: TextStyle(locale: localeFor(controller.words.first.language)),
            child: Column(
            children: [
              if (showProgress) ...[
                SizedBox(height: 12.h),
                Padding(
                  padding: EdgeInsets.symmetric(horizontal: 20.w),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Tiến độ',
                            style: TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 14.sp,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          Text(
                            '${controller.displayPosition}/${controller.displayTotal}',
                            style: TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 16.sp,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                      SizedBox(height: 8.h),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(18.r),
                        child: Builder(builder: (_) {
                          final total = controller.displayTotal;
                          final position = controller.displayPosition;
                          final clamped = total == 0
                              ? 0
                              : (position > total ? total : position);
                          final value =
                              total == 0 ? 0.0 : clamped / total.toDouble();
                          return LinearProgressIndicator(
                            value: value,
                            minHeight: 10.h,
                            backgroundColor: AppColors.surface,
                            valueColor: AlwaysStoppedAnimation(
                              AppColors.primary,
                            ),
                          );
                        }),
                      ),
                    ],
                  ),
                ),
              ] else
                SizedBox(height: 20.h),
              SizedBox(height: 18.h),
              Expanded(
                child: controller.isFlashcardRound
                    ? _FlashcardContent(controller: controller)
                    : controller.round ==
                            LearningSessionController.roundFinalCheck
                        ? _RoundThreeContent(controller: controller)
                        : _RoundOneContent(controller: controller),
              ),
              if (!controller.isFlashcardRound &&
                  controller.round !=
                      LearningSessionController.roundFinalCheck) ...[
                Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: 20.w,
                    vertical: 16.h,
                  ),
                  child: Row(
                    children: [
                      _NavigationButton(
                        icon: Icons.arrow_back_ios_new_rounded,
                        onTap: controller.canPrevious
                            ? controller.previousWord
                            : null,
                      ),
                      SizedBox(width: 12.w),
                      _NavigationButton(
                        icon: Icons.arrow_forward_ios_rounded,
                        onTap: controller.canNext ? controller.nextWord : null,
                      ),
                    ],
                  ),
                ),
                Padding(
                  padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 24.h),
                  child: SizedBox(
                    width: double.infinity,
                    height: 52.h,
                    child: ElevatedButton(
                      onPressed: controller.isOnLastCard
                          ? controller.startFlashcardRound
                          : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: controller.isOnLastCard
                            ? AppColors.primary
                            : AppColors.surfaceMuted,
                        foregroundColor: controller.isOnLastCard
                            ? Colors.white
                            : AppColors.textSecondary,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14.r),
                        ),
                        textStyle: TextStyle(
                          fontSize: 15.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      child: const Text('Kiểm tra lại bằng Flashcard'),
                    ),
                  ),
                ),
              ],
              if (controller.isFlashcardRound &&
                  !controller.isAwaitingRoundThree)
                Padding(
                  padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 28.h),
                  child: Row(
                    children: [
                      Expanded(
                        child: ElevatedButton(
                          onPressed: controller.hasFlashcards
                              ? controller.markForgotten
                              : null,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primarySoft,
                            foregroundColor: AppColors.primary,
                            elevation: 0,
                            padding: EdgeInsets.symmetric(vertical: 14.h),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14.r),
                            ),
                            textStyle: TextStyle(
                              fontSize: 15.sp,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          child: const Text('Chưa nhớ'),
                        ),
                      ),
                      SizedBox(width: 12.w),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: controller.hasFlashcards
                              ? controller.markRemembered
                              : null,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primary,
                            foregroundColor: Colors.white,
                            elevation: 0,
                            padding: EdgeInsets.symmetric(vertical: 14.h),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14.r),
                            ),
                            textStyle: TextStyle(
                              fontSize: 15.sp,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          child: const Text('Đã nhớ'),
                        ),
                      ),
                    ],
                  ),
                ),
              if (controller.isFlashcardRound &&
                  controller.isAwaitingRoundThree)
                Padding(
                  padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 28.h),
                  child: SizedBox(
                    width: double.infinity,
                    height: 56.h,
                    child: ElevatedButton(
                      onPressed: controller.proceedToRoundThree,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.surface,
                        foregroundColor: AppColors.primary,
                        elevation: 0,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14.r),
                        ),
                        textStyle: TextStyle(
                          fontSize: 16.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      child: const Text('Tiếp tục'),
                    ),
                  ),
                ),
            ],
          ),
          );
        },
      ),
    );
  }
}

class _RoundOneContent extends StatelessWidget {
  const _RoundOneContent({required this.controller});

  final LearningSessionController controller;

  @override
  Widget build(BuildContext context) {
    return PageView.builder(
      controller: controller.pageController,
      onPageChanged: controller.onPageChanged,
      itemCount: controller.total,
      physics: const ClampingScrollPhysics(),
      itemBuilder: (context, index) {
        final word = controller.words[index];
        return _LearningCard(
          word: word,
          onSpeak: () => controller.speakWord(word),
        );
      },
    );
  }
}

class _RoundThreeContent extends StatefulWidget {
  const _RoundThreeContent({required this.controller});

  final LearningSessionController controller;

  @override
  State<_RoundThreeContent> createState() => _RoundThreeContentState();
}

class _RoundThreeContentState extends State<_RoundThreeContent> {
  late final PageController _pageController;
  late List<RoundThreeQuestion> _questions;
  // Single SFX player; we stop before play to avoid overlap/timeouts.
  final AudioPlayer _sfxPlayer = AudioPlayer();
  // Use asset-relative paths; the player will prepend "assets/" automatically.
  final AssetSource _correctSource = AssetSource('sounds/correct.wav');
  final AssetSource _wrongSource = AssetSource('sounds/wrong.wav');
  final RxBool _canContinue = false.obs;
  int _currentIndex = 0;
  bool _retryPhase = false;
  final Set<String> _wrongWords = <String>{};
  final Set<String> _awarded = <String>{};
  // Lưu kết quả lượt đầu theo từng từ: true = đúng, false = sai
  final Map<String, bool> _firstPassResult = <String, bool>{};
  VoidCallback? _primaryAction;

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    _questions = _buildQuestionsFromWords(widget.controller.words);
    _configurePlayer(_sfxPlayer);
  }

  List<RoundThreeQuestion> _buildQuestionsFromWords(List<LearningWord> words) {
    // Chỉ tạo đúng số câu hỏi bằng số lượng từ vựng.
    // Random loại câu giữa: trắc nghiệm, nối cặp, sắp xếp chữ.
    final rnd = math.Random();
    final translations = words.map((w) => w.translation).toList();
    final questions = <RoundThreeQuestion>[];
    for (final w in words) {
      final type = rnd.nextInt(4); // 0: MC, 1: Matching, 2: Scramble, 3: Listen & type
      if (type == 0 || words.length < 3) {
        // Multiple choice
        final opts = <String>{w.translation};
        while (opts.length < 4 && opts.length < translations.length) {
          opts.add(translations[rnd.nextInt(translations.length)]);
        }
        final list = opts.toList()..shuffle(rnd);
        questions.add(MultipleChoiceQuestion(
          learningWord: w,
          questionWord: w.word,
          options: list,
          correctOption: w.translation,
        ));
      } else if (type == 1) {
        // Matching: tạo 2-4 cặp (tùy dữ liệu), luôn gồm từ hiện tại
        final others = words.where((x) => x.word != w.word).toList()..shuffle(rnd);
        final picksCount = math.min(3, others.length);
        final picks = [w, ...others.take(picksCount)];
        final pairs = <String, String>{
          for (final p in picks) p.word: p.translation,
        };
        questions.add(MatchingQuestion(learningWord: w, pairs: pairs));
      } else if (type == 2) {
        // Scramble
        final chars = w.word.split('');
        if (chars.length > 1) {
          // đảm bảo khác thứ tự ít nhất một chút
          do {
            chars.shuffle(rnd);
          } while (chars.join() == w.word && chars.length > 1);
        }
        final scrambled = chars.join();
        questions.add(ScrambleQuestion(
          learningWord: w,
          correctWord: w.word,
          scrambledWord: scrambled,
        ));
      } else if (type == 3) {
        // Listen & type
        questions.add(ListenAndTypeQuestion(learningWord: w));
      }
    }
    return questions;
  }

  void _onQuestionCompleted({
    required RoundThreeQuestion question,
    required bool isCorrect,
    required String type,
  }) {
    final learningWord = question.learningWord;
    final wordKey = learningWord.word;
    final vocabularyId = learningWord.vocabularyId;

    final hadFirstResult = _firstPassResult.containsKey(wordKey);
    final isFirstAttempt = !_retryPhase && !hadFirstResult;

    _canContinue.value = true;
    _updatePrimaryAction(null);
    _playFeedbackSound(isCorrect);
    if (mounted) PrismoReaction.show(context, correct: isCorrect);

    if (isFirstAttempt) {
      _firstPassResult[wordKey] = isCorrect;
      if (!isCorrect) {
        _wrongWords.add(wordKey);
      } else {
          if (!_awarded.contains(vocabularyId)) {
            _awarded.add(vocabularyId);
            int xp = 0;
            if (type == 'mc') {
              xp = 3;
            } else if (type == 'match') {
              xp = 5;
            } else if (type == 'scramble') {
              xp = 7;
            } else if (type == 'listen') {
              xp = 6;
            } else if (type == 'misspelled') {
              xp = 4;
            }
            if (xp > 0) {
            final sourceType =
                widget.controller.currentSessionType == 'review' ? 'review' : 'learning';
            widget.controller.awardXp(
              amount: xp,
              sourceType: sourceType,
              action: 'round3_$type',
              wordsCount: 1,
              metadata: {
                'question_type': type,
              },
              sourceId: learningWord.personalWordId,
            );
          }
        }
      }
    } else {
      if (_retryPhase && !isCorrect) {
      }
    }

    widget.controller.recordRoundThreeResult(
      word: learningWord,
      questionType: type,
      isFirstAttempt: isFirstAttempt,
      isCorrect: isCorrect,
    );
  }

  Future<void> _playFeedbackSound(bool isCorrect) async {
    final source = isCorrect ? _correctSource : _wrongSource;
    try {
      await _sfxPlayer.stop();
      await _sfxPlayer.play(
        source,
        volume: 0.9,
        mode: PlayerMode.lowLatency,
      );
    } catch (e) {
      Get.log('Play sound error: $e');
    }
  }

  void _configurePlayer(AudioPlayer player) {
    player
      ..setPlayerMode(PlayerMode.lowLatency)
      ..setReleaseMode(ReleaseMode.stop)
      ..setAudioContext(
        const AudioContext(
          iOS: AudioContextIOS(
            category: AVAudioSessionCategory.ambient,
          ),
          android: AudioContextAndroid(
            isSpeakerphoneOn: false,
            stayAwake: false,
            contentType: AndroidContentType.sonification,
            usageType: AndroidUsageType.assistanceSonification,
            audioFocus: AndroidAudioFocus.gainTransientMayDuck,
          ),
        ),
      );
  }

  void _updatePrimaryAction(VoidCallback? action) {
    if (!mounted || _primaryAction == action) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || _primaryAction == action) return;
      setState(() {
        _primaryAction = action;
      });
    });
  }

  bool _sessionFinalized = false;

  @override
  void dispose() {
    _pageController.dispose();
    _sfxPlayer.dispose();
    super.dispose();
  }

  Future<void> _finalizeSession() async {
    if (_sessionFinalized) return;
    _sessionFinalized = true;

    RoundThreeSummary summary;
    try {
      summary = await widget.controller.finalizeRoundThree();
    } catch (error, stackTrace) {
      Get.log('Finalize round three error: $error');
      debugPrintStack(stackTrace: stackTrace);
      summary = widget.controller
          .buildRoundThreeSummary()
          .copyWith(
            xpEarned: widget.controller.totalXpEarned,
            scalesEarned: widget.controller.totalScalesEarned,
          );
    }

    if (!mounted) return;
    _showCompletionPage(summary: summary);
  }

  Future<void> _goNext() async {
    if (!_canContinue.value) return;
    if (_currentIndex < _questions.length - 1) {
      _pageController.nextPage(duration: const Duration(milliseconds: 240), curve: Curves.easeOut);
      setState(() {
        _currentIndex++;
      });
      _primaryAction = null;
      _canContinue.value = false;
      return;
    }
    // reached end of current batch
    if (_wrongWords.isNotEmpty && !_retryPhase) {
      // build one more question per wrong word (multiple choice)
      final words = widget.controller.words.where((w) => _wrongWords.contains(w.word)).toList();
      setState(() {
        _questions = [
          ..._questions,
          ...words.map((w) {
            final rnd = math.Random();
            final translations = widget.controller.words.map((e) => e.translation).toList();
            final opts = <String>{w.translation};
            while (opts.length < 4 && opts.length < translations.length) {
              opts.add(translations[rnd.nextInt(translations.length)]);
            }
            final list = opts.toList()..shuffle(rnd);
            return MultipleChoiceQuestion(
              learningWord: w,
              questionWord: w.word,
              options: list,
              correctOption: w.translation,
            );
          }),
        ];
        _retryPhase = true;
        _wrongWords.clear();
        _currentIndex++;
      });
      _primaryAction = null;
      _canContinue.value = false;
      _pageController.nextPage(duration: const Duration(milliseconds: 240), curve: Curves.easeOut);
      return;
    }
    // Nếu đã qua lượt ôn lại và không còn sai -> hoàn thành
    if (_retryPhase) {
      await _finalizeSession();
      return;
    }

    // Trường hợp tất cả câu đều đúng ngay từ lượt đầu
    if (!_retryPhase && _wrongWords.isEmpty) {
      await _finalizeSession();
      return;
    }
  }

  void _showCompletionDialog({required int percent}) {
    // legacy dialog (unused after fullscreen change)
    Get.back<void>();
  }

  void _showCompletionPage({required RoundThreeSummary summary}) {
    Get.off(() => _LessonCompletedScreen(summary: summary));
  }

  @override
  Widget build(BuildContext context) {
    Widget buildQuestion(RoundThreeQuestion q) {
      if (q is MultipleChoiceQuestion) {
        return _MultipleChoiceQuestionWidget(
          question: q,
          onCompleted: (correct) => _onQuestionCompleted(
            question: q,
            isCorrect: correct,
            type: 'mc',
          ),
        );
      } else if (q is MatchingQuestion) {
        return _MatchingQuestionWidget(
          question: q,
          onCompleted: (correct) => _onQuestionCompleted(
            question: q,
            isCorrect: correct,
            type: 'match',
          ),
        );
      } else if (q is ScrambleQuestion) {
        return _ScrambleQuestionWidget(
          question: q,
          onCompleted: (correct) => _onQuestionCompleted(
            question: q,
            isCorrect: correct,
            type: 'scramble',
          ),
          onPrimaryActionChanged: _updatePrimaryAction,
        );
      } else if (q is ListenAndTypeQuestion) {
        return _ListenAndTypeQuestionWidget(
          question: q,
          onCompleted: (correct) => _onQuestionCompleted(
            question: q,
            isCorrect: correct,
            type: 'listen',
          ),
          onPrimaryActionChanged: _updatePrimaryAction,
          onSpeak: () => widget.controller.speakWord(q.learningWord),
        );
      }
      return const SizedBox.shrink();
    }

    return Column(
      children: [
        Expanded(
          child: PageView.builder(
            controller: _pageController,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _questions.length,
            itemBuilder: (_, i) => buildQuestion(_questions[i]),
          ),
        ),
        Padding(
          padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 20.h),
          child: Obx(() {
            final canContinue = _canContinue.value;
            final hasPrimaryAction = _primaryAction != null;
            final enabled = canContinue || hasPrimaryAction;
            final label = canContinue ? 'Tiếp tục' : 'Kiểm tra';
            return SizedBox(
              width: double.infinity,
              height: 56.h,
              child: ElevatedButton(
                onPressed: enabled
                    ? () {
                        if (canContinue) {
                          _goNext();
                        } else {
                          _primaryAction?.call();
                        }
                      }
                    : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: enabled ? AppColors.primary : AppColors.primaryTint,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14.r)),
                  textStyle: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700),
                ),
                child: Text(label),
              ),
            );
          }),
        ),
      ],
    );
  }
}

// --- Widgets for Round 3 Question Types ---

class _MultipleChoiceQuestionWidget extends StatefulWidget {
  final MultipleChoiceQuestion question;
  final void Function(bool correct) onCompleted;

  const _MultipleChoiceQuestionWidget({required this.question, required this.onCompleted});

  @override
  State<_MultipleChoiceQuestionWidget> createState() => _MultipleChoiceQuestionWidgetState();
}

class _MultipleChoiceQuestionWidgetState extends State<_MultipleChoiceQuestionWidget> {
  String? _selectedOption;
  bool? _isCorrect;

  void _handleAnswer(String option) {
    if (_selectedOption != null) return; // Prevent changing answer

    setState(() {
      _selectedOption = option;
      _isCorrect = option == widget.question.correctOption;
    });
    // Chốt kết quả ngay lần chọn đầu tiên (không cho chọn lại).
    Future.delayed(const Duration(milliseconds: 50), () {
      if (!mounted) return;
      widget.onCompleted(_isCorrect == true);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 20.w),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            "'${widget.question.questionWord}' có nghĩa là gì?",
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 24.sp, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
          ),
          SizedBox(height: 40.h),
          ...widget.question.options.map((option) {
            Color? buttonColor = AppColors.surface;
            Color? textColor = AppColors.textPrimary;
            Color borderColor = AppColors.lineStrong;

            if (_selectedOption != null) {
              if (option == widget.question.correctOption) {
                buttonColor = AppColors.successSoft;
                textColor = AppColors.success;
                borderColor = AppColors.beamMint;
              } else if (option == _selectedOption) {
                buttonColor = AppColors.errorSoft;
                textColor = AppColors.error;
                borderColor = AppColors.error;
              }
            }

            return Padding(
              padding: EdgeInsets.symmetric(vertical: 8.h),
              child: ElevatedButton(
                onPressed: () => _handleAnswer(option),
                style: ElevatedButton.styleFrom(
                  backgroundColor: buttonColor,
                  foregroundColor: textColor,
                  elevation: 0,
                  minimumSize: Size(double.infinity, 52.h),
                  side: BorderSide(color: borderColor, width: 1.5),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14.r)),
                  textStyle: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w600),
                ),
                child: Text(option),
              ),
            );
          }),
        ],
      ),
    );
  }
}

class _MatchingQuestionWidget extends StatefulWidget {
  final MatchingQuestion question;
  final void Function(bool correct) onCompleted;

  const _MatchingQuestionWidget({required this.question, required this.onCompleted});

  @override
  _MatchingQuestionWidgetState createState() => _MatchingQuestionWidgetState();
}

class _MatchingQuestionWidgetState extends State<_MatchingQuestionWidget> {
  late List<String> _englishWords;
  late List<String> _vietnameseWords;
  
  String? _selectedEnglish;
  String? _selectedVietnamese;

  final Map<String, String> _correctMatches = {};
  final Set<String> _wrongFlash = <String>{};
  bool _madeMistake = false; // nếu từng bắt cặp sai -> câu này tính sai

  @override
  void initState() {
    super.initState();
    _englishWords = widget.question.pairs.keys.toList()..shuffle();
    _vietnameseWords = widget.question.pairs.values.toList()..shuffle();
  }

  void _onEnglishWordSelected(String word) {
    setState(() {
      _selectedEnglish = word;
      if (_selectedVietnamese != null) _checkMatch();
    });
  }

  void _onVietnameseWordSelected(String word) {
    setState(() {
      _selectedVietnamese = word;
      if (_selectedEnglish != null) _checkMatch();
    });
  }

  void _checkMatch() {
    final en = _selectedEnglish!;
    final vi = _selectedVietnamese!;
    final ok = widget.question.pairs[en] == vi;
    if (ok) {
      _correctMatches[en] = vi;
      // Reset selection
      setState(() {
        _selectedEnglish = null;
        _selectedVietnamese = null;
      });
      if (_correctMatches.length == widget.question.pairs.length) {
        widget.onCompleted(!_madeMistake);
      }
    } else {
      setState(() {
        _wrongFlash
          ..add(en)
          ..add(vi);
        _madeMistake = true;
      });
      Future.delayed(const Duration(milliseconds: 500), () {
        if (!mounted) return;
        setState(() {
          _wrongFlash
            ..remove(en)
            ..remove(vi);
          _selectedEnglish = null;
          _selectedVietnamese = null;
        });
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(16.w),
      child: Column(
        children: [
          Text("Nối các cặp từ tương ứng", style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.bold)),
          SizedBox(height: 20.h),
          Expanded(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: _buildWordList(
                    _englishWords,
                    _selectedEnglish,
                    _onEnglishWordSelected,
                    (word) => _correctMatches.containsKey(word),
                  ),
                ),
                SizedBox(width: 10.w),
                Expanded(
                  child: _buildWordList(
                    _vietnameseWords,
                    _selectedVietnamese,
                    _onVietnameseWordSelected,
                    (word) => _correctMatches.containsValue(word),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWordList(
    List<String> words,
    String? selected,
    Function(String) onSelected,
    bool Function(String) isMatched,
  ) {
    return ListView.separated(
      padding: EdgeInsets.symmetric(vertical: 6.h, horizontal: 2.w),
      itemCount: words.length,
      separatorBuilder: (_, __) => SizedBox(height: 60.h),
      itemBuilder: (_, index) {
        final word = words[index];
        final bool matched = isMatched(word);
        final bool isSelected = selected == word;
        final bool isWrong = _wrongFlash.contains(word);

        Color bgColor = Colors.white;
        if (matched) {
          bgColor = AppColors.successSoft;
        } else if (isWrong) {
          bgColor = AppColors.errorSoft;
        } else if (isSelected) {
          bgColor = AppColors.primarySoft;
        }

        final Color fgColor = matched
            ? AppColors.success
            : isWrong
                ? AppColors.error
                : AppColors.textPrimary;

        return Padding(
          padding: EdgeInsets.symmetric(horizontal: 2.w),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: matched ? null : () => onSelected(word),
              style: ElevatedButton.styleFrom(
                backgroundColor: bgColor,
                foregroundColor: fgColor,
                disabledBackgroundColor: bgColor,
                disabledForegroundColor: fgColor,
                elevation: 0,
                minimumSize: Size.fromHeight(54.h),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16.r),
                ),
              ),
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 6.h),
                child: Text(
                  word,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: fgColor,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}


class _ScrambleQuestionWidget extends StatefulWidget {
  final ScrambleQuestion question;
  final void Function(bool correct) onCompleted;
  final ValueChanged<VoidCallback?>? onPrimaryActionChanged;

  const _ScrambleQuestionWidget({
    required this.question,
    required this.onCompleted,
    this.onPrimaryActionChanged,
  });

  @override
  _ScrambleQuestionWidgetState createState() => _ScrambleQuestionWidgetState();
}

class _ScrambleQuestionWidgetState extends State<_ScrambleQuestionWidget> {
  final _textController = TextEditingController();
  bool? _isCorrect;

  @override
  void initState() {
    super.initState();
    widget.onPrimaryActionChanged?.call(_checkAnswer);
  }

  @override
  void didUpdateWidget(covariant _ScrambleQuestionWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.question != widget.question) {
      _textController
        ..text = ''
        ..selection = const TextSelection.collapsed(offset: 0);
      _isCorrect = null;
      widget.onPrimaryActionChanged?.call(_checkAnswer);
    } else if (oldWidget.onPrimaryActionChanged != widget.onPrimaryActionChanged) {
      widget.onPrimaryActionChanged?.call(_checkAnswer);
    }
  }

  @override
  void dispose() {
    widget.onPrimaryActionChanged?.call(null);
    _textController.dispose();
    super.dispose();
  }

  void _checkAnswer() {
    if (_isCorrect != null) return;
    final answer = _textController.text.trim();
    setState(() {
      _isCorrect = answer.toLowerCase() == widget.question.correctWord.toLowerCase();
    });
    // Mark completed (user đã kiểm tra). Nút "Tiếp tục" sẽ đưa sang câu kế tiếp
    widget.onCompleted(_isCorrect ?? false);
    widget.onPrimaryActionChanged?.call(null);
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final content = Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Sắp xếp các chữ cái sau để tạo thành một từ đúng:',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 18.sp),
            ),
            SizedBox(height: 20.h),
            Container(
              padding: EdgeInsets.all(12.w),
              decoration: BoxDecoration(
                color: AppColors.primarySoft,
                borderRadius: BorderRadius.circular(12.r),
              ),
              child: Text(
                widget.question.scrambledWord,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 24.sp,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 8,
                  color: Colors.blue.shade800,
                ),
              ),
            ),
            SizedBox(height: 40.h),
            TextField(
              controller: _textController,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w600),
              onSubmitted: (_) => _checkAnswer(),
              decoration: InputDecoration(
                hintText: 'Câu trả lời của bạn',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16.r),
                  borderSide: BorderSide(color: AppColors.textHint),
                ),
                filled: true,
                fillColor: AppColors.surface,
                suffixIcon: _isCorrect == null
                    ? null
                    : Icon(
                        _isCorrect! ? Icons.check_circle : Icons.cancel,
                        color: _isCorrect! ? AppColors.success : Colors.red,
                      ),
              ),
            ),
            SizedBox(height: 30.h),
            if (_isCorrect == false) ...[
              SizedBox(height: 12.h),
              Text(
                'Đáp án đúng: ${widget.question.correctWord}',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: AppColors.error,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
            SizedBox(height: 24.h),
            Text(
              'Nhấn "Kiểm tra" để chấm điểm, sau đó chọn "Tiếp tục" để sang câu mới.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary),
            ),
          ],
        );

        return SingleChildScrollView(
          padding: EdgeInsets.only(
            left: 20.w,
            right: 20.w,
            top: 20.h,
            bottom: 20.h + MediaQuery.of(context).viewInsets.bottom,
          ),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight - MediaQuery.of(context).viewInsets.bottom),
            child: IntrinsicHeight(
              child: Center(child: content),
            ),
          ),
        );
      },
    );
  }
}

class _ListenAndTypeQuestionWidget extends StatefulWidget {
  final ListenAndTypeQuestion question;
  final void Function(bool correct) onCompleted;
  final ValueChanged<VoidCallback?>? onPrimaryActionChanged;
  final VoidCallback onSpeak;

  const _ListenAndTypeQuestionWidget({
    required this.question,
    required this.onCompleted,
    required this.onSpeak,
    this.onPrimaryActionChanged,
  });

  @override
  State<_ListenAndTypeQuestionWidget> createState() => _ListenAndTypeQuestionWidgetState();
}

class _ListenAndTypeQuestionWidgetState extends State<_ListenAndTypeQuestionWidget> {
  final _textController = TextEditingController();
  bool? _isCorrect;

  @override
  void initState() {
    super.initState();
    widget.onPrimaryActionChanged?.call(_checkAnswer);
  }

  @override
  void didUpdateWidget(covariant _ListenAndTypeQuestionWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.question != widget.question) {
      _textController
        ..text = ''
        ..selection = const TextSelection.collapsed(offset: 0);
      _isCorrect = null;
      widget.onPrimaryActionChanged?.call(_checkAnswer);
    } else if (oldWidget.onPrimaryActionChanged != widget.onPrimaryActionChanged) {
      widget.onPrimaryActionChanged?.call(_checkAnswer);
    }
  }

  @override
  void dispose() {
    widget.onPrimaryActionChanged?.call(null);
    _textController.dispose();
    super.dispose();
  }

  void _checkAnswer() {
    if (_isCorrect != null) return;
    final answer = _textController.text.trim();
    final correctWord = widget.question.learningWord.word;
    setState(() {
      _isCorrect = answer.toLowerCase() == correctWord.toLowerCase();
    });
    widget.onCompleted(_isCorrect == true);
    widget.onPrimaryActionChanged?.call(null);
  }

  @override
  Widget build(BuildContext context) {
    final word = widget.question.learningWord;
    return LayoutBuilder(
      builder: (context, constraints) {
        final content = Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Nghe phát âm và gõ lại từ đã nghe.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w600),
            ),
            SizedBox(height: 16.h),
            Center(
              child: Ink(
                decoration: ShapeDecoration(
                  color: AppColors.primary,
                  shape: const CircleBorder(),
                ),
                child: IconButton(
                  icon: Icon(Icons.volume_up_rounded, size: 20.sp),
                  color: Colors.white,
                  onPressed: widget.onSpeak,
                ),
              ),
            ),
            SizedBox(height: 40.h),
            TextField(
              controller: _textController,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w600),
              onSubmitted: (_) => _checkAnswer(),
              decoration: InputDecoration(
                hintText: 'Gõ lại từ tiếng Anh',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16.r),
                  borderSide: BorderSide(color: AppColors.textHint),
                ),
                filled: true,
                fillColor: AppColors.surface,
                suffixIcon: _isCorrect == null
                    ? null
                    : Icon(
                        _isCorrect! ? Icons.check_circle : Icons.cancel,
                        color: _isCorrect! ? AppColors.success : Colors.red,
                      ),
              ),
            ),
      if (_isCorrect == false) ...[
              SizedBox(height: 12.h),
              Text(
                'Đáp án đúng: ${word.word}',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.error, fontWeight: FontWeight.w600),
              ),
            ],
            SizedBox(height: 24.h),
            Text(
              'Nhấn "Kiểm tra" để chấm điểm rồi bấm "Tiếp tục" để sang câu mới.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary),
            ),
          ],
        );

        return SingleChildScrollView(
          padding: EdgeInsets.only(
            left: 20.w,
            right: 20.w,
            top: 20.h,
            bottom: 20.h + MediaQuery.of(context).viewInsets.bottom,
          ),
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: constraints.maxHeight - MediaQuery.of(context).viewInsets.bottom),
            child: IntrinsicHeight(
              child: Center(child: content),
            ),
          ),
        );
      },
    );
  }
}

                 

class _FlashcardContent extends StatelessWidget {
  const _FlashcardContent({required this.controller});

  final LearningSessionController controller;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 20.w),
      child: Column(
        children: [
          Expanded(
            child: LayoutBuilder(
              builder: (context, constraints) {
                final maxWidth = constraints.maxWidth;
                final maxHeight = constraints.maxHeight;
                final minSide =
                    math.min(maxWidth.isFinite ? maxWidth : double.infinity,
                        maxHeight.isFinite ? maxHeight : double.infinity);
                final baseSide =
                    minSide.isFinite && minSide > 0 ? minSide : maxWidth;
                final side = baseSide.clamp(220.w, maxWidth);

                return Obx(
                  () {
                    if (controller.isAwaitingRoundThree) {
                      return const _RoundThreePrompt();
                    }

                    if (!controller.hasFlashcards) {
                      return const SizedBox();
                    }

                    final word = controller.currentWord;

                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          SizedBox(
                            width: side,
                            child: AspectRatio(
                              aspectRatio: 1,
                              child: _FlipCard(
                                showBack:
                                    controller.isFlashcardBackVisible,
                                word: word,
                                version: controller.flashcardVersion,
                                onFlip: controller.toggleFlashcardSide,
                                onSpeak: () =>
                                    controller.speakWord(word),
                              ),
                            ),
                          ),
                          SizedBox(height: 10.h),
                          Text(
                            controller.isFlashcardBackVisible
                                ? 'Chạm để xem mặt trước'
                                : 'Chạm để xem nghĩa tiếng Việt',
                            style: TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 14.sp,
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _LearningCard extends StatelessWidget {
  const _LearningCard({required this.word, required this.onSpeak});

  final LearningWord word;
  final VoidCallback onSpeak;

  Color _backgroundByStatus() {
    switch (word.status) {
      case 'learning':
        return AppColors.tint(const Color(0xFFFFF3CD));
      case 'mastered':
        return AppColors.tint(const Color(0xFFE0F7EC));
      default:
        return AppColors.primarySoft;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 18.h),
      child: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          color: _backgroundByStatus(),
          borderRadius: BorderRadius.circular(28.r),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.08),
              blurRadius: 18.r,
              offset: Offset(0, 10.h),
            ),
          ],
        ),
        padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 26.h),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (!word.isVietnamese && word.imageUrl != null && word.imageUrl!.isNotEmpty) ...[
              Image.network(word.imageUrl!, height: 110.h, fit: BoxFit.contain, errorBuilder: (_, __, ___) => const SizedBox()),
              SizedBox(height: 10.h),
            ],
            LangText(
              word.word,
              language: word.language,
              style: TextStyle(
                fontSize: 30.sp,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
            if (word.target != null && word.target!.isTraditional && word.target!.zhuyin.isNotEmpty)
              LangText(word.target!.zhuyin, language: 'zh-Hant', style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
            if (word.target != null && word.target!.measureWord.isNotEmpty)
              LangText('Lượng từ: ${word.target!.measureWord}', language: word.language,
                  style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
            SizedBox(height: 12.h),
            Text(
              word.phonetic ?? '',
              style: TextStyle(
                fontSize: 16.sp,
                color: AppColors.primary,
              ),
            ),
            SizedBox(height: 18.h),
            IconButton(
              onPressed: onSpeak,
              icon: const Icon(Icons.volume_up_rounded),
              color: AppColors.primary,
            ),
            SizedBox(height: 18.h),
            Text(
              word.translation,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 18.sp,
                fontWeight: FontWeight.w600,
                color: const Color(0xFF045D56),
              ),
            ),
            SizedBox(height: 18.h),
            if ((word.exampleVi ?? '').isNotEmpty) ...[
              Text(
                'VD: ${word.exampleVi}',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 15.sp,
                  color: AppColors.textPrimary,
                ),
              ),
              SizedBox(height: 14.h),
            ],
            if ((word.exampleEn ?? '').isNotEmpty)
              LangText(
                word.exampleEn!,
                language: word.language,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 14.sp,
                  fontStyle: FontStyle.italic,
                  color: AppColors.textSecondary,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _NavigationButton extends StatelessWidget {
  const _NavigationButton({
    required this.icon,
    required this.onTap,
  });

  final IconData icon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(
          backgroundColor: onTap == null
              ? AppColors.primaryTint
              : AppColors.primary,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: EdgeInsets.symmetric(vertical: 12.h),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14.r),
          ),
        ),
        child: Icon(icon, size: 20.sp),
      ),
    );
  }
}

class _FlashcardFront extends StatelessWidget {
  const _FlashcardFront({
    super.key,
    required this.word,
    required this.onSpeak,
  });

  final LearningWord word;
  final VoidCallback onSpeak;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: key,
      width: double.infinity,
      height: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(32.r),
        border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
      padding: EdgeInsets.symmetric(horizontal: 28.w, vertical: 32.h),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            word.word,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 30.sp,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          SizedBox(height: 10.h),
          Text(
            word.phonetic ?? '',
            style: TextStyle(
              fontSize: 16.sp,
              color: AppColors.primary,
            ),
          ),
          SizedBox(height: 24.h),
          Material(
            color: AppColors.primary,
            shape: const CircleBorder(),
            child: InkWell(
              onTap: onSpeak,
              customBorder: const CircleBorder(),
              child: SizedBox(
                width: 54.w,
                height: 54.w,
                child: Icon(
                  Icons.volume_up_rounded,
                  color: Colors.white,
                  size: 28.sp,
                ),
              ),
            ),
          ),
          if ((word.exampleEn ?? '').isNotEmpty) ...[
            SizedBox(height: 28.h),
            Text(
              word.exampleEn!,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 15.sp,
                fontStyle: FontStyle.italic,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _FlashcardBack extends StatelessWidget {
  const _FlashcardBack({
    super.key,
    required this.word,
  });

  final LearningWord word;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: key,
      width: double.infinity,
      height: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.primarySoft,
        borderRadius: BorderRadius.circular(32.r),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.08),
            blurRadius: 22.r,
            offset: Offset(0, 12.h),
          ),
        ],
      ),
      padding: EdgeInsets.symmetric(horizontal: 28.w, vertical: 32.h),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (word.isVietnamese)
            WordPicture(imageUrl: word.imageUrl, emoji: word.emoji, size: 200.w)
          else
          Text(
            word.translation,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 26.sp,
              fontWeight: FontWeight.w700,
              color: const Color(0xFF045D56),
            ),
          ),
          if ((word.exampleVi ?? '').isNotEmpty) ...[
            SizedBox(height: 24.h),
            Text(
              word.exampleVi!,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16.sp,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// --- Completion Fullscreen ---
class _LessonCompletedScreen extends StatefulWidget {
  const _LessonCompletedScreen({required this.summary});
  final RoundThreeSummary summary;

  @override
  State<_LessonCompletedScreen> createState() => _LessonCompletedScreenState();
}

class _LessonCompletedScreenState extends State<_LessonCompletedScreen> {
  late final AudioPlayer _player;

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _playCompletionSound();
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  Future<void> _playCompletionSound() async {
    try {
      await _player.stop();
      await _player.play( AssetSource('sounds/complete.wav'), volume: 1.0);
    } catch (e) {
      Get.log('Play completion screen sound error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final percent = widget.summary.firstTryAccuracyPercent;
    final difficult = widget.summary.difficultResults;
    return Scaffold(
      backgroundColor: AppColors.primarySoft,
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.all(20.w),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              
              const Spacer(),
              Text(
                'Xong bài học!',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 26.sp,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary,
                ),
              ),
              SizedBox(height: 16.h),
              // the lesson's one celebration: Prismo hops inside a burst of the three beams
              Center(
                child: PrismBurst(
                  child: Prismo(
                    mood: percent >= 60 ? PrismoMood.celebrate : PrismoMood.happy,
                    size: 170.w,
                  ),
                ),
              ),
              SizedBox(height: 12.h),
              Padding(
                padding: EdgeInsets.only(bottom: 8.h),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Row(
                      children: [
                        Text(
                          widget.summary.xpEarned > 0 ? '+${widget.summary.xpEarned}' : '0',
                          style: AppTextStyles.h4.copyWith(
                            color: widget.summary.xpEarned > 0 ? AppColors.textPrimary : AppColors.textHint,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        SizedBox(width: 4.w),
                        Image.asset(
                          'assets/brand/icons/xp.png',
                          width: 28.w,
                          height: 28.h,
                          errorBuilder: (_, __, ___) => Icon(
                            Icons.star,
                            size: 28.sp,
                            color: AppColors.xpGold,
                          ),
                        ),
                      ],
                    ),
                    SizedBox(width: 16.w),
                    Row(
                      children: [
                        Text(
                          widget.summary.scalesEarned > 0 ? '+${widget.summary.scalesEarned}' : '0',
                          style: AppTextStyles.h4.copyWith(
                            color: widget.summary.scalesEarned > 0 ? AppColors.primary : AppColors.textHint,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        SizedBox(width: 4.w),
                        Image.asset(
                          'assets/brand/icons/scale.png',
                          width: 26.w,
                          height: 26.h,
                          errorBuilder: (_, __, ___) => Icon(
                            Icons.circle,
                            size: 24.sp,
                            color: AppColors.primary,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              SizedBox(height: 12.h),
              Text(
                'Bạn đã trả lời đúng $percent%',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
              ),
              SizedBox(height: 16.h),
              if (difficult.isNotEmpty) ...[
                Text(
                  'Từ cần ôn thêm:',
                  style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                  textAlign: TextAlign.center,
                ),
                SizedBox(height: 8.h),
                Container(
                  constraints: BoxConstraints(maxHeight: 180.h),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(16.r),
                    border: Border.fromBorderSide(BorderSide(color: AppColors.line)),),
                  child: ListView.builder(
                    padding: EdgeInsets.symmetric(vertical: 12.h, horizontal: 16.w),
                    itemCount: difficult.length,
                    itemBuilder: (context, index) {
                      final result = difficult[index];
                      final word = result.word;
                      return Padding(
                        padding: EdgeInsets.only(bottom: index == difficult.length - 1 ? 0 : 12.h),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.flag, size: 18, color: AppColors.streakFire),
                            SizedBox(width: 8.w),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    word.word,
                                    style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700),
                                  ),
                                  if (word.translation.isNotEmpty)
                                    Text(
                                      word.translation,
                                      style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary),
                                    ),
                                  Text(
                                    'Lần đúng đầu: ${result.firstTryCorrect == true ? 'Đúng' : 'Sai'}, lượt làm: ${result.attempts}',
                                    style: TextStyle(fontSize: 12.sp, color: AppColors.textHint),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ] else ...[
                Text(
                  'Tuyệt vời! Bạn đã trả lời đúng tất cả ngay lần đầu.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16.sp, color: AppColors.textPrimary),
                ),
              ],
              const Spacer(),
              SizedBox(
                height: 56.h,
                child: ElevatedButton(
                  onPressed: () async {
                    if (Get.isRegistered<LearningTabController>()) {
                      try {
                        await Get.find<LearningTabController>().refreshProgress();
                      } catch (_) {}
                    }
                    Get.back<void>();
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14.r)),
                    textStyle: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700),
                  ),
                  child: const Text('Tiếp tục'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FlipCard extends StatelessWidget {
  const _FlipCard({
    required this.showBack,
    required this.word,
    required this.version,
    required this.onFlip,
    required this.onSpeak,
  });

  final bool showBack;
  final LearningWord word;
  final int version;
  final VoidCallback onFlip;
  final VoidCallback onSpeak;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onFlip,
      behavior: HitTestBehavior.opaque,
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 260),
        switchInCurve: Curves.easeOut,
        switchOutCurve: Curves.easeIn,
        layoutBuilder: (currentChild, previousChildren) => Stack(
          alignment: Alignment.center,
          children: [
            ...previousChildren,
            if (currentChild != null) currentChild,
          ],
        ),
        transitionBuilder: (child, animation) {
          final rotate = Tween(begin: 1.0, end: 0.0).animate(animation);
          return AnimatedBuilder(
            animation: rotate,
            child: child,
            builder: (context, widgetChild) {
              final value = rotate.value;
              final tilt = (value - 0.5).abs() * 0.003;
              return Transform(
                transform: Matrix4.identity()
                  ..setEntry(3, 2, 0.001)
                  ..rotateY(value * math.pi)
                  ..setEntry(0, 3, tilt),
                alignment: Alignment.center,
                child: widgetChild,
              );
            },
          );
        },
        child: showBack
            ? _FlashcardBack(
                key: ValueKey('flashcard-back-${word.vocabularyId}-$version'),
                word: word,
              )
            : _FlashcardFront(
                key: ValueKey('flashcard-front-${word.vocabularyId}-$version'),
                word: word,
                onSpeak: onSpeak,
              ),
      ),
    );
  }
}

class _RoundThreePrompt extends StatelessWidget {
  const _RoundThreePrompt();

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          'Kiểm tra lần cuối nhé!',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 28.sp,
            fontWeight: FontWeight.w700,
            color: AppColors.ink,
          ),
        ),
        SizedBox(height: 32.h),
        SizedBox(
          width: 240.w,
          height: 240.w,
          child: Image.asset(
            'assets/brand/mascot/prismo_reminder.png',
            fit: BoxFit.contain,
          ),
        ),
      ],
    );
  }
}
