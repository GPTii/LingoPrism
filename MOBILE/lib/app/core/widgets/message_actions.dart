import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../network/api_client.dart';
import '../theme/app_colors.dart';

/// One chat bubble with a small "⋯" button (or a long press): put a heart on it, or translate it into
/// Vietnamese – a machine translation shown under the bubble, only to me. Same as the web MessageActions.
/// The hearts are shown under the bubble; tapping them (or double-tapping the bubble) toggles mine.
class MessageActions extends StatefulWidget {
  const MessageActions({super.key, required this.child, required this.text, required this.hearts, required this.me,
      required this.mine, this.onHeart});

  final Widget child;

  /// the text of the message ('' for a sticker: nothing to translate)
  final String text;
  final List<int> hearts;
  final int me;
  final bool mine;
  final Future<void> Function()? onHeart;

  static Future<bool>? _canTranslate;

  @override
  State<MessageActions> createState() => _MessageActionsState();
}

class _MessageActionsState extends State<MessageActions> {
  ({String text, String reading})? _translation;
  bool _shown = false;
  bool _busy = false;

  bool get _hearted => widget.hearts.contains(widget.me);

  @override
  void initState() {
    super.initState();
    MessageActions._canTranslate ??=
        ApiClient.to.get<dynamic>('/ai/status/').then((d) => d is Map && d['translate'] == true).catchError((_) => false);
  }

  Future<void> _translate() async {
    if (_translation != null) {
      setState(() => _shown = !_shown);
      return;
    }
    setState(() => _busy = true);
    try {
      final d = Map<String, dynamic>.from(await ApiClient.to.post<dynamic>('/translate/',
          data: {'text': widget.text, 'source': 'auto', 'target': 'vi'}) as Map);
      if (!mounted) return;
      setState(() {
        _translation = (text: d['translation'] as String? ?? '', reading: d['source_reading'] as String? ?? '');
        _shown = true;
      });
    } catch (e) {
      Get.snackbar('Không dịch được', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _menu() async {
    final canTranslate = widget.text.trim().isNotEmpty && await MessageActions._canTranslate == true;
    if (!mounted || (widget.onHeart == null && !canTranslate)) return;
    final choice = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          if (widget.onHeart != null)
            ListTile(
              leading: Icon(_hearted ? Icons.favorite_rounded : Icons.favorite_border_rounded, color: AppColors.error),
              title: Text(_hearted ? 'Bỏ tim' : 'Thả tim'),
              onTap: () => Navigator.pop(context, 'heart'),
            ),
          if (canTranslate)
            ListTile(
              leading: Icon(Icons.translate_rounded, color: AppColors.primary),
              title: Text(_translation != null && _shown ? 'Ẩn bản dịch' : 'Dịch sang tiếng Việt'),
              onTap: () => Navigator.pop(context, 'translate'),
            ),
        ]),
      ),
    );
    if (choice == 'heart') await widget.onHeart?.call();
    if (choice == 'translate') await _translate();
  }

  @override
  Widget build(BuildContext context) {
    final t = _translation;
    final small = TextStyle(fontSize: 11.sp, color: AppColors.textSecondary);
    return Column(
      crossAxisAlignment: widget.mine ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          textDirection: widget.mine ? TextDirection.rtl : TextDirection.ltr,
          children: [
            Flexible(
              child: GestureDetector(
                onLongPress: _menu,
                onDoubleTap: widget.onHeart,
                child: widget.child,
              ),
            ),
            SizedBox(
              width: 32.w,
              height: 32.w,
              child: _busy
                  ? Padding(padding: EdgeInsets.all(8.w), child: const CircularProgressIndicator(strokeWidth: 2))
                  : IconButton(
                      padding: EdgeInsets.zero,
                      tooltip: 'Tuỳ chọn tin nhắn',
                      onPressed: _menu,
                      icon: Icon(Icons.more_horiz_rounded, size: 18.sp, color: AppColors.textSecondary),
                    ),
            ),
          ],
        ),
        if (t != null && _shown)
          Container(
            margin: EdgeInsets.only(top: 4.h),
            constraints: BoxConstraints(maxWidth: 0.7.sw),
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 6.h),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12.r),
              border: Border.all(color: AppColors.line),
            ),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              if (t.reading.isNotEmpty) Text(t.reading, style: small),
              Text(t.text, style: TextStyle(fontSize: 14.sp, color: AppColors.textPrimary)),
              Text('Bản dịch máy', style: small),
            ]),
          ),
        if (widget.hearts.isNotEmpty)
          Padding(
            padding: EdgeInsets.only(top: 2.h),
            child: InkWell(
              borderRadius: BorderRadius.circular(12.r),
              onTap: widget.onHeart,
              child: Container(
                padding: EdgeInsets.symmetric(horizontal: 6.w, vertical: 2.h),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(12.r),
                  border: Border.all(color: _hearted ? AppColors.error.withValues(alpha: 0.4) : AppColors.line),
                ),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(Icons.favorite_rounded, size: 13.sp, color: AppColors.error),
                  if (widget.hearts.length > 1) ...[
                    SizedBox(width: 3.w),
                    Text('${widget.hearts.length}',
                        style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w700, color: AppColors.textSecondary)),
                  ],
                ]),
              ),
            ),
          ),
      ],
    );
  }
}
