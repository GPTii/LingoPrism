import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// Scenery of the game map (same art as the web, FE/src/components/GameScenery.tsx): each level is a little
/// world – meadow, seaside, desert, volcano at night – with a winding trail through its stops, things swaying
/// beside it and clouds drifting above. Hand-drawn SVG in the LingoPrism palette; one animation per level, off
/// when the phone asks for reduced motion.
enum SceneTheme { meadow, sea, desert, night }

SceneTheme themeOfLevel(int level) => SceneTheme.values[(level - 1) % SceneTheme.values.length];

enum _Move { none, sway, bob, float, twinkle }

class _Sprite {
  const _Sprite(this.svg, this.w, this.h, this.move);
  final String svg;
  final double w, h; // relative to the size given
  final _Move move;
}

const _tree = _Sprite(
    '<svg viewBox="0 0 60 72"><rect x="26" y="44" width="8" height="26" rx="3" fill="#8a5a3b"/><circle cx="30" cy="30" r="22" fill="#2fbf71"/><circle cx="18" cy="38" r="13" fill="#27a862"/><circle cx="42" cy="38" r="13" fill="#27a862"/><circle cx="24" cy="22" r="6" fill="#5bd994" opacity=".8"/></svg>',
    1,
    1.2,
    _Move.sway);
const _pine = _Sprite(
    '<svg viewBox="0 0 48 72"><rect x="21" y="56" width="6" height="14" rx="2" fill="#7a4e33"/><path d="M24 2 44 30H32L46 50H30L42 62H6L18 50H2L16 30H4Z" fill="#1d9a5b"/></svg>',
    0.8,
    1.2,
    _Move.sway);
const _flower = _Sprite(
    '<svg viewBox="0 0 30 40"><path d="M15 40V18" stroke="#2fbf71" stroke-width="3"/><ellipse cx="15" cy="8" rx="4.5" ry="7" fill="#ff8fab"/><ellipse cx="15" cy="8" rx="4.5" ry="7" fill="#ff8fab" transform="rotate(72 15 14)"/><ellipse cx="15" cy="8" rx="4.5" ry="7" fill="#ff8fab" transform="rotate(144 15 14)"/><ellipse cx="15" cy="8" rx="4.5" ry="7" fill="#ff8fab" transform="rotate(216 15 14)"/><ellipse cx="15" cy="8" rx="4.5" ry="7" fill="#ff8fab" transform="rotate(288 15 14)"/><circle cx="15" cy="14" r="4" fill="#ffd23f"/></svg>',
    0.6,
    0.8,
    _Move.sway);
const _mushroom = _Sprite(
    '<svg viewBox="0 0 40 40"><rect x="15" y="20" width="10" height="16" rx="4" fill="#fff4e0"/><path d="M2 22C2 10 10 3 20 3s18 7 18 19z" fill="#ff5d73"/><circle cx="13" cy="12" r="3" fill="#fff"/><circle cx="26" cy="9" r="2.5" fill="#fff"/><circle cx="29" cy="17" r="2" fill="#fff"/></svg>',
    0.7,
    0.7,
    _Move.none);
const _butterfly = _Sprite(
    '<svg viewBox="0 0 40 34"><path d="M20 17C12 2 2 4 4 14s10 6 16 3z" fill="#a78bfa"/><path d="M20 17c8-15 18-13 16-3s-10 6-16 3z" fill="#a78bfa"/><path d="M20 18c-8 2-12 10-8 13s8-6 8-13zM20 18c8 2 12 10 8 13s-8-6-8-13z" fill="#c4b5fd"/><rect x="19" y="10" width="2" height="16" rx="1" fill="#3b2f63"/></svg>',
    0.7,
    0.6,
    _Move.float);
const _palm = _Sprite(
    '<svg viewBox="0 0 60 78"><path d="M30 76c2-20 0-36-4-50" stroke="#a0703f" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M27 24C17 12 4 14 2 22c10-6 18-4 25 2zM27 24c4-14 18-20 26-14-11 0-20 6-26 14zM27 24c10-6 24-2 30 8-10-6-20-8-30-8zM27 24C18 20 8 28 6 38c6-8 13-12 21-14z" fill="#22b573"/><circle cx="27" cy="26" r="3" fill="#7a4e33"/><circle cx="31" cy="27" r="3" fill="#7a4e33"/></svg>',
    1,
    1.3,
    _Move.sway);
