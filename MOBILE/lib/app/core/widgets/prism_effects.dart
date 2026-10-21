import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../theme/app_colors.dart';
import 'prismo.dart';

/// One burst of light in the three beam colours – the single celebration moment of a lesson.
/// Plays once; nothing with "reduce motion" on.
class PrismBurst extends StatefulWidget {
  const PrismBurst({super.key, required this.child, this.particles = 46});

  final Widget child;
  final int particles;

  @override
  State<PrismBurst> createState() => _PrismBurstState();
}

class _PrismBurstState extends State<PrismBurst> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1500));
  late final List<_Particle> _ps;

  @override
  void initState() {
    super.initState();
    final r = math.Random();
    const colors = [AppColors.beamAmber, AppColors.beamMint, AppColors.beamCoral];
    _ps = List.generate(widget.particles, (i) {
      final a = -math.pi / 2 + (r.nextDouble() - 0.5) * math.pi * 1.5;
      return _Particle(
        angle: a,
        speed: 0.55 + r.nextDouble() * 0.6,
        size: 4 + r.nextDouble() * 5,
        spin: (r.nextDouble() - 0.5) * 8,
        color: colors[i % 3],
        long: i % 2 == 0,
      );
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted && !(MediaQuery.maybeOf(context)?.disableAnimations ?? false)) _c.forward();
    });
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(clipBehavior: Clip.none, alignment: Alignment.center, children: [
      widget.child,
      Positioned.fill(
        child: IgnorePointer(
          child: AnimatedBuilder(
            animation: _c,
            builder: (context, _) => CustomPaint(painter: _BurstPainter(_ps, _c.value)),
          ),
        ),
      ),
    ]);
  }
}

class _Particle {
  _Particle({required this.angle, required this.speed, required this.size, required this.spin, required this.color, required this.long});
  final double angle, speed, size, spin;
  final Color color;
  final bool long;
}

class _BurstPainter extends CustomPainter {
  _BurstPainter(this.ps, this.t);
  final List<_Particle> ps;
  final double t;

  @override
  void paint(Canvas canvas, Size size) {
    if (t == 0 || t == 1) return;
    final c = size.center(Offset.zero);
    final reach = size.shortestSide * 0.9;
    final e = Curves.easeOutCubic.transform(t);
    final fade = t < 0.65 ? 1.0 : 1 - (t - 0.65) / 0.35;
    for (final p in ps) {
      final d = reach * p.speed * e;
      final pos = c + Offset(math.cos(p.angle) * d, math.sin(p.angle) * d + 140 * t * t); // a little gravity
      canvas.save();
      canvas.translate(pos.dx, pos.dy);
      canvas.rotate(p.spin * t);
      final paint = Paint()..color = p.color.withValues(alpha: fade);
      if (p.long) {
        canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromCenter(center: Offset.zero, width: p.size * 2.2, height: p.size * 0.8), const Radius.circular(2)), paint);
      } else {
        canvas.drawCircle(Offset.zero, p.size / 2, paint);
      }
      canvas.restore();
    }
  }

  @override
  bool shouldRepaint(covariant _BurstPainter old) => old.t != t;
}

/// After each answer Prismo rises from the bottom edge for a moment: a hop and "Đúng rồi!",
/// or a slump and "Chưa đúng". Comes with a light haptic tick (heavier for a miss).
class PrismoReaction {
  PrismoReaction._();

  static OverlayEntry? _entry;

  static void show(BuildContext context, {required bool correct}) {
    correct ? HapticFeedback.lightImpact() : HapticFeedback.mediumImpact();
    final overlay = Overlay.maybeOf(context);
    if (overlay == null) return;
    _entry?.remove();
    late final OverlayEntry entry;
    entry = OverlayEntry(builder: (_) => _ReactionToast(correct: correct, onDone: () {
          if (_entry == entry) _entry = null;
          entry.remove();
        }));
    _entry = entry;
    overlay.insert(entry);
  }
}

class _ReactionToast extends StatefulWidget {
  const _ReactionToast({required this.correct, required this.onDone});
  final bool correct;
  final VoidCallback onDone;

  @override
  State<_ReactionToast> createState() => _ReactionToastState();
}

class _ReactionToastState extends State<_ReactionToast> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 260), reverseDuration: const Duration(milliseconds: 200));

  @override
  void initState() {
    super.initState();
    _c.forward();
    Future<void>.delayed(const Duration(milliseconds: 1100), () async {
      if (!mounted) return;
      await _c.reverse();
      widget.onDone();
    });
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ok = widget.correct;
    final bottom = MediaQuery.paddingOf(context).bottom + 96.h;
    return Positioned(
      left: 0,
      right: 0,
      bottom: bottom,
      child: IgnorePointer(
        child: AnimatedBuilder(
          animation: _c,
          builder: (context, child) {
            final v = Curves.easeOutCubic.transform(_c.value);
            return Opacity(opacity: v, child: Transform.translate(offset: Offset(0, (1 - v) * 24), child: child));
          },
          child: Center(
            child: Material(
              color: Colors.transparent,
              child: Container(
                padding: EdgeInsets.fromLTRB(10.w, 6.h, 18.w, 6.h),
                decoration: BoxDecoration(
                  color: ok ? AppColors.successSoft : AppColors.errorSoft,
                  borderRadius: BorderRadius.circular(40.r),
                  border: Border.all(color: ok ? AppColors.beamMint : AppColors.error, width: 1.5),
                ),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Prismo(mood: ok ? PrismoMood.celebrate : PrismoMood.sad, size: 46.w, blink: false),
                  SizedBox(width: 8.w),
                  Text(ok ? 'Đúng rồi!' : 'Chưa đúng',
                      style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: ok ? AppColors.success : AppColors.error)),
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
