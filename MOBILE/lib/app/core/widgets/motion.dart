import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../theme/app_colors.dart';

/// The app's tactile motion, after Duolingo: a solid lip under every pressable surface that the face
/// is pushed down onto, springy feedback on answers, a progress bar that fills with a little overshoot.
/// Motion lives where the learner acts (press, answer, progress, finish), never as idle decoration,
/// and everything stands still when the phone asks for reduced motion.

bool reduceMotion(BuildContext context) => MediaQuery.maybeOf(context)?.disableAnimations ?? false;

Color _darker(Color c, [double by = 0.22]) => Color.lerp(c, Colors.black, by)!;

/// A pressable face sitting on a solid lip; on press the face sinks onto the lip.
class Press3D extends StatefulWidget {
  const Press3D({
    super.key,
    required this.child,
    this.onTap,
    required this.color,
    Color? lipColor,
    this.borderColor,
    this.radius,
    this.depth,
    this.padding,
    this.semanticLabel,
  }) : lipColor = lipColor ?? borderColor;

  final Widget child;
  final VoidCallback? onTap;
  final Color color;
  final Color? lipColor;
  final Color? borderColor;
  final double? radius;
  final double? depth;
  final EdgeInsetsGeometry? padding;
  final String? semanticLabel;

  @override
  State<Press3D> createState() => _Press3DState();
}

class _Press3DState extends State<Press3D> {
  bool _down = false;

  void _set(bool v) {
    if (_down != v && mounted) setState(() => _down = v);
  }

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onTap != null;
    final depth = widget.depth ?? 4.h;
    final radius = BorderRadius.circular(widget.radius ?? 16.r);
    final lip = widget.lipColor ?? _darker(widget.color);
    final sunk = _down && enabled;
    return Semantics(
      button: true,
      enabled: enabled,
      label: widget.semanticLabel,
      child: MouseRegion(
        cursor: enabled ? SystemMouseCursors.click : SystemMouseCursors.basic,
        child: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapDown: enabled ? (_) => _set(true) : null,
          onTapUp: enabled ? (_) => _set(false) : null,
          onTapCancel: () => _set(false),
          onTap: enabled
              ? () {
                  HapticFeedback.selectionClick();
                  widget.onTap!();
                }
              : null,
          child: Stack(children: [
            Positioned.fill(
              top: depth,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 160),
                decoration: BoxDecoration(color: lip, borderRadius: radius),
              ),
            ),
            AnimatedPadding(
              duration: const Duration(milliseconds: 70),
              curve: Curves.easeOut,
              padding: EdgeInsets.only(top: sunk ? depth : 0, bottom: sunk ? 0 : depth),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 160),
                padding: widget.padding,
                decoration: BoxDecoration(
                  color: widget.color,
                  borderRadius: radius,
                  border: widget.borderColor == null ? null : Border.all(color: widget.borderColor!, width: 2),
                ),
                child: widget.child,
              ),
            ),
          ]),
        ),
      ),
    );
  }
}

enum DuoTone { primary, success, danger, neutral }

/// The app's main button: full width, bold label, on a lip. Disabled = flat grey.
class DuoButton extends StatelessWidget {
  const DuoButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.tone = DuoTone.primary,
    this.icon,
    this.loading = false,
    this.height,
  });

  final String label;
  final VoidCallback? onPressed;
  final DuoTone tone;
  final IconData? icon;
  final bool loading;
  final double? height;

  @override
  Widget build(BuildContext context) {
    final enabled = onPressed != null && !loading;
    final (Color face, Color text, Color? border) = !enabled
        ? (AppColors.surfaceMuted, AppColors.textHint, null)
        : switch (tone) {
            DuoTone.primary => (AppColors.primary, Colors.white, null),
            DuoTone.success => (AppColors.success, Colors.white, null),
            DuoTone.danger => (AppColors.error, Colors.white, null),
            DuoTone.neutral => (AppColors.surface, AppColors.textPrimary, AppColors.lineStrong),
          };
    return Press3D(
      onTap: enabled ? onPressed : null,
      color: face,
      borderColor: border,
      lipColor: enabled ? (border ?? _darker(face)) : AppColors.lineStrong,
      child: SizedBox(
        height: height ?? 50.h,
        width: double.infinity,
        child: Center(
          child: loading
              ? SizedBox(width: 22.w, height: 22.w, child: CircularProgressIndicator(strokeWidth: 2.4, color: text))
              : Row(mainAxisSize: MainAxisSize.min, children: [
                  if (icon != null) ...[Icon(icon, color: text, size: 20.sp), SizedBox(width: 8.w)],
                  Flexible(
                    child: Text(label.toUpperCase(),
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(color: text, fontSize: 15.sp, fontWeight: FontWeight.w800, letterSpacing: 0.6)),
                  ),
                ]),
        ),
      ),
    );
  }
}

/// Lesson progress: a thick rounded bar that fills with a little overshoot and carries a light
/// stripe along its top, like a filled glass tube.
class LessonProgressBar extends StatelessWidget {
  const LessonProgressBar({super.key, required this.value, this.color});

  final double value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final fill = color ?? AppColors.primary;
    final h = 16.h;
    return Semantics(
      label: 'Tiến độ bài học',
      value: '${(value * 100).round()}%',
      child: Container(
        height: h,
        decoration: BoxDecoration(color: AppColors.lineStrong.withValues(alpha: 0.55), borderRadius: BorderRadius.circular(h)),
        child: TweenAnimationBuilder<double>(
          tween: Tween(end: value.clamp(0.0, 1.0)),
          duration: reduceMotion(context) ? Duration.zero : const Duration(milliseconds: 650),
          curve: Curves.easeOutBack,
          builder: (context, v, _) => FractionallySizedBox(
            alignment: Alignment.centerLeft,
            widthFactor: v.clamp(0.04, 1.0),
            child: Container(
              decoration: BoxDecoration(color: fill, borderRadius: BorderRadius.circular(h)),
              padding: EdgeInsets.fromLTRB(h * 0.45, h * 0.22, h * 0.45, 0),
              alignment: Alignment.topCenter,
              child: Container(
                height: h * 0.22,
                decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.32), borderRadius: BorderRadius.circular(h)),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// A number that counts up from 0 when it first appears.
class CountUp extends StatefulWidget {
  const CountUp({super.key, required this.value, this.prefix = '', this.suffix = '', this.style, this.delay = Duration.zero});

  final int value;
  final String prefix;
  final String suffix;
  final TextStyle? style;
  final Duration delay;

  @override
  State<CountUp> createState() => _CountUpState();
}

class _CountUpState extends State<CountUp> {
  bool _go = false;

  @override
  void initState() {
    super.initState();
    Future<void>.delayed(widget.delay, () {
      if (mounted) setState(() => _go = true);
    });
  }

  @override
  Widget build(BuildContext context) {
    final w = widget;
    if (reduceMotion(context) || w.value == 0) return Text('${w.prefix}${w.value}${w.suffix}', style: w.style);
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: _go ? w.value.toDouble() : 0),
      duration: const Duration(milliseconds: 900),
      curve: Curves.easeOutCubic,
      builder: (context, v, _) => Text('${w.prefix}${v.round()}${w.suffix}', style: w.style),
    );
  }
}
