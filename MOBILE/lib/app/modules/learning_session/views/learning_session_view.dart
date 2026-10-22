import 'dart:math' as math;

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/widgets/target_word.dart';
import '../../../core/theme/app_colors.dart';
import '../controllers/learning_session_controller.dart';
import '../../home/controllers/learning_tab_controller.dart';
import '../../../core/widgets/word_picture.dart';
import '../../../core/widgets/prismo.dart';
import '../../../core/widgets/prism_effects.dart';
import '../../../core/widgets/motion.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

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
          onPressed: goBack,
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
                      Builder(builder: (_) {
                        final total = controller.displayTotal;
                        final position = controller.displayPosition;
                        final clamped = total == 0
                            ? 0
                            : (position > total ? total : position);
                        return LessonProgressBar(
                          value: total == 0 ? 0.0 : clamped / total.toDouble(),
                        );
                      }),
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
                  child: DuoButton(
                    label: 'Kiểm tra lại bằng Flashcard',
                    onPressed: controller.isOnLastCard
                        ? controller.startFlashcardRound
                        : null,
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
                        child: DuoButton(
                          label: 'Chưa nhớ',
                          tone: DuoTone.neutral,
                          onPressed: controller.hasFlashcards
                              ? controller.markForgotten
                              : null,
                        ),
                      ),
                      SizedBox(width: 12.w),
                      Expanded(
                        child: DuoButton(
                          label: 'Đã nhớ',
                          onPressed: controller.hasFlashcards
                              ? controller.markRemembered
                              : null,
                        ),
                      ),
                    ],
                  ),
                ),
              if (controller.isFlashcardRound &&
                  controller.isAwaitingRoundThree)
                Padding(
                  padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 28.h),
                  child: DuoButton(
                    label: 'Tiếp tục',
                    onPressed: controller.proceedToRoundThree,
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
  // the answer panel that slides up from the bottom (null = not answered yet)
  bool? _lastCorrect;
  String _lastAnswer = '';
  String _praise = '';
  int _combo = 0;
  static const _praises = ['Chính xác!', 'Tuyệt vời!', 'Giỏi quá!', 'Quá đỉnh!', 'Chuẩn luôn!'];

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
    isCorrect ? HapticFeedback.lightImpact() : HapticFeedback.heavyImpact();
    if (mounted) {
      setState(() {
        _lastCorrect = isCorrect;
        _combo = isCorrect ? _combo + 1 : 0;
        _praise = _praises[math.Random().nextInt(_praises.length)];
        _lastAnswer = switch (question) {
          MultipleChoiceQuestion q => '${q.questionWord} = ${q.correctOption}',
          ScrambleQuestion q => q.correctWord,
          ListenAndTypeQuestion q => q.learningWord.word,
          _ => '',
        };
      });
    }

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
    setState(() => _lastCorrect = null);
    if (_currentIndex < _questions.length - 1) {
      _pageController.nextPage(duration: const Duration(milliseconds: 320), curve: Curves.easeOutCubic);
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
      _pageController.nextPage(duration: const Duration(milliseconds: 320), curve: Curves.easeOutCubic);
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
    goBack<void>();
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
        // the answer panel: after each answer it rises in green or red with the verdict, the right
        // answer and a matching "Tiếp tục" button (Duolingo's check → continue footer)
        Obx(() {
          final canContinue = _canContinue.value;
          final enabled = canContinue || _primaryAction != null;
          final verdict = _lastCorrect;
          return AnimatedContainer(
            duration: const Duration(milliseconds: 220),
            curve: Curves.easeOut,
            width: double.infinity,
            decoration: BoxDecoration(
              color: verdict == null
                  ? Colors.transparent
                  : verdict
                      ? AppColors.successSoft
                      : AppColors.errorSoft,
              borderRadius: BorderRadius.vertical(top: Radius.circular(20.r)),
            ),
            padding: EdgeInsets.fromLTRB(20.w, verdict == null ? 0 : 16.h, 20.w, 20.h + MediaQuery.paddingOf(context).bottom * 0.5),
            child: AnimatedSize(
              duration: const Duration(milliseconds: 220),
              curve: Curves.easeOutCubic,
              alignment: Alignment.bottomCenter,
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                if (verdict != null)
                  _AnswerVerdict(
                    key: ValueKey('verdict-$_currentIndex'),
                    correct: verdict,
                    title: verdict ? _praise : 'Chưa đúng rồi',
                    detail: verdict
                        ? (_combo >= 3 ? '$_combo câu đúng liên tiếp' : '')
                        : (_lastAnswer.isEmpty ? 'Xem lại các cặp từ ở trên nhé' : 'Đáp án: $_lastAnswer'),
                  ),
                DuoButton(
                  label: canContinue ? 'Tiếp tục' : 'Kiểm tra',
                  tone: verdict == null
                      ? DuoTone.primary
                      : verdict
                          ? DuoTone.success
                          : DuoTone.danger,
                  onPressed: enabled
                      ? () {
                          if (canContinue) {
                            _goNext();
                          } else {
                            _primaryAction?.call();
                          }
                        }
                      : null,
                ),
              ]),
            ),
          );
        }),
      ],
    );
  }
}

