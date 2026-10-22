import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Prismo's big-eyed face – the app icon and the opening screen's picture
/// (FE/scripts/make-brand-mark.py draws the same thing as an image; keep the two in step).
///
/// Drawn in code so it can move: [eyeOpen] 1 open … 0 shut, [look] moves the pupils
/// (in grid units, about ±6), [beams] stretches the three beams of light (1 = at rest).
class PrismoFacePainter extends CustomPainter {
  PrismoFacePainter({this.eyeOpen = 1, this.look = Offset.zero, this.beams = 1, this.smile = 0});

  final double eyeOpen;
  final Offset look;
  final double beams;

  /// 0 the small smile … 1 a wide open happy mouth
  final double smile;

  static const body = Color(0xFF5CC6FF);
  static const lip = Color(0xFF0F78C8);
  static const ink = Color(0xFF15233B);

  @override
  void paint(Canvas canvas, Size size) {
    canvas.scale(size.width / 160, size.height / 160);
    final round = Paint()
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    // the three beams of light leaving the prism – one per language
    for (final (from, dir, color) in [
      (const Offset(131, 95), const Offset(21, -11), const Color(0xFFFFB020)),
      (const Offset(134, 104), const Offset(23, 0), const Color(0xFF10C79A)),
      (const Offset(131, 113), const Offset(21, 11), const Color(0xFFFF6B81)),
    ]) {
      canvas.drawLine(from, from + dir * beams, round
        ..color = color
        ..strokeWidth = 7);
    }

    // body: a rounded triangle sitting on its darker lip
    final tri = Path()
      ..moveTo(80, 22)
      ..lineTo(138, 124)
      ..lineTo(22, 124)
      ..close();
    for (final (dy, color) in [(7.0, lip), (0.0, body)]) {
      final p = tri.shift(Offset(0, dy));
      canvas.drawPath(p, Paint()..color = color);
      canvas.drawPath(
          p,
          Paint()
            ..color = color
            ..style = PaintingStyle.stroke
            ..strokeWidth = 22
            ..strokeJoin = StrokeJoin.round);
    }
    canvas.drawLine(const Offset(67, 43), const Offset(58, 59), round
      ..color = Colors.white.withValues(alpha: 0.6)
      ..strokeWidth = 6);

    final cheek = Paint()..color = const Color(0xFFFF8FA3).withValues(alpha: 0.75);
    canvas.drawOval(Rect.fromCenter(center: const Offset(44, 113), width: 14, height: 9), cheek);
    canvas.drawOval(Rect.fromCenter(center: const Offset(116, 113), width: 14, height: 9), cheek);

    for (final x in [60.0, 100.0]) {
      canvas.save();
      canvas.translate(x, 89);
      canvas.scale(1, eyeOpen.clamp(0.06, 1.0));
      canvas.drawOval(Rect.fromCenter(center: Offset.zero, width: 35, height: 42), Paint()..color = Colors.white);
      canvas.drawOval(Rect.fromCenter(center: const Offset(3, 4) + look, width: 17, height: 21), Paint()..color = ink);
      canvas.drawCircle(const Offset(6.5, -1.5) + look, 3.4, Paint()..color = Colors.white);
      canvas.restore();
    }

    if (smile <= 0) {
      canvas.drawPath(Path()..moveTo(73, 113)..quadraticBezierTo(80, 120, 87, 113), round
        ..color = ink
        ..strokeWidth = 4);
    } else {
      final w = 7 + 3 * smile, h = 7 + 9 * smile;
      final mouth = Path()
        ..moveTo(80 - w, 112)
        ..quadraticBezierTo(80, 112 + h * 1.6, 80 + w, 112)
        ..close();
      canvas.drawPath(mouth, Paint()..color = ink);
      canvas.drawPath(mouth, round
        ..color = ink
        ..strokeWidth = 3
        ..strokeJoin = StrokeJoin.round);
    }
  }