const _boat = _Sprite(
    '<svg viewBox="0 0 60 48"><path d="M30 4v30" stroke="#5b6b7f" stroke-width="2"/><path d="M31 6l18 24H31z" fill="#fff"/><path d="M29 10L14 30h15z" fill="#ffd23f"/><path d="M6 34h48l-8 10H14z" fill="#e0445e"/></svg>',
    1,
    0.8,
    _Move.bob);
const _wave = _Sprite(
    '<svg viewBox="0 0 70 20"><path d="M0 12c6-8 12-8 18 0s12 8 18 0 12-8 18 0 12 8 16 0" stroke="#ffffff" stroke-opacity=".8" stroke-width="3" fill="none" stroke-linecap="round"/></svg>',
    1.4,
    0.4,
    _Move.bob);
const _fish = _Sprite(
    '<svg viewBox="0 0 40 24"><path d="M4 12C10 2 26 2 32 12 26 22 10 22 4 12z" fill="#ff9f43"/><path d="M32 12l8-8v16z" fill="#ff9f43"/><circle cx="11" cy="10" r="2" fill="#243447"/></svg>',
    0.8,
    0.5,
    _Move.float);
const _shell = _Sprite(
    '<svg viewBox="0 0 30 24"><path d="M15 2C6 2 1 12 3 20h24c2-8-3-18-12-18z" fill="#ffc6d3"/><path d="M15 20L8 4M15 20L12 4M15 20L15 4M15 20L18 4M15 20L22 4" stroke="#ff8fab" stroke-width="1.4"/></svg>',
    0.6,
    0.5,
    _Move.none);
const _cactus = _Sprite(
    '<svg viewBox="0 0 48 66"><rect x="18" y="6" width="12" height="58" rx="6" fill="#2fa36b"/><path d="M18 34H10a4 4 0 0 1-4-4V18a4 4 0 0 1 8 0v8h4zM30 26h8V14a4 4 0 0 1 8 0v12a8 8 0 0 1-8 8h-8z" fill="#2fa36b"/><circle cx="24" cy="6" r="4" fill="#ff8fab"/></svg>',
    0.8,
    1.1,
    _Move.sway);
const _pyramid = _Sprite(
    '<svg viewBox="0 0 64 50"><path d="M32 2l30 46H2z" fill="#e7b25c"/><path d="M32 2l30 46H32z" fill="#c98f35"/></svg>',
    1.3,
    1,
    _Move.none);
const _rock = _Sprite(
    '<svg viewBox="0 0 40 24"><path d="M2 22l6-12 10-6 12 4 8 14z" fill="#b9a38a"/><path d="M18 4l12 4 8 14H22z" fill="#a08a72"/></svg>',
    0.8,
    0.5,
    _Move.none);
const _star = _Sprite('<svg viewBox="0 0 20 20"><path d="M10 0l2.6 7.4L20 10l-7.4 2.6L10 20l-2.6-7.4L0 10l7.4-2.6z" fill="#ffe28a"/></svg>',
    0.4, 0.4, _Move.twinkle);
const _crystal = _Sprite(
    '<svg viewBox="0 0 34 48"><path d="M10 46L4 20 12 4l6 16-2 26z" fill="#c084fc"/><path d="M18 46l2-28 8-12 4 18-6 22z" fill="#f472b6"/></svg>',
    0.7,
    1,
    _Move.twinkle);
const _volcano = _Sprite(
    '<svg viewBox="0 0 70 60"><circle cx="38" cy="10" r="6" fill="#9ca3af" opacity=".6"/><circle cx="32" cy="14" r="5" fill="#9ca3af" opacity=".5"/><path d="M2 58L26 20h18l24 38z" fill="#5b3a4a"/><path d="M26 20h18l-4 8-5-3-4 6-5-5z" fill="#ff7a45"/></svg>',
    1.4,
    1.2,
    _Move.none);
const _lantern = _Sprite(
    '<svg viewBox="0 0 24 40"><path d="M12 0v6" stroke="#ffd23f" stroke-width="2"/><rect x="3" y="6" width="18" height="24" rx="9" fill="#ff5d73"/><rect x="8" y="30" width="8" height="4" rx="1" fill="#ffd23f"/><path d="M12 34v6" stroke="#ffd23f" stroke-width="2"/></svg>',
    0.5,
    0.8,
    _Move.bob);

