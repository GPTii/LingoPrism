import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Prismo's moods – the same set as the web mascot (FE/src/components/brand/Brand.tsx).
enum PrismoMood { happy, celebrate, sad, think, wow, sleepy }

/// Prismo drawn in code (not a picture) so it can be alive: it blinks now and then,
/// jumps when the mood turns to [PrismoMood.celebrate] and sinks a little on [PrismoMood.sad].
/// With "reduce motion" on, it stays still.
class Prismo extends StatefulWidget {
  const Prismo({super.key, this.mood = PrismoMood.happy, this.size = 120, this.blink = true});

  final PrismoMood mood;
  final double size;
  final bool blink;

  @override
  State<Prismo> createState() => _PrismoState();
}

class _PrismoState extends State<Prismo> with TickerProviderStateMixin {
  late final AnimationController _blink = AnimationController(vsync: this, duration: const Duration(milliseconds: 160));
  late final AnimationController _react = AnimationController(vsync: this, duration: const Duration(milliseconds: 620));
  final _rnd = math.Random();
  bool _alive = true;

  @override
  void initState() {
    super.initState();
    _scheduleBlink();
    WidgetsBinding.instance.addPostFrameCallback((_) => _playReaction());
  }

  bool get _still => MediaQuery.maybeOf(context)?.disableAnimations ?? false;

  Future<void> _scheduleBlink() async {
    while (_alive && widget.blink) {
      await Future<void>.delayed(Duration(milliseconds: 2800 + _rnd.nextInt(2600)));
      if (!_alive || !mounted || _still) continue;
      if (widget.mood == PrismoMood.celebrate || widget.mood == PrismoMood.sleepy) continue;
      await _blink.forward(from: 0);
      if (mounted) await _blink.reverse();
    }
  }

  void _playReaction() {
    if (!mounted || _still) return;
    if (widget.mood == PrismoMood.celebrate || widget.mood == PrismoMood.sad || widget.mood == PrismoMood.wow) {
      _react.forward(from: 0);
    }
  }

  @override
  void didUpdateWidget(covariant Prismo old) {
    super.didUpdateWidget(old);
    if (old.mood != widget.mood) _playReaction();
  }

