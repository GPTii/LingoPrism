import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../../data/models/api/common.dart';
import 'prismo.dart';

/// Someone's Prismo as their picture: the whole wardrobe frame, background included, in a circle (or a rounded square).
class PrismoAvatar extends StatelessWidget {
  const PrismoAvatar({super.key, this.look, this.size = 40, this.mood = PrismoMood.happy, this.square = false});

  final MascotLook? look;
  final double size;
  final PrismoMood mood;
  final bool square;

  @override
  Widget build(BuildContext context) {
    final k = size / 180;
    final frame = SizedBox(
      width: size,
      height: size,
      child: Stack(children: [
        const Positioned.fill(child: ColoredBox(color: Color(0xFFDFF1FF))),
        if ((look?.background ?? '').isNotEmpty) Positioned.fill(child: SvgPicture.asset(outfitAsset(look!.background), fit: BoxFit.fill)),
        // Prismo's 160-wide grid sits at (10, 24) of the 180 frame
        Positioned(left: 10 * k, top: 24 * k, child: Prismo(look: look, mine: false, size: 160 * k, mood: mood, blink: false)),
      ]),
    );
    return square ? ClipRRect(borderRadius: BorderRadius.circular(size * 0.22), child: frame) : ClipOval(child: frame);
  }
}

/// A person's picture: their photo, or their Prismo when they have no photo or chose Prismo instead.
class PersonAvatar extends StatelessWidget {
  const PersonAvatar({super.key, this.avatar, this.look, this.size = 40});

  final String? avatar;
  final MascotLook? look;
  final double size;

  @override
  Widget build(BuildContext context) {
    final path = avatar ?? '';
    if (path.isEmpty || look?.asAvatar == true) return PrismoAvatar(look: look, size: size);
    final image = path.startsWith('http') ? NetworkImage(path) as ImageProvider : AssetImage(path);
    return CircleAvatar(radius: size / 2, backgroundColor: const Color(0xFFDFF1FF), backgroundImage: image);
  }
}
