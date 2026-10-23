import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/navigation/back.dart';
import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_widgets.dart';
import '../../core/widgets/prismo.dart';
import '../../core/widgets/prismo_avatar.dart';
import '../../data/models/api/common.dart';
import '../../data/models/api/game.dart';
import '../../data/models/api/user.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/auth_service.dart';
import '../../data/services/game_service.dart';
import '../../routes/app_pages.dart';

/// How my Prismo feels about today: sad right after a lost streak, sleepy while a kept streak waits for today's lesson,
/// happy once I have studied, celebrating when every quest of the day is done. With one line saying why.
(PrismoMood, String) prismoMood(String name) {
  if (!Get.isRegistered<GameService>()) return (PrismoMood.happy, '');
  final g = GameService.to.summary.value;
  final quests = GameService.to.quests;
  if (g.repairableStreak > 0 && !g.studiedToday) {
    return (PrismoMood.sad, '$name buồn vì mất chuỗi ${g.repairableStreak} ngày. Hồi chuỗi trong Cửa hàng để nối lại.');
  }
  if (g.studiedToday && quests.isNotEmpty && quests.every((q) => q.completed)) {
    return (PrismoMood.celebrate, 'Xong hết nhiệm vụ hôm nay, $name vui lắm!');
  }
  if (g.studiedToday) return (PrismoMood.happy, '$name vui vì hôm nay bạn đã học.');
  if (g.streak > 0) return (PrismoMood.sleepy, '$name đang ngủ gật. Học một bài để giữ chuỗi ${g.streak} ngày.');
  return (PrismoMood.wow, 'Học một bài để $name thức dậy nhé!');
}

class WardrobeController extends GetxController {
  final wardrobe = Rxn<Wardrobe>();
  final slot = 'hat'.obs;
  final trying = Rxn<OutfitInfo>();
  final busy = false.obs;

  @override
  void onInit() {
    super.onInit();
    load();
    if (Get.isRegistered<GameService>()) GameService.to.refreshAll();
  }

  Future<void> load() async {
    try {
      wardrobe.value = await GameRepository.wardrobe();
    } catch (e) {
      AppWidgets.showErrorDialog(title: 'Không mở được tủ đồ', message: ApiClient.toApiException(e).message);
    }
  }

  /// what the big Prismo shows: what it wears, with the piece being tried on
  MascotLook get shown {
    final w = wardrobe.value!;
    final t = trying.value;
    return t == null ? w.look : w.look.wearing(t.slot, t.code);
  }

  Future<void> _apply(Future<Wardrobe> Function() call, [String? done]) async {
    busy.value = true;
    try {
      wardrobe.value = await call();
      // everyone sees the new look: my profile carries it
      if (Get.isRegistered<AuthService>()) await AuthService.to.refreshUser();
      if (done != null) Get.snackbar('Tủ đồ Prismo', done, snackPosition: SnackPosition.BOTTOM, duration: const Duration(seconds: 2));
    } catch (e) {
      AppWidgets.showErrorDialog(title: 'Chưa được', message: ApiClient.toApiException(e).message);
    } finally {
      busy.value = false;
    }
  }

  Future<void> toggleWear(OutfitInfo o) {
    final on = wardrobe.value!.look.slot(o.slot) == o.code;
    return _apply(() => GameRepository.dress(wearing: {o.slot: on ? '' : o.code}));
  }

  Future<void> buy(OutfitInfo o) async {
    final w = wardrobe.value!;
    final ok = await AppWidgets.showConfirmDialog(
        title: 'Mua ${o.name}?', message: 'Giá ${o.costGems} ngọc. Bạn đang có ${w.gems} ngọc.', confirmText: 'Mua');
    if (ok == true) await _apply(() => GameRepository.buyOutfit(o.code), 'Prismo đã mặc ${o.name}!');
  }

  Future<void> rename(String name) async {
    final n = name.trim();
    if (n.isEmpty || n == wardrobe.value?.look.name) return;
    await _apply(() => GameRepository.dress(name: n), 'Đã đổi tên thành $n');
  }

  Future<void> setAsAvatar(bool v) => _apply(() => GameRepository.dress(asAvatar: v));
}

class WardrobeView extends StatelessWidget {
  const WardrobeView({super.key});