  @override
  void dispose() {
    _alive = false;
    _blink.dispose();
    _react.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: 'Prismo',
      image: true,
      child: AnimatedBuilder(
        animation: Listenable.merge([_blink, _react]),
        builder: (context, _) {
          final t = _react.value;
          // celebrate: one hop up and back (ease-out, no overshoot); sad: sink and tilt a little
          double dy = 0, angle = 0, squash = 1;
          if (widget.mood == PrismoMood.celebrate || widget.mood == PrismoMood.wow) {
            final hop = math.sin(t * math.pi);
            dy = -hop * widget.size * (widget.mood == PrismoMood.wow ? 0.06 : 0.12);
            squash = 1 + hop * 0.04;
          } else if (widget.mood == PrismoMood.sad) {
            final sink = Curves.easeOut.transform(t < 0.5 ? t * 2 : 1);
            dy = sink * widget.size * 0.04;
            angle = -sink * 0.06;
          }
          return Transform.translate(
            offset: Offset(0, dy),
            child: Transform.rotate(
              angle: angle,
              child: Transform.scale(
                scaleY: squash,
                scaleX: 2 - squash,
                alignment: Alignment.bottomCenter,
                child: CustomPaint(
                  size: Size(widget.size, widget.size * 150 / 160),
                  painter: _PrismoPainter(widget.mood, 1 - _blink.value),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _PrismoPainter extends CustomPainter {
  _PrismoPainter(this.mood, this.eyeOpen);

  final PrismoMood mood;
  final double eyeOpen; // 1 open … 0 closed (blink)

  static const _ink = Color(0xFF2A1F5C);

  @override
  void paint(Canvas canvas, Size size) {
    // drawn on the web mascot's 160 × 150 grid
    canvas.scale(size.width / 160, size.height / 150);
    final stroke = Paint()
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    // shadow
    canvas.drawOval(Rect.fromCenter(center: const Offset(80, 141), width: 88, height: 12),
        Paint()..color = Colors.black.withValues(alpha: 0.12));

    // light leaving the prism: the three languages
    for (final (a, b, c) in [
      (const Offset(128, 92), const Offset(151, 80), const Color(0xFFFFB020)),
      (const Offset(131, 100), const Offset(155, 99), const Color(0xFF10C79A)),
      (const Offset(128, 108), const Offset(150, 118), const Color(0xFFFF6B81)),
    ]) {
      canvas.drawLine(a, b, stroke
        ..color = c
        ..strokeWidth = 6);
    }

    // feet
    final feet = Paint()..color = const Color(0xFF4A2FD6);
    canvas.drawOval(Rect.fromCenter(center: const Offset(62, 132), width: 22, height: 12), feet);
    canvas.drawOval(Rect.fromCenter(center: const Offset(98, 132), width: 22, height: 12), feet);

    // body: a rounded triangle
    final body = Path()
      ..moveTo(80, 16)
      ..lineTo(140, 122)
      ..lineTo(20, 122)
      ..close();
    final grad = const LinearGradient(
      begin: Alignment(-0.6, -1),
      end: Alignment(0.6, 1),
      colors: [Color(0xFF8F74FF), Color(0xFF6D4AFF), Color(0xFF3FB5E8)],
      stops: [0, 0.6, 1],
    ).createShader(const Rect.fromLTWH(20, 16, 120, 106));
    canvas.drawPath(body, Paint()..shader = grad);
    canvas.drawPath(
        body,
        Paint()
          ..shader = grad
          ..style = PaintingStyle.stroke
          ..strokeWidth = 18
          ..strokeJoin = StrokeJoin.round);
    canvas.drawPath(Path()..moveTo(80, 24)..lineTo(80, 124)..lineTo(26, 124)..close(),
        Paint()..color = Colors.white.withValues(alpha: 0.12));
    canvas.drawLine(const Offset(66, 46), const Offset(56, 64), stroke
      ..color = Colors.white.withValues(alpha: 0.65)
      ..strokeWidth = 5);

    // cheeks
    final cheek = Paint()..color = const Color(0xFFFF8FA3).withValues(alpha: 0.55);
    canvas.drawOval(Rect.fromCenter(center: const Offset(55, 101), width: 14, height: 9), cheek);
    canvas.drawOval(Rect.fromCenter(center: const Offset(105, 101), width: 14, height: 9), cheek);

    _eye(canvas, 64, stroke);
    _eye(canvas, 96, stroke);
    _mouth(canvas, stroke);

    if (mood == PrismoMood.sad) {
      canvas.drawPath(Path()..moveTo(101, 97)..quadraticBezierTo(105, 104, 101, 106)..quadraticBezierTo(97, 104, 101, 97),
          Paint()..color = const Color(0xFF7DD3FC));
    }
    if (mood == PrismoMood.celebrate) {
      _sparkle(canvas, const Offset(29, 50), 10, const Color(0xFFFFB020));
      _sparkle(canvas, const Offset(134, 39), 7, const Color(0xFF10C79A));
    }
    if (mood == PrismoMood.think || mood == PrismoMood.sleepy) {
      final tp = TextPainter(
        text: TextSpan(
            text: mood == PrismoMood.think ? '?' : 'z',
            style: TextStyle(
                fontSize: mood == PrismoMood.think ? 26 : 20,
                fontWeight: FontWeight.w800,
                color: mood == PrismoMood.think ? const Color(0xFFFFB020) : const Color(0xFF8F74FF))),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(canvas, Offset(mood == PrismoMood.think ? 114 : 112, mood == PrismoMood.think ? 38 : 40));
    }
  }

  void _eye(Canvas canvas, double x, Paint stroke) {
    final p = stroke
      ..color = _ink
      ..strokeWidth = 4.5;
    switch (mood) {
      case PrismoMood.celebrate:
        canvas.drawPath(Path()..moveTo(x - 7, 90)..quadraticBezierTo(x, 81, x + 7, 90), p);
        return;
      case PrismoMood.sleepy:
        canvas.drawPath(Path()..moveTo(x - 7, 88)..quadraticBezierTo(x, 94, x + 7, 88), p..strokeWidth = 4);
        return;
      default:
        final big = mood == PrismoMood.wow;
        final dy = mood == PrismoMood.sad ? 3.0 : mood == PrismoMood.think ? -2.0 : 1.0;
        final open = eyeOpen.clamp(0.08, 1.0);
        canvas.save();
        canvas.translate(x, 88);
        canvas.scale(1, open);
        canvas.drawOval(Rect.fromCenter(center: Offset.zero, width: big ? 18 : 15, height: big ? 20 : 17), Paint()..color = Colors.white);
        canvas.drawCircle(Offset(mood == PrismoMood.think ? 2 : 1, dy), big ? 5 : 4.4, Paint()..color = _ink);
        canvas.drawCircle(Offset(2.5, dy - 3), 1.6, Paint()..color = Colors.white);
        canvas.restore();
    }
  }

  void _mouth(Canvas canvas, Paint stroke) {
    final p = stroke
      ..color = _ink
      ..strokeWidth = 4;
    final fill = Paint()..color = _ink;
    switch (mood) {
      case PrismoMood.happy:
        canvas.drawPath(Path()..moveTo(70, 104)..quadraticBezierTo(80, 114, 90, 104), p);
      case PrismoMood.celebrate:
        canvas.drawPath(Path()..moveTo(67, 101)..quadraticBezierTo(80, 122, 93, 101)..close(), fill);
        canvas.drawPath(Path()..moveTo(74, 110)..quadraticBezierTo(80, 116, 86, 110)..quadraticBezierTo(80, 107, 74, 110),
            Paint()..color = const Color(0xFFFF6B81));
      case PrismoMood.sleepy:
        canvas.drawOval(Rect.fromCenter(center: const Offset(80, 106), width: 8, height: 6), fill);
      case PrismoMood.think:
        canvas.drawLine(const Offset(72, 107), const Offset(88, 104), p);
      case PrismoMood.sad:
        canvas.drawPath(Path()..moveTo(70, 110)..quadraticBezierTo(80, 101, 90, 110), p);
      case PrismoMood.wow:
        canvas.drawOval(Rect.fromCenter(center: const Offset(80, 107), width: 11, height: 13), fill);
    }
  }

  void _sparkle(Canvas canvas, Offset c, double r, Color color) {
    final path = Path()
      ..moveTo(c.dx, c.dy - r)
      ..lineTo(c.dx + r * 0.3, c.dy - r * 0.3)
      ..lineTo(c.dx + r, c.dy)
      ..lineTo(c.dx + r * 0.3, c.dy + r * 0.3)
      ..lineTo(c.dx, c.dy + r)
      ..lineTo(c.dx - r * 0.3, c.dy + r * 0.3)
      ..lineTo(c.dx - r, c.dy)
      ..lineTo(c.dx - r * 0.3, c.dy - r * 0.3)
      ..close();
    canvas.drawPath(path, Paint()..color = color);
  }

  @override
  bool shouldRepaint(covariant _PrismoPainter old) => old.mood != mood || old.eyeOpen != eyeOpen;
}
