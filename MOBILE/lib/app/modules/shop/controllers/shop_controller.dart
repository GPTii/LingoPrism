import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_widgets.dart';
import '../../../data/models/api/game.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

/// The shop, as the server sells it (/shop/items/): boosts, Đá băng, Hồi chuỗi, Đổi vảy lấy ngọc and sticker packs.
class ShopController extends GetxController {
  final coins = 0.obs;
  final gems = 0.obs;
  final repairableStreak = 0.obs;
  final isLoading = false.obs;
  final catalogue = <ShopItem>[].obs;
  final busy = ''.obs; // code of the item being bought

  List<ShopItem> get items => catalogue.where((i) => !i.isSticker).toList();
  List<ShopItem> get packs => catalogue.where((i) => i.isSticker).toList();
  List<ShopItem> get myItems => catalogue.where((i) => i.owned > 0 && !i.isSticker && !i.isInstant).toList();

  @override
  void onInit() {
    super.onInit();
    refreshShopData();
  }

  Future<void> refreshShopData() async {
    isLoading.value = true;
    try {
      await GameService.to.refreshSummary();
      final s = GameService.to.summary.value;
      coins.value = s.scales;
      gems.value = s.gems;
      repairableStreak.value = s.repairableStreak;
      catalogue.assignAll(await GameRepository.shop());
    } catch (e) {
      Get.log('Shop load error: $e');
    } finally {
      isLoading.value = false;
    }
  }

  /// Activate an XP boost from the inventory.
  Future<void> useItem(ShopItem item) async {
    try {
      final r = await GameRepository.use(item.id);
      AppWidgets.showSuccessDialog(title: 'Đã kích hoạt', message: '${item.name}: x${r['multiplier']} XP');
      await refreshShopData();
    } catch (e) {
      AppWidgets.showErrorDialog(title: 'Không thể dùng', message: ApiClient.toApiException(e).message);
    }
  }

  Future<void> confirmPurchase(ShopItem item) async {
    if (!AuthService.to.isLoggedIn) {
      AppWidgets.showErrorDialog(title: 'Cần đăng nhập', message: 'Vui lòng đăng nhập để mua vật phẩm.');
      return;
    }
    final repair = item.effect == 'streak_repair';
    if (repair && repairableStreak.value == 0) {
      AppWidgets.showErrorDialog(title: 'Chuỗi vẫn còn', message: 'Hồi chuỗi chỉ dùng được trong 3 ngày sau khi mất chuỗi ngày học.');
      return;
    }
    final verb = repair ? 'Hồi chuỗi' : item.effect == 'gem_exchange' ? 'Đổi' : 'Mua';
    final ok = await Get.dialog<bool>(
      Dialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24.r)),
        child: Padding(
          padding: EdgeInsets.all(20.w),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            if (item.isSticker)
              Wrap(spacing: 4.w, runSpacing: 4.w, alignment: WrapAlignment.center, children: [
                for (final s in item.stickers) Image.asset(s.asset, width: 72.w, height: 75.w),
              ])
            else
              Image.asset(item.image, height: 80.h, errorBuilder: (_, __, ___) => Icon(Icons.inventory, size: 60.sp)),
            SizedBox(height: 14.h),
            Text(item.name, textAlign: TextAlign.center,
                style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
            SizedBox(height: 6.h),
            Text(repair ? 'Nối lại chuỗi ${repairableStreak.value} ngày vừa mất.' : item.description, textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
            SizedBox(height: 16.h),
            PriceTag(item: item, size: 22),
            SizedBox(height: 20.h),
            Row(children: [
              Expanded(child: OutlinedButton(onPressed: () => goBack(result: false), child: const Text('Huỷ'))),
              SizedBox(width: 12.w),
              Expanded(child: FilledButton(onPressed: () => goBack(result: true), child: Text(verb))),
            ]),
          ]),
        ),
      ),
    );
    if (ok == true) await purchase(item);
  }

  Future<void> purchase(ShopItem item) async {
    busy.value = item.code;
    try {
      final r = await GameRepository.buy(item.id);
      coins.value = (r['scales'] as num?)?.toInt() ?? coins.value;
      gems.value = (r['gems'] as num?)?.toInt() ?? gems.value;
      await refreshShopData();
      final done = switch (item.effect) {
        'streak_repair' => 'Đã nối lại chuỗi ngày học!',
        'gem_exchange' => 'Đã đổi được 1 ngọc.',
        'sticker' => 'Đã mở khoá ${item.name}. Gửi sticker trong bình luận, chat nhóm và tin nhắn nhé!',
        _ => 'Đã mua ${item.name}.',
      };
      AppWidgets.showSuccessDialog(title: 'Thành công', message: done);
    } catch (e) {
      final err = ApiClient.toApiException(e);
      AppWidgets.showErrorDialog(title: err.message.startsWith('Không đủ') ? 'Không đủ tiền' : 'Lỗi', message: err.message);
    } finally {
      busy.value = '';
    }
  }
}

/// "150 vảy" / "3 ngọc" with the coin's picture.
class PriceTag extends StatelessWidget {
  const PriceTag({super.key, required this.item, this.size = 16});

  final ShopItem item;
  final double size;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        Image.asset(item.paidWithScales ? 'assets/brand/icons/scale.png' : 'assets/brand/icons/gem.png', height: (size * 1.5).h),
        SizedBox(width: 4.w),
        Text('${item.price}', style: TextStyle(fontSize: size.sp, fontWeight: FontWeight.w800,
            color: item.paidWithScales ? AppColors.textPrimary : AppColors.primary)),
      ]);
}