const _decor = <SceneTheme, List<_Sprite>>{
  SceneTheme.meadow: [_tree, _flower, _butterfly, _pine, _mushroom, _flower, _tree],
  SceneTheme.sea: [_palm, _wave, _boat, _fish, _shell, _wave, _palm],
  SceneTheme.desert: [_cactus, _pyramid, _rock, _cactus, _star, _rock],
  SceneTheme.night: [_star, _crystal, _volcano, _lantern, _star, _crystal],
};

/// Small art for the level banner (faded, bottom right).
Widget bannerArt(int level) {
  final s =
      {SceneTheme.meadow: _tree, SceneTheme.sea: _boat, SceneTheme.desert: _pyramid, SceneTheme.night: _volcano}[themeOfLevel(level)]!;
  return IgnorePointer(child: Opacity(opacity: 0.3, child: SvgPicture.string(s.svg, width: 70 * s.w, height: 70 * s.h)));
}

List<Color> _sky(SceneTheme t, bool dark) => switch ((t, dark)) {
      (SceneTheme.meadow, false) => const [Color(0xFFE6FAF1), Color(0xFFC8F0D9), Color(0xFFB4E8C8)],
      (SceneTheme.sea, false) => const [Color(0xFFE6F4FF), Color(0xFFC4E3FB), Color(0xFF9FD2F5)],
      (SceneTheme.desert, false) => const [Color(0xFFFFF6E2), Color(0xFFFBE2B0), Color(0xFFF3CF8A)],
      (SceneTheme.night, false) => const [Color(0xFF2A1838), Color(0xFF43213F), Color(0xFF5C2442)],
      (SceneTheme.meadow, true) => const [Color(0xFF0F2A22), Color(0xFF123A2C), Color(0xFF154533)],
      (SceneTheme.sea, true) => const [Color(0xFF0D2238), Color(0xFF10304F), Color(0xFF123A62)],
      (SceneTheme.desert, true) => const [Color(0xFF2A2110), Color(0xFF3A2C12), Color(0xFF4A3614)],
      (SceneTheme.night, true) => const [Color(0xFF170D20), Color(0xFF24112A), Color(0xFF321430)],
    };

/// Wraps the column of stops of one level. [circleKeys]: the key of each stop's circle, in order (the scene
/// measures them after layout); [progress]: index of the last stop reached (the trail is golden up to it).
class LevelScene extends StatefulWidget {
  const LevelScene({super.key, required this.level, required this.circleKeys, required this.progress, required this.child});
  final int level;
  final List<GlobalKey> circleKeys;
  final int progress;
  final Widget child;

  @override
  State<LevelScene> createState() => _LevelSceneState();
}