  @override
  bool shouldRepaint(covariant PrismoFacePainter old) =>
      old.eyeOpen != eyeOpen || old.look != look || old.beams != beams || old.smile != smile;
}

/// The opening screen's Prismo: it starts exactly as the still picture the phone shows while the app
/// loads, then comes alive – crouches, hops, lands with a squash, shines its beams, blinks and looks
/// around – and keeps breathing and blinking until the app is ready. Still when "reduce motion" is on.
class LivingPrismoFace extends StatefulWidget {
  const LivingPrismoFace({super.key, this.size = 180});

  final double size;

  @override
  State<LivingPrismoFace> createState() => _LivingPrismoFaceState();
}

class _LivingPrismoFaceState extends State<LivingPrismoFace> with TickerProviderStateMixin {
  late final AnimationController _intro = AnimationController(vsync: this, duration: const Duration(milliseconds: 2100));
  late final AnimationController _idle = AnimationController(vsync: this, duration: const Duration(milliseconds: 1700));
  late final AnimationController _blink = AnimationController(vsync: this, duration: const Duration(milliseconds: 140));
  final _rnd = math.Random();
  bool _alive = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || (MediaQuery.maybeOf(context)?.disableAnimations ?? false)) return;
      _intro.forward().whenComplete(() {
        if (!_alive) return;
        _idle.repeat();
        _blinkNowAndThen();
      });
    });
  }

  Future<void> _blinkNowAndThen() async {
    while (_alive) {
      await Future<void>.delayed(Duration(milliseconds: 1400 + _rnd.nextInt(1800)));
      if (!_alive || !mounted) return;
      await _blink.forward(from: 0);
      if (mounted) await _blink.reverse();
    }
  }

  @override
  void dispose() {
    _alive = false;
    _intro.dispose();
    _idle.dispose();
    _blink.dispose();
    super.dispose();
  }

  /// 0 → 1 → 0 over [a, b] of the intro
  static double _bump(double t, double a, double b) => t <= a || t >= b ? 0 : math.sin((t - a) / (b - a) * math.pi);

  @override
  Widget build(BuildContext context) {
    final s = widget.size;
    return AnimatedBuilder(
      animation: Listenable.merge([_intro, _idle, _blink]),
      builder: (context, _) {
        final t = _intro.value;
        // crouch (0–.12) → hop (.12–.42) → land and squash (.42–.56) → settle
        final crouch = _bump(t, 0, 0.16);
        final air = _bump(t, 0.12, 0.44);
        final land = _bump(t, 0.42, 0.58);
        final wobble = t > 0.56 && t < 0.72 ? math.sin((t - 0.56) / 0.16 * math.pi * 2) * (0.72 - t) / 0.16 : 0.0;
        final breathe = _intro.isCompleted ? math.sin(_idle.value * math.pi * 2) : 0.0;

        final squash = 1 - 0.12 * crouch - 0.14 * land + 0.10 * air + 0.03 * wobble + 0.018 * breathe;
        final dy = -s * 0.22 * Curves.easeOut.transform(air);

        // after landing: the beams shine, a happy grin, one blink, a look left and right
        final beams = 1 + 0.55 * _bump(t, 0.46, 0.74);
        final grin = _bump(t, 0.44, 0.8);
        final introBlink = _bump(t, 0.8, 0.86);
        final lookX = -6 * _bump(t, 0.84, 0.93) + 6 * _bump(t, 0.92, 1.0);
        final lookY = -3 * air;
        final eyeOpen = 1 - math.max(introBlink, _blink.value).toDouble();

        return SizedBox(
          width: s,
          height: s,
          child: Transform.translate(
            offset: Offset(0, dy),
            child: Transform(
              alignment: Alignment.bottomCenter,
              transform: Matrix4.diagonal3Values(2 - squash, squash, 1),
              child: CustomPaint(
                size: Size.square(s),
                painter: PrismoFacePainter(eyeOpen: eyeOpen, look: Offset(lookX, lookY), beams: beams, smile: grin),
              ),
            ),
          ),
        );
      },
    );
  }
}