  @override
  Widget build(BuildContext context) {
    final c = Get.put(WardrobeController());
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        leading: IconButton(icon: Icon(Icons.arrow_back, color: AppColors.textPrimary), onPressed: () => goBack()),
        title: Text('Tủ đồ Prismo', style: TextStyle(color: AppColors.textPrimary, fontSize: 22.sp, fontWeight: FontWeight.w800)),
        actions: [
          Obx(() => Padding(
                padding: EdgeInsets.only(right: 14.w),
                child: Row(children: [
                  Image.asset('assets/brand/icons/gem.png', width: 24.w),
                  SizedBox(width: 4.w),
                  Text('${c.wardrobe.value?.gems ?? 0}',
                      style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: AppColors.primary)),
                ]),
              )),
        ],
      ),
      body: Obx(() {
        final w = c.wardrobe.value;
        if (w == null) return const Center(child: CircularProgressIndicator());
        final (mood, line) = prismoMood(w.look.name);
        final pieces = w.outfits.where((o) => o.slot == c.slot.value).toList();
        return RefreshIndicator(
          onRefresh: c.load,
          child: ListView(padding: EdgeInsets.fromLTRB(16.w, 4.h, 16.w, 32.h), children: [
            Center(child: PrismoAvatar(look: c.shown, size: 230.w, mood: mood, square: true)),
            if (line.isNotEmpty)
              Padding(
                padding: EdgeInsets.only(top: 10.h),
                child: Text(line, textAlign: TextAlign.center, style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
              ),
            SizedBox(height: 12.h),
            c.trying.value == null ? _Settings(c: c, w: w) : _TryPanel(c: c, w: w, o: c.trying.value!),
            SizedBox(height: 14.h),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(children: [
                for (final (code, label) in w.slots)
                  Padding(
                    padding: EdgeInsets.only(right: 8.w),
                    child: ChoiceChip(
                      label: Text(label),
                      selected: c.slot.value == code,
                      onSelected: (_) => c.slot.value = code,
                      labelStyle: TextStyle(fontWeight: FontWeight.w700, fontSize: 14.sp),
                    ),
                  ),
              ]),
            ),
            SizedBox(height: 12.h),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 3, mainAxisSpacing: 10.h, crossAxisSpacing: 10.w, childAspectRatio: 0.7),
              itemCount: pieces.length,
              itemBuilder: (_, i) => _PieceCard(c: c, w: w, o: pieces[i]),
            ),
          ]),
        );
      }),
    );
  }
}

class _Settings extends StatelessWidget {
  const _Settings({required this.c, required this.w});

  final WardrobeController c;
  final Wardrobe w;

  @override
  Widget build(BuildContext context) {
    final owned = w.outfits.where((o) => o.owned).length;
    return Container(
      padding: EdgeInsets.all(14.w),
      decoration: _card(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        TextFormField(
          initialValue: w.look.name,
          maxLength: 20,
          decoration: const InputDecoration(labelText: 'Tên linh vật', counterText: ''),
          textInputAction: TextInputAction.done,
          onFieldSubmitted: c.rename,
        ),
        SwitchListTile(
          contentPadding: EdgeInsets.zero,
          value: w.look.asAvatar,
          onChanged: c.busy.value ? null : c.setAsAvatar,
          title: Text('Dùng làm ảnh đại diện', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15.sp)),
          subtitle: Text('Mọi người thấy ${w.look.name} thay cho ảnh của bạn', style: TextStyle(fontSize: 12.sp)),
        ),
        Text('Đã có $owned/${w.outfits.length} món. Chạm một món bên dưới để thử.',
            style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
      ]),
    );
  }
}

class _TryPanel extends StatelessWidget {
  const _TryPanel({required this.c, required this.w, required this.o});

  final WardrobeController c;
  final Wardrobe w;
  final OutfitInfo o;

  @override
  Widget build(BuildContext context) {
    final on = w.look.slot(o.slot) == o.code;
    final enough = w.gems >= (o.costGems ?? 0);
    final Widget action;
    if (o.owned) {
      action = FilledButton(onPressed: c.busy.value ? null : () => c.toggleWear(o), child: Text(on ? 'Tháo ra' : 'Mặc vào'));
    } else if (o.forSale) {
      action = FilledButton(
        onPressed: c.busy.value || !enough ? null : () => c.buy(o),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Text(enough ? 'Mua · ${o.costGems} ' : 'Chưa đủ ngọc'),
          if (enough) Image.asset('assets/brand/icons/gem.png', height: 18.h),
        ]),
      );
    } else if (o.badge.isNotEmpty) {
      action = OutlinedButton.icon(
          onPressed: () => Get.toNamed(Routes.profile), icon: const Icon(Icons.lock_rounded), label: const Text('Xem huy hiệu'));
    } else {
      action = OutlinedButton.icon(onPressed: null, icon: const Icon(Icons.lock_rounded), label: const Text('Chưa bán lúc này'));
    }
    return Container(
      padding: EdgeInsets.all(14.w),
      decoration: _card(),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Text(o.name, style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary))),
          if (o.owned)
            Text('Đã có', style: TextStyle(fontWeight: FontWeight.w800, color: AppColors.beamMint, fontSize: 13.sp))
          else if (o.costGems != null && o.badge.isEmpty)
            _Price(gems: o.costGems!),
        ]),
        if (o.how.isNotEmpty)
          Padding(
            padding: EdgeInsets.only(top: 4.h),
            child: Text(o.how, style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
          ),
        SizedBox(height: 10.h),
        Row(children: [
          Expanded(child: action),
          SizedBox(width: 8.w),
          TextButton(onPressed: () => c.trying.value = null, child: const Text('Bỏ thử')),
        ]),
      ]),
    );
  }
}

