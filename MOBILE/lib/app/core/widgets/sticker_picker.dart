import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../data/models/api/game.dart';
import '../../data/repositories/repositories.dart';
import '../../routes/app_pages.dart';
import '../navigation/back.dart';
import '../theme/app_colors.dart';

/// A sent sticker (comment, group chat, private message).
class StickerImage extends StatelessWidget {
  const StickerImage({super.key, required this.code, this.size = 110});

  final String code;
  final double size;

  @override
  Widget build(BuildContext context) => Image.asset(
        stickerAsset(code),
        width: size.w,
        height: size.w * 294 / 282,
        fit: BoxFit.contain,
        errorBuilder: (_, __, ___) => SizedBox(width: size.w, height: size.w, child: Icon(Icons.emoji_emotions_outlined, size: 40.sp)),
      );
}

/// The smiley button beside a message box: opens [pickSticker] and hands the chosen code to [onPick].
class StickerButton extends StatelessWidget {
  const StickerButton({super.key, required this.onPick});

  final ValueChanged<String> onPick;

  @override
  Widget build(BuildContext context) => IconButton(
        tooltip: 'Sticker',
        icon: Icon(Icons.emoji_emotions_outlined, color: AppColors.primary, size: 26.sp),
        onPressed: () async {
          final code = await pickSticker();
          if (code != null) onPick(code);
        },
      );
}

/// My stickers in a bottom sheet; the chosen code, or null. With no sticker pack yet, it leads to the shop.
Future<String?> pickSticker() {
  return Get.bottomSheet<String>(
    Container(
      constraints: BoxConstraints(maxHeight: 0.6.sh),
      decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.vertical(top: Radius.circular(24.r))),
      padding: EdgeInsets.fromLTRB(16.w, 10.h, 16.w, 16.h),
      child: SafeArea(
        top: false,
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(width: 40.w, height: 4.h, decoration: BoxDecoration(color: AppColors.line, borderRadius: BorderRadius.circular(2.r))),
          SizedBox(height: 12.h),
          Text('Sticker của tôi', style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
          SizedBox(height: 10.h),
          Flexible(
            child: FutureBuilder<List<StickerInfo>>(
              future: GameRepository.stickers(),
              builder: (context, snap) {
                if (snap.connectionState != ConnectionState.done) {
                  return Padding(padding: EdgeInsets.all(32.w), child: const CircularProgressIndicator());
                }
                final mine = snap.data ?? const <StickerInfo>[];
                if (mine.isEmpty) {
                  return Column(mainAxisSize: MainAxisSize.min, children: [
                    const StickerImage(code: 'hello', size: 96),
                    SizedBox(height: 8.h),
                    Text('Bạn chưa có sticker nào. Mua gói sticker Prismo trong cửa hàng nhé!',
                        textAlign: TextAlign.center, style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
                    SizedBox(height: 12.h),
                    FilledButton(
                      onPressed: () {
                        goBack();
                        Get.toNamed(Routes.shop);
                      },
                      child: const Text('Đến cửa hàng'),
                    ),
                  ]);
                }
                return GridView.count(
                  shrinkWrap: true,
                  crossAxisCount: 4,
                  mainAxisSpacing: 6.h,
                  crossAxisSpacing: 6.w,
                  children: [
                    for (final s in mine)
                      InkWell(
                        borderRadius: BorderRadius.circular(14.r),
                        onTap: () => goBack(result: s.code),
                        child: Tooltip(
                          message: s.caption,
                          child: Padding(padding: EdgeInsets.all(2.w), child: Image.asset(s.asset, fit: BoxFit.contain)),
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
        ]),
      ),
    ),
    isScrollControlled: true,
  );
}