class _LevelSceneState extends State<LevelScene> with SingleTickerProviderStateMixin {
  final _box = GlobalKey();
  late final AnimationController _anim = AnimationController(vsync: this, duration: const Duration(seconds: 12));
  List<Offset> _pts = const [];
  Size _size = Size.zero;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _measure());
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.of(context).disableAnimations) {
      _anim.stop();
    } else if (!_anim.isAnimating) {
      _anim.repeat();
    }
  }

  @override
  void didUpdateWidget(covariant LevelScene old) {
    super.didUpdateWidget(old);
    WidgetsBinding.instance.addPostFrameCallback((_) => _measure());
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  void _measure() {
    final box = _box.currentContext?.findRenderObject() as RenderBox?;
    if (!mounted || box == null || !box.hasSize) return;
    final pts = <Offset>[];
    for (final k in widget.circleKeys) {
      final r = k.currentContext?.findRenderObject() as RenderBox?;
      if (r == null || !r.hasSize) continue;
      pts.add(box.globalToLocal(r.localToGlobal(r.size.center(Offset.zero))));
    }
    if (box.size != _size || !_samePoints(pts)) {
      setState(() {
        _pts = pts;
        _size = box.size;
      });
    }
  }

  bool _samePoints(List<Offset> p) => p.length == _pts.length && Iterable.generate(p.length).every((i) => (p[i] - _pts[i]).distance < 1);

  @override
  Widget build(BuildContext context) {
    final theme = themeOfLevel(widget.level);
    final dark = Theme.of(context).brightness == Brightness.dark;
    final sprites = _decor[theme]!;
    final w = _size.width;
    final decor = <(double, double, _Sprite, double, int)>[]; // x, y (feet), sprite, size, phase
    for (var i = 0; i < _pts.length; i++) {
      final p = _pts[i];
      final left = p.dx > w / 2;
      final a = (sprites[i % sprites.length], 46.0 + (i * 7) % 18, (left ? p.dx - 140 : p.dx + 140).clamp(28.0, math.max(28.0, w - 28)).toDouble());
      decor.add((a.$3, p.dy + 10, a.$1, a.$2, i));
      if (i.isOdd) {
        decor.add((
          (left ? p.dx - 90 : p.dx + 90).clamp(20.0, math.max(20.0, w - 20)).toDouble(),
          p.dy + 44,
          sprites[(i + 3) % sprites.length],
          30.0,
          i + 7
        ));
      }
    }
    // never on top of a stop
    decor.removeWhere((d) => _pts.any((p) => (d.$1 - p.dx).abs() < d.$4 * 0.7 + 44 && d.$2 > p.dy - 44 && d.$2 - d.$4 * 1.3 < p.dy + 44));
    // built once per layout, only moved by the animation (no SVG rebuilt each frame)
    final pics = [for (final d in decor) SvgPicture.string(d.$3.svg, width: d.$4 * d.$3.w, height: d.$4 * d.$3.h)];

    return NotificationListener<SizeChangedLayoutNotification>(
      onNotification: (_) {
        WidgetsBinding.instance.addPostFrameCallback((_) => _measure());
        return false;
      },
      child: SizeChangedLayoutNotifier(
        child: DecoratedBox(
          key: _box,
          decoration:
              BoxDecoration(gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: _sky(theme, dark))),
          child: Stack(children: [
            Positioned.fill(
              child: IgnorePointer(
                child: RepaintBoundary(
                  child: AnimatedBuilder(
                    animation: _anim,
                    builder: (context, _) {
                      final t = _anim.value;
                      return Stack(clipBehavior: Clip.hardEdge, children: [
                        Positioned(right: 20, top: 16, child: _SunMoon(night: theme == SceneTheme.night, t: t)),
                        for (final (i, top, scale) in [(0, 24.0, 1.0), (1, 96.0, 0.75)])
                          Positioned(
                            left: ((t + i * 0.45) % 1) * (w + 200) - 120,
                            top: top,
                            child: Transform.scale(scale: scale, child: _Cloud(dark: dark || theme == SceneTheme.night)),
                          ),
                        CustomPaint(size: _size, painter: _TrailPainter(_pts, widget.progress, theme, dark)),
                        for (final (k, (x, y, s, size, phase)) in decor.indexed)
                          Positioned(
                            left: x - size * s.w / 2,
                            top: y - size * s.h,
                            child: _moving(s, pics[k], t, phase),
                          ),
                      ]);
                    },
                  ),
                ),
              ),
            ),
            widget.child,
          ]),
        ),
      ),
    );
  }

  Widget _moving(_Sprite s, Widget pic, double t, int phase) {
    final a = (t * 3 + phase * 0.37) * 2 * math.pi; // three swings per 12 s loop, each sprite out of step
    return switch (s.move) {
      _Move.sway => Transform.rotate(angle: math.sin(a) * 0.05, alignment: Alignment.bottomCenter, child: pic),
      _Move.bob => Transform.translate(offset: Offset(0, math.sin(a) * 4), child: Transform.rotate(angle: math.sin(a) * 0.04, child: pic)),
      _Move.float => Transform.translate(offset: Offset(math.sin(a) * 8, math.cos(a * 0.7) * 8), child: pic),
      _Move.twinkle => Opacity(opacity: 0.45 + 0.55 * (0.5 + 0.5 * math.sin(a * 1.5)), child: pic),
      _Move.none => pic,
    };
  }
}

class _SunMoon extends StatelessWidget {
  const _SunMoon({required this.night, required this.t});
  final bool night;
  final double t;