class _PieceCard extends StatelessWidget {
  const _PieceCard({required this.c, required this.w, required this.o});

  final WardrobeController c;
  final Wardrobe w;
  final OutfitInfo o;

  @override
  Widget build(BuildContext context) {
    final on = w.look.slot(o.slot) == o.code;
    final picked = c.trying.value?.code == o.code;
    final locked = !o.owned && !o.forSale;
    // each piece on a plain Prismo (a background on its own)
    final preview = const MascotLook().wearing(o.slot, o.code);
    final Widget status;
    if (on) {
      status = Text('Đang mặc', style: TextStyle(fontSize: 11.sp, fontWeight: FontWeight.w800, color: AppColors.beamMint));
    } else if (o.owned) {
      status = Text('Đã có', style: TextStyle(fontSize: 11.sp, fontWeight: FontWeight.w700, color: AppColors.textSecondary));
    } else if (o.forSale) {
      status = _Price(gems: o.costGems ?? 0, small: true);
    } else {
      status = Text(o.badge.isNotEmpty ? 'Mở bằng huy hiệu' : 'Dịp lễ',
          style: TextStyle(fontSize: 11.sp, color: AppColors.textSecondary), textAlign: TextAlign.center);
    }
    return InkWell(
      onTap: () => c.trying.value = o,
      borderRadius: BorderRadius.circular(16.r),
      child: Container(
        padding: EdgeInsets.all(6.w),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(color: picked ? AppColors.primary : on ? AppColors.beamMint : AppColors.line, width: picked || on ? 2 : 1),
        ),
        child: Column(children: [
          Stack(children: [
            Opacity(opacity: locked ? 0.55 : 1, child: PrismoAvatar(look: preview, size: 88.w, square: true)),
            if (locked)
              Positioned(
                right: 4,
                bottom: 4,
                child: CircleAvatar(radius: 11.r, backgroundColor: Colors.white, child: Icon(Icons.lock_rounded, size: 14.sp)),
              ),
          ]),
          SizedBox(height: 4.h),
          Text(o.name, maxLines: 2, overflow: TextOverflow.ellipsis, textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12.5.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary, height: 1.15)),
          const Spacer(),
          status,
        ]),
      ),
    );
  }
}

class _Price extends StatelessWidget {
  const _Price({required this.gems, this.small = false});

  final int gems;
  final bool small;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        Text('$gems', style: TextStyle(fontSize: small ? 13.sp : 16.sp, fontWeight: FontWeight.w800, color: AppColors.primary)),
        SizedBox(width: 2.w),
        Image.asset('assets/brand/icons/gem.png', height: small ? 16.h : 20.h),
      ]);
}

BoxDecoration _card() => BoxDecoration(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(18.r),
      border: Border.all(color: AppColors.line),
    );

/// A small card that opens the wardrobe: my Prismo as I dressed it.
class MyPrismoCard extends StatelessWidget {
  const MyPrismoCard({super.key});

  @override
  Widget build(BuildContext context) => Obx(() {
        final AppUser? me = Get.isRegistered<AuthService>() ? AuthService.to.user.value : null;
        final look = me?.mascot;
        return InkWell(
          onTap: () => Get.toNamed(Routes.wardrobe),
          borderRadius: BorderRadius.circular(18.r),
          child: Container(
            padding: EdgeInsets.all(12.w),
            decoration: _card(),
            child: Row(children: [
              PrismoAvatar(look: look, size: 64.w, square: true),
              SizedBox(width: 12.w),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('${look?.name ?? 'Prismo'} của bạn',
                      style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
                  Text('Mở tủ đồ: mũ, kính, đồ cầm tay và nền', style: TextStyle(fontSize: 12.5.sp, color: AppColors.textSecondary)),
                ]),
              ),
              Icon(Icons.chevron_right_rounded, color: AppColors.textSecondary),
            ]),
          ),
        );
      });
}
