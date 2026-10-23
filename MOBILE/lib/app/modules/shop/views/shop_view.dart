import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import '../../../data/models/api/game.dart';
import '../controllers/shop_controller.dart';
import 'package:lingoprism/app/core/theme/app_colors.dart';
import 'package:lingoprism/app/core/navigation/back.dart';
import '../../../core/widgets/show_more.dart';

/// Ways to earn gems, as the server gives them (apps/gamification: badges, quests, leagues, the exchange).
const _gemWays = [
  ('1–20', 'Mở huy hiệu', 'Huy hiệu càng khó, càng nhiều ngọc'),
  ('+1', 'Xong hết nhiệm vụ ngày', 'Khi nhận thưởng nhiệm vụ cuối cùng'),
  ('+5', 'Nhiệm vụ tháng', '20 nhiệm vụ ngày trong tháng'),
  ('1–5', 'Thăng hạng giải đấu', 'Hạng 1: 5 · hạng 2: 3 · hạng 3: 2'),
  ('+1', 'Đổi 500 vảy', 'Ngay trong cửa hàng'),
];

class ShopView extends GetView<ShopController> {
  const ShopView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        leading: IconButton(icon: Icon(Icons.arrow_back, color: AppColors.textPrimary), onPressed: () => goBack()),
        title: Text('Cửa hàng', style: TextStyle(color: AppColors.textPrimary, fontSize: 22.sp, fontWeight: FontWeight.w800)),
        actions: [
          Obx(() => _Balance(icon: 'assets/brand/icons/scale.png', value: controller.coins.value)),
          Obx(() => _Balance(icon: 'assets/brand/icons/gem.png', value: controller.gems.value, color: AppColors.primary)),
          SizedBox(width: 8.w),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: controller.refreshShopData,
        child: Obx(() {
          if (controller.isLoading.value && controller.catalogue.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          final mine = controller.myItems;
          return ListView(
            padding: EdgeInsets.fromLTRB(16.w, 8.h, 16.w, 32.h),
            children: [
              if (mine.isNotEmpty) ...[
                _title('Vật phẩm của tôi'),
                SizedBox(
                  height: 132.h,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: mine.length,
                    separatorBuilder: (_, __) => SizedBox(width: 10.w),
                    itemBuilder: (_, i) => _MyItem(item: mine[i], onUse: mine[i].isBoost ? () => controller.useItem(mine[i]) : null),
                  ),
                ),
                SizedBox(height: 20.h),
              ],
              _title('Cách kiếm ngọc'),
              SizedBox(
                height: 104.h,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: _gemWays.length,
                  separatorBuilder: (_, __) => SizedBox(width: 10.w),
                  itemBuilder: (_, i) => _GemWay(way: _gemWays[i]),
                ),
              ),
              SizedBox(height: 20.h),
              _title('Vật phẩm'),
              for (final item in controller.items) ...[
                _ItemRow(item: item, repairable: controller.repairableStreak.value, busy: controller.busy.value == item.code,
                    onTap: () => controller.confirmPurchase(item)),
                SizedBox(height: 10.h),
              ],
              SizedBox(height: 12.h),
              _title('Gói sticker Prismo'),
              Text('Mua một lần, gửi mãi trong bình luận, chat nhóm và tin nhắn.',
                  style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
              SizedBox(height: 10.h),
              ShowMoreColumn(limit: 2, label: 'Xem tất cả gói sticker', spacing: 12.h, children: [
                for (final pack in controller.packs)
                  _PackCard(pack: pack, busy: controller.busy.value == pack.code, onBuy: () => controller.confirmPurchase(pack)),
              ]),
            ],
          );
        }),
      ),
    );
  }

  Widget _title(String text) => Padding(
        padding: EdgeInsets.only(bottom: 10.h),
        child: Text(text, style: TextStyle(fontSize: 19.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
      );
}

class _Balance extends StatelessWidget {
  const _Balance({required this.icon, required this.value, this.color});

  final String icon;
  final int value;
  final Color? color;

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.symmetric(horizontal: 6.w),
        child: Row(children: [
          Image.asset(icon, width: 26.w, height: 26.w),
          SizedBox(width: 3.w),
          Text('$value', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15.sp, color: color ?? AppColors.textPrimary)),
        ]),
      );
}

BoxDecoration _card() => BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(18.r),
      border: Border.all(color: AppColors.line),
    );

class _MyItem extends StatelessWidget {
  const _MyItem({required this.item, this.onUse});

  final ShopItem item;
  final VoidCallback? onUse;