  @override
  Widget build(BuildContext context) {
    if (night) {
      return Container(
        width: 44,
        height: 44,
        decoration: const BoxDecoration(
            shape: BoxShape.circle, color: Color(0xFFFFF6D6), boxShadow: [BoxShadow(color: Color(0x55FFF6D6), blurRadius: 24)]),
      );
    }
    final s = 1 + 0.06 * math.sin(t * 2 * math.pi * 3);
    return Transform.scale(
      scale: s,
      child: Container(
        width: 50,
        height: 50,
        decoration: const BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(colors: [Color(0xFFFFF3B0), Color(0xFFFFD23F), Color(0xFFFFB800)]),
          boxShadow: [BoxShadow(color: Color(0x88FFD23F), blurRadius: 30)],
        ),
      ),
    );
  }
}

class _Cloud extends StatelessWidget {
  const _Cloud({required this.dark});
  final bool dark;

  @override
  Widget build(BuildContext context) {
    final c = Colors.white.withValues(alpha: dark ? 0.12 : 0.85);
    return SizedBox(
      width: 90,
      height: 46,
      child: Stack(children: [
        Positioned(
            left: 0,
            bottom: 0,
            child: Container(width: 90, height: 28, decoration: BoxDecoration(color: c, borderRadius: BorderRadius.circular(30)))),
        Positioned(
            left: 14, bottom: 10, child: Container(width: 40, height: 40, decoration: BoxDecoration(color: c, shape: BoxShape.circle))),
        Positioned(
            left: 44, bottom: 12, child: Container(width: 30, height: 30, decoration: BoxDecoration(color: c, shape: BoxShape.circle))),
      ]),
    );
  }
}

class _TrailPainter extends CustomPainter {
  _TrailPainter(this.pts, this.progress, this.theme, this.dark);
  final List<Offset> pts;
  final int progress;
  final SceneTheme theme;
  final bool dark;

  Path _curve(List<Offset> p) {
    final path = Path();
    if (p.isEmpty) return path;
    path.moveTo(p.first.dx, p.first.dy);
    for (var i = 1; i < p.length; i++) {
      final a = p[i - 1], b = p[i], my = (a.dy + b.dy) / 2;
      path.cubicTo(a.dx, my, b.dx, my, b.dx, b.dy);
    }
    return path;
  }

  @override
  void paint(Canvas canvas, Size size) {
    if (pts.length < 2) return;
    final path = _curve(pts);
    final night = theme == SceneTheme.night;
    canvas.drawPath(
        path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 14
          ..strokeCap = StrokeCap.round
          ..color = Colors.white.withValues(alpha: dark || night ? 0.12 : 0.75));
    final dash = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round
      ..color = switch (theme) {
        SceneTheme.meadow => const Color(0xFF9FD8B8),
        SceneTheme.sea => const Color(0xFFE9C98A),
        SceneTheme.desert => const Color(0xFFD9A752),
        SceneTheme.night => const Color(0xFFFF9FB8),
      };
    for (final ui.PathMetric m in path.computeMetrics()) {
      for (double d = 0; d < m.length; d += 14) {
        canvas.drawPath(m.extractPath(d, d + 2), dash);
      }
    }
    if (progress > 0) {
      canvas.drawPath(
          _curve(pts.sublist(0, math.min(progress + 1, pts.length))),
          Paint()
            ..style = PaintingStyle.stroke
            ..strokeWidth = 6
            ..strokeCap = StrokeCap.round
            ..color = const Color(0xD9FFC800));
    }
  }

  @override
  bool shouldRepaint(covariant _TrailPainter old) => old.pts != pts || old.progress != progress || old.dark != dark;
}

/// A ring breathing out of the stop to play now.
class PulseRing extends StatefulWidget {
  const PulseRing({super.key, required this.size, required this.color});
  final double size;
  final Color color;

  @override
  State<PulseRing> createState() => _PulseRingState();
}

class _PulseRingState extends State<PulseRing> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1600));

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    MediaQuery.of(context).disableAnimations ? _c.stop() : _c.repeat();
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => IgnorePointer(
        child: AnimatedBuilder(
          animation: _c,
          builder: (context, _) => Opacity(
            opacity: 0.7 * (1 - _c.value),
            child: Transform.scale(
              scale: 1 + 0.45 * _c.value,
              child: Container(
                width: widget.size,
                height: widget.size,
                decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: widget.color, width: 4)),
              ),
            ),
          ),
        ),
      );
}
