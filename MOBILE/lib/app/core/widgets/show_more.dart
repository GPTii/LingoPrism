import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../theme/app_colors.dart';

/// A long list never shows everything at once: the first [limit] entries, then "Xem tất cả (N) ⌄".
/// Tapping opens the rest; "Thu gọn ⌃" closes them again. [builder] gets how many entries to build.
class ShowMore extends StatefulWidget {
  const ShowMore({super.key, required this.count, required this.builder, this.limit = 5, this.label = 'Xem tất cả'});

  final int count;
  final int limit;
  final String label;
  final Widget Function(BuildContext context, int shown) builder;

  @override
  State<ShowMore> createState() => _ShowMoreState();
}

class _ShowMoreState extends State<ShowMore> {
  bool _open = false;

  @override
  Widget build(BuildContext context) {
    final hidden = widget.count > widget.limit;
    final shown = _open || !hidden ? widget.count : widget.limit;
    if (!hidden) return widget.builder(context, shown);
    return Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      widget.builder(context, shown),
      MoreToggle(open: _open, count: widget.count, label: widget.label, onTap: () => setState(() => _open = !_open)),
    ]);
  }
}

/// The same for a plain column of rows, with an optional [divider] or [spacing] between them.
class ShowMoreColumn extends StatelessWidget {
  const ShowMoreColumn({super.key, required this.children, this.limit = 5, this.label = 'Xem tất cả', this.spacing = 0, this.divider});

  final List<Widget> children;
  final int limit;
  final String label;
  final double spacing;
  final Widget? divider;

  @override
  Widget build(BuildContext context) => ShowMore(
        count: children.length,
        limit: limit,
        label: label,
        builder: (_, shown) => Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          for (var i = 0; i < shown; i++) ...[
            if (i > 0 && divider != null) divider!,
            if (i > 0 && spacing > 0) SizedBox(height: spacing),
            children[i],
          ],
        ]),
      );
}

/// "Xem tất cả (12) ⌄" / "Thu gọn ⌃".
class MoreToggle extends StatelessWidget {
  const MoreToggle({super.key, required this.open, required this.onTap, this.count, this.label = 'Xem tất cả'});

  final bool open;
  final int? count;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Center(
        child: TextButton.icon(
          onPressed: onTap,
          iconAlignment: IconAlignment.end,
          icon: Icon(open ? Icons.keyboard_arrow_up_rounded : Icons.keyboard_arrow_down_rounded, size: 22.sp),
          label: Text(open ? 'Thu gọn' : count == null ? label : '$label ($count)',
              style: TextStyle(fontSize: 14.sp, fontWeight: FontWeight.w700)),
          style: TextButton.styleFrom(foregroundColor: AppColors.primary),
        ),
      );
}
