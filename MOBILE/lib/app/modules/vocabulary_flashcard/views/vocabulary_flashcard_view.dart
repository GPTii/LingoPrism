import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../core/theme/app_colors.dart';
import '../../vocabulary_topic/controllers/vocabulary_topic_controller.dart';
import '../controllers/vocabulary_flashcard_controller.dart';

class VocabularyFlashcardView extends GetView<VocabularyFlashcardController> {
  const VocabularyFlashcardView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFE5FFFD),
      appBar: AppBar(
        backgroundColor: const Color(0xFFBBFFEE),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.black),
          onPressed: Get.back,
        ),
        title: Obx(
          () => Text(
            '${controller.currentIndex + 1}/${controller.total}',
            style: const TextStyle(
              color: Colors.black,
              fontSize: 20,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: controller.total == 0
            ? _EmptyState(onBack: Get.back)
            : Column(
                children: [
                  Expanded(
                    child: Column(
                      children: [
                        Expanded(
                          child: PageView.builder(
                            controller: controller.pageController,
                            onPageChanged: controller.onPageChanged,
                            physics:
                                const NeverScrollableScrollPhysics(),
                            itemCount: controller.total,
                            itemBuilder: (context, index) =>
                                _Flashcard(
                              item: controller.items[index],
                              index: index,
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        const _NavigationControls(),
                        const SizedBox(height: 8),
                      ],
                    ),
                  ),
                  _CompletionSection(
                    onComplete: controller.completeSession,
                  ),
                ],
              ),
      ),
    );
  }
}

class _Flashcard extends StatelessWidget {
  const _Flashcard({
    required this.item,
    required this.index,
  });

  final VocabularyTopicItem item;
  final int index;

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<VocabularyFlashcardController>();
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final side = constraints.biggest.shortestSide;
          final squareSize = side.isFinite && side > 0 ? side : constraints.maxWidth;
          return Align(
            alignment: Alignment.center,
            child: SizedBox(
              width: squareSize,
              height: squareSize,
              child: _SwipeableFlashcard(
                index: index,
                child: GestureDetector(
                  onTap: () => controller.toggleSideFor(index),
                  behavior: HitTestBehavior.opaque,
                  child: Obx(
                    () {
                      final isCurrent = controller.currentIndex == index;
                      final showBack = isCurrent && controller.isBackVisible;
                      return AnimatedSwitcher(
                        duration: const Duration(milliseconds: 250),
                        switchInCurve: Curves.easeOut,
                        switchOutCurve: Curves.easeIn,
                        transitionBuilder: (child, animation) {
                          final rotate =
                              Tween(begin: 1.0, end: 0.0).animate(animation);
                          return AnimatedBuilder(
                            animation: rotate,
                            child: child,
                            builder: (context, widgetChild) {
                              final value = rotate.value;
                              final tilt = (value - 0.5).abs() * 0.002;
                              return Transform(
                                transform: Matrix4.identity()
                                  ..setEntry(3, 2, 0.001)
                                  ..rotateY(value * 3.1416)
                                  ..setEntry(0, 3, tilt),
                                alignment: Alignment.center,
                                child: widgetChild,
                              );
                            },
                          );
                        },
                        layoutBuilder: (currentChild, previousChildren) => Stack(
                          alignment: Alignment.center,
                          children: [
                            ...previousChildren,
                            if (currentChild != null) currentChild,
                          ],
                        ),
                        child: showBack
                            ? _FlashcardBack(
                                item: item, key: ValueKey('back-$index'))
                            : _FlashcardFront(
                                item: item,
                                index: index,
                                key: ValueKey('front-$index'),
                              ),
                      );
                    },
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _NavigationControls extends StatelessWidget {
  const _NavigationControls();

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<VocabularyFlashcardController>();
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Obx(
        () {
          final canGoBack = controller.canGoBack;
          final canGoNext = controller.canGoNext;
          return Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _PillButton(
                label: 'Quay lại',
                onPressed: canGoBack ? controller.previousCard : null,
              ),
              const SizedBox(width: 16),
              _PillButton(
                label: 'Tiếp tục',
                onPressed: canGoNext ? controller.nextCard : null,
              ),
            ],
          );
        },
      ),
    );
  }
}

class _PillButton extends StatelessWidget {
  const _PillButton({
    required this.label,
    required this.onPressed,
  });

  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final isEnabled = onPressed != null;
    final activeColor = AppColors.buttonActive;
    final textColor = isEnabled ? activeColor : AppColors.textHint;
    final borderColor =
        isEnabled ? activeColor : AppColors.textHint.withOpacity(0.4);

    return SizedBox(
      height: 48,
      child: TextButton(
        onPressed: onPressed,
        style: TextButton.styleFrom(
          backgroundColor: Colors.white,
          foregroundColor: textColor,
          disabledForegroundColor: AppColors.textHint,
          padding: const EdgeInsets.symmetric(horizontal: 28),
          shape: const StadiumBorder(),
          side: BorderSide(
            color: borderColor,
            width: 1.4,
          ),
        ),
        child: Text(
          label,
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

class _CompletionSection extends StatelessWidget {
  const _CompletionSection({required this.onComplete});

  final VoidCallback onComplete;

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).padding.bottom;
    return Container(
      width: double.infinity,
      padding: EdgeInsets.fromLTRB(24, 20, 24, 20 + bottomInset),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: ElevatedButton(
        onPressed: onComplete,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.buttonActive,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(vertical: 18),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(28),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w700,
          ),
        ),
        child: const Text('Hoàn thành'),
      ),
    );
  }
}

class _SwipeableFlashcard extends StatefulWidget {
  const _SwipeableFlashcard({
    required this.child,
    required this.index,
  });

  final Widget child;
  final int index;

  @override
  State<_SwipeableFlashcard> createState() => _SwipeableFlashcardState();
}

class _SwipeableFlashcardState extends State<_SwipeableFlashcard> {
  static const double _swipeThreshold = 60;
  double _dragExtent = 0;

  VocabularyFlashcardController get _controller =>
      Get.find<VocabularyFlashcardController>();

  void _handleDragUpdate(DragUpdateDetails details) {
    _dragExtent += details.primaryDelta ?? 0;
  }

  void _handleDragEnd(DragEndDetails details) {
    if (_dragExtent.abs() < _swipeThreshold) {
      _dragExtent = 0;
      return;
    }

    if (_dragExtent > 0) {
      if (_controller.canGoBack) {
        _controller.previousCard();
      }
    } else {
      _controller.nextCard();
    }

    _dragExtent = 0;
  }

  void _handleDragStart(DragStartDetails details) {
    _dragExtent = 0;
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onHorizontalDragStart: _handleDragStart,
      onHorizontalDragUpdate: _handleDragUpdate,
      onHorizontalDragEnd: _handleDragEnd,
      child: widget.child,
    );
  }
}

class _FlashcardFront extends StatelessWidget {
  const _FlashcardFront({
    required this.item,
    required this.index,
    super.key,
  });

  final VocabularyTopicItem item;
  final int index;

  @override
  Widget build(BuildContext context) {
    final controller = Get.find<VocabularyFlashcardController>();
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFBFE6FF),
        borderRadius: BorderRadius.circular(28),
      ),
      child: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                item.word,
                style: const TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              Text(
                item.ipa,
                style: const TextStyle(
                  fontSize: 18,
                  fontStyle: FontStyle.italic,
                  color: AppColors.textSecondary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 28),
              Material(
                color: AppColors.buttonActive,
                shape: const CircleBorder(),
                child: InkWell(
                  onTap: () => controller.playAudio(item),
                  customBorder: const CircleBorder(),
                  child: const SizedBox(
                    width: 52,
                    height: 52,
                    child: Icon(
                      Icons.volume_up_rounded,
                      color: Colors.white,
                      size: 28,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FlashcardBack extends StatelessWidget {
  const _FlashcardBack({
    required this.item,
    super.key,
  });

  final VocabularyTopicItem item;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFBFE6FF),
        borderRadius: BorderRadius.circular(28),
      ),
      child: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                item.translation,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Text(
                item.exampleVi,
                style: const TextStyle(
                  fontSize: 15,
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              Text(
                item.exampleEn,
                style: const TextStyle(
                  fontSize: 15,
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onBack});

  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        IconButton(
          onPressed: onBack,
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
        ),
        const Expanded(
          child: Center(
            child: Text(
              'Không có thẻ từ vựng để hiển thị.',
              style: TextStyle(fontSize: 16, color: AppColors.textSecondary),
            ),
          ),
        ),
      ],
    );
  }
}
