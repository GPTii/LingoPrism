import 'package:flutter/widgets.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// LingoPrism's own UI icons: chunky, filled, each shape on a darker lip like the buttons.
/// The same SVGs as the web (assets/icons/ui, made by FE/scripts/make-ui-icons.py).
class AppIcon extends StatelessWidget {
  const AppIcon(this.name, {super.key, this.size = 24});

  /// home, learn, vocab, camera, community, trophy, chat, bell, sparkle, review, tiles, mic, pencil,
  /// exam, shapes, bookmark, photo, pin, news, group, podium, mail, chart, target, calendar, medal,
  /// bag, cap, profile, check, book, more
  final String name;
  final double size;

  @override
  Widget build(BuildContext context) =>
      SvgPicture.asset('assets/icons/ui/$name.svg', width: size, height: size, excludeFromSemantics: true);
}