  @override
  Widget build(BuildContext context) => Container(
        width: 112.w,
        padding: EdgeInsets.all(8.w),
        decoration: _card(),
        child: Column(children: [
          Image.asset(item.image, height: 48.h, errorBuilder: (_, __, ___) => Icon(Icons.inventory, size: 40.sp)),
          SizedBox(height: 4.h),
          Text(item.name, maxLines: 1, overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
          Text('x${item.owned}', style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w800, color: AppColors.primary)),
          if (onUse != null)
            SizedBox(
              height: 26.h,
              child: TextButton(onPressed: onUse, style: TextButton.styleFrom(padding: EdgeInsets.zero), child: const Text('Dùng')),
            ),
        ]),
      );
}

class _GemWay extends StatelessWidget {
  const _GemWay({required this.way});

  final (String, String, String) way;

  @override
  Widget build(BuildContext context) => Container(
        width: 150.w,
        padding: EdgeInsets.all(12.w),
        decoration: _card(),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Text(way.$1, style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w900, color: AppColors.primary)),
            SizedBox(width: 3.w),
            Image.asset('assets/brand/icons/gem.png', width: 18.w),
          ]),
          SizedBox(height: 2.h),
          Text(way.$2, maxLines: 1, overflow: TextOverflow.ellipsis,
              style: TextStyle(fontSize: 13.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
          Text(way.$3, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 11.sp, color: AppColors.textSecondary)),
        ]),
      );
}

class _ItemRow extends StatelessWidget {
  const _ItemRow({required this.item, required this.repairable, required this.busy, required this.onTap});

  final ShopItem item;
  final int repairable;
  final bool busy;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final repair = item.effect == 'streak_repair';
    final off = repair && repairable == 0;
    return InkWell(
      onTap: busy ? null : onTap,
      borderRadius: BorderRadius.circular(18.r),
      child: Opacity(
        opacity: off ? 0.55 : 1,
        child: Container(
          padding: EdgeInsets.all(14.w),
          decoration: _card(),
          child: Row(children: [
            Image.asset(item.image, height: 52.h, width: 52.h, errorBuilder: (_, __, ___) => Icon(Icons.inventory, size: 40.sp)),
            SizedBox(width: 14.w),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(item.name, style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
                SizedBox(height: 2.h),
                Text(repair && repairable > 0 ? 'Nối lại chuỗi $repairable ngày vừa mất!' : item.description,
                    style: TextStyle(fontSize: 12.5.sp, color: repair && repairable > 0 ? AppColors.beamAmber : AppColors.textSecondary,
                        fontWeight: repair && repairable > 0 ? FontWeight.w700 : FontWeight.w400)),
              ]),
            ),
            SizedBox(width: 10.w),
            busy ? SizedBox(width: 22.w, height: 22.w, child: const CircularProgressIndicator(strokeWidth: 2)) : PriceTag(item: item),
          ]),
        ),
      ),
    );
  }
}

class _PackCard extends StatelessWidget {
  const _PackCard({required this.pack, required this.busy, required this.onBuy});

  final ShopItem pack;
  final bool busy;
  final VoidCallback onBuy;

  @override
  Widget build(BuildContext context) {
    final owned = pack.owned > 0;
    return Container(
      padding: EdgeInsets.all(14.w),
      decoration: _card(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text(pack.name, style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary))),
          if (owned)
            Row(children: [
              Icon(Icons.check_circle, color: AppColors.beamMint, size: 18.sp),
              SizedBox(width: 4.w),
              Text('Đã có', style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.beamMint, fontSize: 13.sp)),
            ])
          else
            FilledButton(
              onPressed: busy ? null : onBuy,
              style: FilledButton.styleFrom(minimumSize: Size(0, 36.h), padding: EdgeInsets.symmetric(horizontal: 12.w)),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                const Text('Mua · '),
                Image.asset(pack.paidWithScales ? 'assets/brand/icons/scale.png' : 'assets/brand/icons/gem.png', height: 18.h),
                SizedBox(width: 2.w),
                Text('${pack.price}', style: const TextStyle(fontWeight: FontWeight.w800)),
              ]),
            ),
        ]),
        SizedBox(height: 10.h),
        GridView.count(
          crossAxisCount: 3,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 4.h,
          crossAxisSpacing: 4.w,
          childAspectRatio: 282 / 294,
          children: [for (final s in pack.stickers) Image.asset(s.asset, fit: BoxFit.contain)],
        ),
      ]),
    );
  }
}