class _AnswerVerdict extends StatelessWidget {
  const _AnswerVerdict({super.key, required this.correct, required this.title, required this.detail});

  final bool correct;
  final String title;
  final String detail;

  @override
  Widget build(BuildContext context) {
    final color = correct ? AppColors.success : AppColors.error;
    final row = Padding(
      padding: EdgeInsets.only(bottom: 14.h),
      child: Row(children: [
        Prismo(mood: correct ? PrismoMood.celebrate : PrismoMood.sad, size: 52.w, blink: false)
            .animate()
            .scaleXY(begin: 0.4, end: 1, duration: 380.ms, curve: Curves.elasticOut),
        SizedBox(width: 12.w),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800, color: color)),
            if (detail.isNotEmpty)
              Padding(
                padding: EdgeInsets.only(top: 2.h),
                child: Text(detail, style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700, color: color)),
              ),
          ]),
        ),
      ]),
    );
    if (reduceMotion(context)) return row;
    return row.animate().fadeIn(duration: 160.ms).slideY(begin: 0.5, end: 0, duration: 260.ms, curve: Curves.easeOutCubic);
  }
}

// --- Widgets for Round 3 Question Types ---

/// A typed answer that was wrong gives a short shake.
Widget _shakeIfWrong(BuildContext context, bool? isCorrect, Widget field) => reduceMotion(context)
    ? field
    : field.animate(target: isCorrect == false ? 1 : 0).shakeX(duration: 420.ms, hz: 5, amount: 6);

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
          ...widget.question.options.indexed.map((e) {
            final (i, option) = e;
            final answered = _selectedOption != null;
            final right = answered && option == widget.question.correctOption;
            final wrong = answered && !right && option == _selectedOption;
            final textColor = right
                ? AppColors.success
                : wrong
                    ? AppColors.error
                    : AppColors.textPrimary;
            final borderColor = right
                ? AppColors.beamMint
                : wrong
                    ? AppColors.error
                    : AppColors.lineStrong;

            final tile = Press3D(
              onTap: answered ? null : () => _handleAnswer(option),
              color: right
                  ? AppColors.successSoft
                  : wrong
                      ? AppColors.errorSoft
                      : AppColors.surface,
              borderColor: borderColor,
              padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 14.h),
              child: Row(children: [
                // the option's number, like the keyboard hints on Duolingo
                Container(
                  width: 28.w,
                  height: 28.w,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(8.r),
                    border: Border.all(color: borderColor, width: 1.5),
                  ),
                  child: Text('${i + 1}', style: TextStyle(fontSize: 13.sp, fontWeight: FontWeight.w700, color: textColor)),
                ),
                SizedBox(width: 12.w),
                Expanded(
                  child: Text(option, style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700, color: textColor)),
                ),
              ]),
            );

            return Padding(
              padding: EdgeInsets.symmetric(vertical: 6.h),
              child: reduceMotion(context)
                  ? tile
                  : tile
                      .animate(target: wrong ? 1 : 0)
                      .shakeX(duration: 420.ms, hz: 5, amount: 6)
                      .animate(target: right ? 1 : 0)
                      .scaleXY(end: 1.04, duration: 140.ms, curve: Curves.easeOut)
                      .then()
                      .scaleXY(end: 1 / 1.04, duration: 220.ms, curve: Curves.elasticOut),
            )
                // the options deal in one after another
                .animate(delay: (70 * i).ms)
                .fadeIn(duration: 220.ms)
                .slideY(begin: 0.25, end: 0, duration: 300.ms, curve: Curves.easeOutCubic);
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

        final borderColor = matched
            ? AppColors.beamMint
            : isWrong
                ? AppColors.error
                : isSelected
                    ? AppColors.primary
                    : AppColors.lineStrong;
        final tile = Press3D(
          onTap: matched ? null : () => onSelected(word),
          color: bgColor,
          borderColor: borderColor,
          // a matched pair sinks flat and stays there
          depth: matched ? 0 : null,
          child: ConstrainedBox(
            constraints: BoxConstraints(minHeight: 50.h),
            child: Center(
              child: Padding(
                padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 8.h),
                child: Text(
                  word,
                  textAlign: TextAlign.center,
                  style: TextStyle(color: fgColor, fontWeight: FontWeight.w700, fontSize: 15.sp),
                ),
              ),
            ),
          ),
        );
        return Padding(
          padding: EdgeInsets.symmetric(horizontal: 2.w),
          child: reduceMotion(context)
              ? tile
              : tile
                  .animate(target: isWrong ? 1 : 0)
                  .shakeX(duration: 400.ms, hz: 5, amount: 5)
                  .animate(target: matched ? 1 : 0)
                  .scaleXY(end: 0.96, duration: 160.ms, curve: Curves.easeOut)
                  .fade(end: 0.6, duration: 260.ms),
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
            _shakeIfWrong(context, _isCorrect, TextField(
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
            )),
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
            _shakeIfWrong(context, _isCorrect, TextField(
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
            )),
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
    final enabled = onTap != null;
    return Expanded(
      child: Press3D(
        onTap: onTap,
        color: enabled ? AppColors.surface : AppColors.surfaceMuted,
        borderColor: AppColors.lineStrong,
        padding: EdgeInsets.symmetric(vertical: 11.h),
        child: Icon(icon, size: 20.sp, color: enabled ? AppColors.primary : AppColors.textHint),
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
              // the finish, after Duolingo: the title drops in, Prismo hops in a burst of beams,
              // then the three result cards land one by one and count up
              Text(
                percent == 100 ? 'Hoàn hảo!' : 'Xong bài học!',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 28.sp,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary,
                ),
              ).animate().fadeIn(duration: 260.ms).slideY(begin: -0.4, end: 0, duration: 420.ms, curve: Curves.easeOutBack),
              SizedBox(height: 16.h),
              Center(
                child: PrismBurst(
                  child: Prismo(
                    mood: percent >= 60 ? PrismoMood.celebrate : PrismoMood.happy,
                    size: 170.w,
                  ),
                ),
              ).animate(delay: 120.ms).scaleXY(begin: 0.5, end: 1, duration: 650.ms, curve: Curves.elasticOut),
              SizedBox(height: 20.h),
              Row(children: [
                _ResultCard(
                  label: 'KINH NGHIỆM',
                  color: AppColors.beamAmber,
                  value: widget.summary.xpEarned,
                  prefix: '+',
                  icon: Icons.bolt_rounded,
                  delay: 450.ms,
                ),
                SizedBox(width: 10.w),
                _ResultCard(
                  label: 'CHÍNH XÁC',
                  color: AppColors.beamMint,
                  value: percent,
                  suffix: '%',
                  icon: Icons.track_changes_rounded,
                  delay: 600.ms,
                ),
                SizedBox(width: 10.w),
                _ResultCard(
                  label: 'VẢY',
                  color: AppColors.primary,
                  value: widget.summary.scalesEarned,
                  prefix: '+',
                  icon: Icons.diamond_rounded,
                  delay: 750.ms,
                ),
              ]),
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
              DuoButton(
                label: 'Tiếp tục',
                onPressed: () async {
                  if (Get.isRegistered<LearningTabController>()) {
                    try {
                      await Get.find<LearningTabController>().refreshProgress();
                    } catch (_) {}
                  }
                  goBack<void>();
                },
              ).animate(delay: 950.ms).fadeIn(duration: 250.ms).slideY(begin: 0.4, end: 0, curve: Curves.easeOutCubic),
            ],
          ),
        ),
      ),
    );
  }
}

/// One result on the finish screen: a coloured header band and a number that counts up.
class _ResultCard extends StatelessWidget {
  const _ResultCard({
    required this.label,
    required this.color,
    required this.value,
    required this.icon,
    required this.delay,
    this.prefix = '',
    this.suffix = '',
  });

  final String label;
  final Color color;
  final int value;
  final IconData icon;
  final Duration delay;
  final String prefix;
  final String suffix;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(16.r)),
        padding: EdgeInsets.all(2.w),
        child: Column(children: [
          Padding(
            padding: EdgeInsets.symmetric(vertical: 5.h),
            child: Text(label,
                style: TextStyle(fontSize: 11.sp, fontWeight: FontWeight.w800, color: Colors.white, letterSpacing: 0.6)),
          ),
          Container(
            width: double.infinity,
            padding: EdgeInsets.symmetric(vertical: 12.h),
            decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(14.r)),
            child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              Icon(icon, color: color, size: 20.sp),
              SizedBox(width: 4.w),
              CountUp(
                value: value,
                prefix: prefix,
                suffix: suffix,
                delay: delay,
                style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary),
              ),
            ]),
          ),
        ]),
      ).animate(delay: delay).fadeIn(duration: 200.ms).scaleXY(begin: 0.6, end: 1, duration: 500.ms, curve: Curves.elasticOut),
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
            color: AppColors.textPrimary,
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
