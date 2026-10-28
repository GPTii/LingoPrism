import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/navigation/back.dart';
import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/utils/vietnamese.dart';
import '../../core/widgets/app_icon.dart';
import '../../core/widgets/target_word.dart';
import '../../core/widgets/word_picture.dart';
import '../../data/models/api/common.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/auth_service.dart';
import '../../data/services/game_service.dart';
import '../../data/services/tts_service.dart';
import '../../routes/app_pages.dart';
import '../learning_session/controllers/learning_session_controller.dart';
import '../levels/levels_module.dart' show levelColors;

/// Trò chơi: the game map (4 levels of rounds, chests and a boss round) and its mini games (BE apps/games).
/// Learning comes first: a round opens once its words / reading lesson were learned in the Học section, and a lost
/// round leads straight back to what to learn again.

typedef Json = Map<String, dynamic>;

/// Locale tag of the language being played, for the right glyphs of Chinese characters.
String _langTag() {
  final u = Get.find<AuthService>().currentUser;
  final lang = u?.activeLanguage ?? 'en';
  if (lang != 'zh') return lang;
  return u?.zhScript == 'hant' ? 'zh-Hant' : 'zh-Hans';
}

void _sayAudio(dynamic audio) {
  final a = asMap(audio);
  if (a.isNotEmpty) TtsService.to.speak(asString(a['text']), asString(a['locale']));
}

const _green = Color(0xFF58CC02);
const _greenLip = Color(0xFF43A000);

// ====================================================================== map

class GameMapController extends GetxController {
  final Rxn<Json> data = Rxn<Json>();
  final RxBool isLoading = false.obs;
  final RxString error = ''.obs;

  @override
  void onInit() {
    super.onInit();
    load();
  }

  Future<void> load() async {
    isLoading.value = true;
    error.value = '';
    try {
      data.value = await GamesRepository.map();
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> tap(Json stop) async {
    final status = asString(stop['status']);
    final kind = asString(stop['kind']);
    if (status == 'locked') return _locked(asMap(stop['lock']));
    if (kind != 'chest') {
      await Get.toNamed(Routes.gamePlay, arguments: asString(stop['id']));
      load();
      return;
    }
    if (status == 'done') {
      Get.snackbar('Rương', 'Rương này đã mở rồi', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    try {
      final reward = await GamesRepository.openChest(asString(stop['id']));
      await Get.dialog(_ChestDialog(gems: asInt(reward['gems']), scales: asInt(reward['scales'])));
      load();
      if (Get.isRegistered<GameService>()) GameService.to.refreshSummary();
    } catch (e) {
      Get.snackbar('Không mở được rương', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  void _locked(Json lock) {
    final reason = asString(lock['reason']);
    if (reason == 'learn') {
      _ask('Học trước rồi chơi nhé!',
          'Màn này dùng những từ bạn đã học. Hãy học thêm ${asInt(lock['need'])} từ ở cấp ${asInt(lock['level'])} để mở.',
          'Đi học từ mới', () => Get.toNamed(Routes.learningSession, arguments: const LearningSessionArguments(kind: 'learn')));
    } else if (reason == 'lesson') {
      _ask('Học bài trước rồi chơi nhé!', 'Màn này mở khi con học xong bài “${asString(lock['title'])}”.',
          'Học bài ${asInt(lock['lesson'])}', () => Get.toNamed(Routes.literacyLesson, arguments: asInt(lock['lesson'])));
    } else {
      Get.snackbar('Chưa mở', 'Hãy qua màn trước đã!', snackPosition: SnackPosition.BOTTOM);
    }
  }

  void _ask(String title, String text, String action, VoidCallback go) {
    Get.dialog(AlertDialog(
      title: Text(title),
      content: Text(text),
      actions: [
        TextButton(onPressed: () => goBack(), child: const Text('Để sau')),
        FilledButton(onPressed: () { goBack(); go(); }, child: Text(action)),
      ],
    ));
  }
}

class GameMapView extends GetView<GameMapController> {
  const GameMapView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Trò chơi'), backgroundColor: AppColors.appBarBackground),
      body: Obx(() {
        final d = controller.data.value;
        if (d == null) {
          if (controller.error.isNotEmpty) return Center(child: Padding(padding: EdgeInsets.all(24.w), child: Text(controller.error.value)));
          return const Center(child: CircularProgressIndicator());
        }
        final reading = asString(d['track']) == 'reading';
        final current = asString(d['current']);
        return RefreshIndicator(
          onRefresh: controller.load,
          child: ListView(padding: EdgeInsets.all(16.w), children: [
            Row(children: [
              Image.asset('assets/brand/mascot/prismo_party.png', width: 60.w, height: 60.w),
              SizedBox(width: 12.w),
              Expanded(
                child: Text(
                    reading
                        ? 'Học xong bài ở mục Học đọc – viết rồi vào đây chơi. Qua mỗi màn, mở rương nhận ngọc!'
                        : 'Chơi với những từ bạn đã học. Học thêm ở mục Học để mở màn mới.',
                    style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary, height: 1.35)),
              ),
            ]),
            SizedBox(height: 16.h),
            for (final level in asMapList(d['levels'])) _level(level, current),
          ]),
        );
      }),
    );
  }

  Widget _level(Json level, String current) {
    final n = asInt(level['level']);
    final color = levelColors[n - 1];
    final unlocked = level['unlocked'] == true;
    final nodes = asMapList(level['nodes']);
    return Container(
      margin: EdgeInsets.only(bottom: 18.h),
      decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(20.r),
          border: Border.all(color: AppColors.line)),
      clipBehavior: Clip.antiAlias,
      child: Column(children: [
        Container(
          color: color,
          padding: EdgeInsets.all(16.w),
          child: Row(children: [
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('Cấp $n', style: TextStyle(color: Colors.white70, fontSize: 12.sp)),
                Text(asString(level['name']), style: TextStyle(color: Colors.white, fontSize: 22.sp, fontWeight: FontWeight.w800)),
                Text(asString(level['description']), style: TextStyle(color: Colors.white70, fontSize: 12.sp)),
              ]),
            ),
            Column(children: [
              Text('${asInt(level['done'])}/${asInt(level['total'])}',
                  style: TextStyle(color: Colors.white, fontSize: 18.sp, fontWeight: FontWeight.w700)),
              if (!unlocked) const Icon(Icons.lock_rounded, color: Colors.white70),
            ]),
          ]),
        ),
        if (!unlocked)
          Padding(
            padding: EdgeInsets.all(16.w),
            child: Row(children: [
              Image.asset('assets/brand/mascot/prismo_sleepy.png', width: 48.w, height: 48.w),
              SizedBox(width: 10.w),
              Expanded(child: Text('Thắng màn trùm của cấp trước để mở cấp này.', style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp))),
            ]),
          )
        else
          Padding(
            padding: EdgeInsets.only(top: 44.h, bottom: 24.h),
            child: Column(children: [
              for (var k = 0; k < nodes.length; k++)
                Padding(
                  padding: EdgeInsets.only(bottom: 30.h),
                  child: Transform.translate(
                    offset: Offset(math.sin(k * 0.85) * 70.w, 0),
                    child: _StopButton(stop: nodes[k], color: color, current: asString(nodes[k]['id']) == current, onTap: () => controller.tap(nodes[k])),
                  ),
                ),
            ]),
          ),
      ]),
    );
  }
}

class _StopButton extends StatelessWidget {
  const _StopButton({required this.stop, required this.color, required this.current, required this.onTap});

  final Json stop;
  final Color color;
  final bool current;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final status = asString(stop['status']);
    final kind = asString(stop['kind']);
    final boss = kind == 'boss';
    final size = (boss ? 88 : 68).w;
    final locked = status == 'locked';
    final face = locked ? const Color(0xFFD5DCE6) : status == 'done' ? _green : color;
    final lip = locked ? const Color(0xFFAAB6C4) : status == 'done' ? _greenLip : Color.lerp(color, Colors.black, 0.3)!;
    Widget inner;
    if (kind == 'chest') {
      inner = Opacity(opacity: status == 'done' ? 0.55 : 1, child: AppIcon('chest', size: size * 0.62));
    } else if (boss) {
      inner = Opacity(opacity: locked ? 0.5 : 1, child: AppIcon('trophy', size: size * 0.6));
    } else if (locked) {
      inner = Icon(Icons.lock_rounded, color: Colors.white, size: 26.sp);
    } else {
      inner = Text('${asInt(stop['index'])}', style: TextStyle(color: Colors.white, fontSize: 24.sp, fontWeight: FontWeight.w800));
    }
    return Column(mainAxisSize: MainAxisSize.min, children: [
      if (current)
        Container(
          margin: EdgeInsets.only(bottom: 8.h),
          padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 4.h),
          decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(12.r), border: Border.all(color: AppColors.line, width: 2)),
          child: Text(kind == 'chest' ? 'Mở rương!' : 'Chơi nào!', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.w800, fontSize: 13.sp)),
        ),
      Semantics(
        button: true,
        label: '${asString(stop['title'])}${locked ? ' (chưa mở)' : ''}',
        child: GestureDetector(
          onTap: onTap,
          child: Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              color: face,
              shape: BoxShape.circle,
              boxShadow: [BoxShadow(color: lip, offset: Offset(0, 6.h)), if (current) BoxShadow(color: color.withValues(alpha: 0.25), spreadRadius: 8.w)],
            ),
            alignment: Alignment.center,
            child: inner,
          ),
        ),
      ),
      if (kind != 'chest' && status == 'done') Padding(padding: EdgeInsets.only(top: 8.h), child: _Stars(asInt(stop['stars']), size: 16)),
      if (boss) Padding(padding: EdgeInsets.only(top: 4.h), child: Text('Màn trùm', style: TextStyle(fontSize: 11.sp, color: AppColors.textSecondary))),
    ]);
  }
}

class _Stars extends StatelessWidget {
  const _Stars(this.n, {this.size = 18});

  final int n;
  final double size;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
        for (var s = 1; s <= 3; s++) Icon(Icons.star_rounded, size: size.sp, color: s <= n ? const Color(0xFFFFC800) : AppColors.lineStrong),
      ]);
}

class _ChestDialog extends StatelessWidget {
  const _ChestDialog({required this.gems, required this.scales});

  final int gems;
  final int scales;

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Padding(
        padding: EdgeInsets.all(24.w),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          TweenAnimationBuilder<double>(
            tween: Tween(begin: 0, end: 1),
            duration: const Duration(milliseconds: 900),
            builder: (_, t, child) => Transform.rotate(
              angle: math.sin(t * math.pi * 5) * 0.14 * (1 - t),
              child: Transform.scale(scale: 0.8 + 0.25 * t, child: child),
            ),
            child: AppIcon('chest', size: 110.w),
          ),
          SizedBox(height: 12.h),
          Text('Rương đã mở!', style: TextStyle(fontSize: 22.sp, fontWeight: FontWeight.w800)),
          SizedBox(height: 10.h),
          Row(mainAxisAlignment: MainAxisAlignment.center, children: [
            Text('+$gems ngọc', style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800, color: const Color(0xFFE062A8))),
            SizedBox(width: 20.w),
            Text('+$scales vảy', style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800, color: AppColors.beamMint)),
          ]),
          SizedBox(height: 16.h),
          FilledButton(onPressed: () => goBack(), child: const Text('Tuyệt quá!')),
        ]),
      ),
    );
  }
}

// ====================================================================== play

const gameNames = {
  'pop': 'Bắt bong bóng', 'fish': 'Câu cá', 'tone': 'Thả dấu', 'picture': 'Chọn hình', 'meaning': 'Chọn nghĩa',
  'gate': 'Chọn cửa', 'train': 'Ghép toa tàu', 'sort': 'Hái quả', 'match': 'Lật thẻ', 'spell': 'Ghép chữ',
  'order': 'Xếp câu', 'type': 'Đuổi hình bắt chữ',
};

class GamePlayController extends GetxController {
  late final String node;
  final Rxn<Json> round = Rxn<Json>();
  final RxInt at = 0.obs;
  final RxBool intro = true.obs;
  final Rxn<Json> finish = Rxn<Json>();
  final RxString error = ''.obs;
  final List<List<bool>> results = [];

  @override
  void onInit() {
    super.onInit();
    node = Get.arguments as String;
    load();
  }

  Future<void> load() async {
    round.value = null;
    finish.value = null;
    error.value = '';
    at.value = 0;
    intro.value = true;
    results.clear();
    try {
      round.value = await GamesRepository.round(node);
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
    }
  }

  List<Json> get games => asMapList(round.value?['games']);

  Future<void> done(List<bool> r) async {
    results.add(r);
    if (at.value + 1 < games.length) {
      at.value++;
      intro.value = true;
      return;
    }
    try {
      finish.value = await GamesRepository.finish(node, asString(round.value!['token']), results);
      if (Get.isRegistered<GameService>()) GameService.to.refreshSummary();
    } catch (e) {
      error.value = ApiClient.toApiException(e).message;
    }
  }

  void learnAgain() {
    final review = asMap(finish.value?['review']);
    if (asString(review['kind']) == 'lesson') {
      Get.offNamed(Routes.literacyLesson, arguments: asInt(review['lesson']));
    } else {
      final ids = (review['word_ids'] as List? ?? const []).map((e) => asInt(e)).toList();
      Get.offNamed(Routes.learningSession, arguments: LearningSessionArguments(kind: 'review', wordIds: ids));
    }
  }

  void next() {
    final nxt = asMap(finish.value?['next']);
    if (nxt.isNotEmpty && asString(nxt['kind']) != 'chest' && asString(nxt['status']) == 'open') {
      Get.offNamed(Routes.gamePlay, arguments: asString(nxt['id']), preventDuplicates: false);
    } else {
      goBack();
    }
  }
}

class GamePlayView extends GetView<GamePlayController> {
  const GamePlayView({super.key});

  @override
  Widget build(BuildContext context) {
    final lang = _langTag();
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Obx(() {
          if (controller.error.isNotEmpty) return _message(controller.error.value);
          final r = controller.round.value;
          if (r == null) return const Center(child: CircularProgressIndicator());
          if (controller.finish.value != null) return _result(r, controller.finish.value!);
          final games = controller.games;
          final at = controller.at.value;
          final game = games[at];
          return Column(children: [
            Padding(
              padding: EdgeInsets.fromLTRB(8.w, 8.h, 16.w, 8.h),
              child: Row(children: [
                IconButton(onPressed: () => goBack(), icon: const Icon(Icons.close_rounded), tooltip: 'Thoát màn chơi'),
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8.r),
                    child: LinearProgressIndicator(value: at / games.length, minHeight: 10.h, color: AppColors.primary, backgroundColor: AppColors.surfaceMuted),
                  ),
                ),
                SizedBox(width: 10.w),
                Text('${at + 1}/${games.length}', style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp)),
              ]),
            ),
            Expanded(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 250),
                child: controller.intro.value
                    ? _intro(r, game, at, games.length)
                    : SingleChildScrollView(
                        key: ValueKey('game-$at'),
                        padding: EdgeInsets.all(16.w),
                        child: Column(children: [
                          Text(asString(game['title']), textAlign: TextAlign.center, style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
                          SizedBox(height: 12.h),
                          MiniGame(key: ValueKey('mini-$at'), game: game, lang: lang, onDone: controller.done),
                        ]),
                      ),
              ),
            ),
          ]);
        }),
      ),
    );
  }

  Widget _intro(Json r, Json game, int at, int count) {
    return Center(
      key: ValueKey('intro-$at'),
      child: Padding(
        padding: EdgeInsets.all(24.w),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text('${asString(r['kind']) == 'boss' ? 'Màn trùm' : asString(r['title'])} · Trò chơi ${at + 1}/$count',
              textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp)),
          SizedBox(height: 16.h),
          AppIcon('game', size: 88.w),
          SizedBox(height: 12.h),
          Text(gameNames[asString(game['game'])] ?? '', style: TextStyle(fontSize: 28.sp, fontWeight: FontWeight.w800)),
          SizedBox(height: 8.h),
          Text(asString(game['title']), textAlign: TextAlign.center, style: TextStyle(fontSize: 15.sp, color: AppColors.textSecondary)),
          SizedBox(height: 24.h),
          FilledButton(onPressed: () => controller.intro.value = false, child: const Text('Bắt đầu')),
        ]),
      ),
    );
  }

  Widget _message(String text) => Center(
        child: Padding(
          padding: EdgeInsets.all(24.w),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Image.asset('assets/brand/mascot/prismo_think.png', width: 120.w),
            SizedBox(height: 12.h),
            Text(text, textAlign: TextAlign.center, style: TextStyle(fontSize: 16.sp)),
            SizedBox(height: 16.h),
            Wrap(spacing: 12.w, children: [
              OutlinedButton(onPressed: () => goBack(), child: const Text('Về bản đồ')),
              FilledButton(
                  onPressed: () => Get.offNamed(Routes.learningSession, arguments: const LearningSessionArguments(kind: 'learn')),
                  child: const Text('Đi học')),
            ]),
          ]),
        ),
      );

  Widget _result(Json r, Json f) {
    final passed = f['passed'] == true;
    final boss = asString(r['kind']) == 'boss';
    final title = !passed
        ? 'Chưa qua màn này'
        : !boss ? 'Qua màn rồi!' : asInt(r['level']) == 4 ? 'Thắng màn trùm cuối! Bạn đã hoàn thành cả 4 cấp.' : 'Thắng màn trùm! Cấp mới đã mở.';
    final review = asMap(f['review']);
    final nxt = asMap(f['next']);
    return Center(
      child: SingleChildScrollView(
        padding: EdgeInsets.all(24.w),
        child: Column(children: [
          Image.asset(passed ? 'assets/brand/mascot/prismo_celebrate.png' : 'assets/brand/mascot/prismo_sad.png', width: 150.w),
          SizedBox(height: 12.h),
          Text(title, textAlign: TextAlign.center, style: TextStyle(fontSize: 22.sp, fontWeight: FontWeight.w800)),
          SizedBox(height: 10.h),
          _Stars(asInt(f['stars']), size: 40),
          SizedBox(height: 8.h),
          Text('Đúng ${asInt(f['correct'])}/${asInt(f['total'])} câu (${asInt(f['percent'])}%) · cần ${asInt(r['pass_percent'])}% để qua màn',
              textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp)),
          if (asInt(f['xp']) > 0 || asInt(f['gems']) > 0)
            Padding(
              padding: EdgeInsets.only(top: 8.h),
              child: Text([if (asInt(f['xp']) > 0) '+${asInt(f['xp'])} XP', if (asInt(f['gems']) > 0) '+${asInt(f['gems'])} ngọc'].join('   '),
                  style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800, color: AppColors.xpGold)),
            ),
          if (!passed)
            Padding(
              padding: EdgeInsets.only(top: 8.h),
              child: Text('Học lại những phần còn sai rồi quay lại chơi nhé!', textAlign: TextAlign.center, style: TextStyle(fontSize: 14.sp)),
            ),
          SizedBox(height: 22.h),
          if (passed) ...[
            FilledButton(
              onPressed: controller.next,
              child: Text(nxt.isNotEmpty && asString(nxt['kind']) != 'chest' && asString(nxt['status']) == 'open'
                  ? 'Màn tiếp theo'
                  : asString(nxt['kind']) == 'chest' ? 'Đi mở rương' : 'Về bản đồ'),
            ),
            TextButton(onPressed: () => goBack(), child: const Text('Về bản đồ')),
          ] else ...[
            if (review.isNotEmpty)
              FilledButton(
                onPressed: controller.learnAgain,
                child: Text(asString(review['kind']) == 'lesson' ? 'Học lại bài ${asInt(review['lesson'])}' : 'Ôn lại những từ còn sai'),
              ),
            OutlinedButton(onPressed: controller.load, child: const Text('Chơi lại')),
          ],
        ]),
      ),
    );
  }
}

// ====================================================================== mini games

/// One mini game; reports, item by item, whether the first answer was right.
class MiniGame extends StatelessWidget {
  const MiniGame({super.key, required this.game, required this.lang, required this.onDone});

  final Json game;
  final String lang;
  final void Function(List<bool>) onDone;

  @override
  Widget build(BuildContext context) {
    final items = asMapList(game['items']);
    switch (asString(game['game'])) {
      case 'train':
        return _TrainGame(items: items, onDone: onDone);
      case 'sort':
        return _SortGame(baskets: (game['baskets'] as List).map((e) => '$e').toList(), items: items, onDone: onDone);
      case 'match':
        return _MatchGame(items: items, lang: lang, onDone: onDone);
      case 'spell':
      case 'order':
        return _TilesGame(items: items, lang: lang, onDone: onDone);
      case 'type':
        return _TypeGame(items: items, lang: lang, onDone: onDone);
      default:
        return _ChooseGame(kind: asString(game['game']), items: items, lang: lang, onDone: onDone);
    }
  }
}

String _normalize(String s) => s.toLowerCase().replaceAll(RegExp(r'[.,!?;:"“”‘’…。，！？]'), '').replaceAll(RegExp(r'\s+'), ' ').trim();

/// Steps through the items of one game: [answer] records the first answer, then moves on after a moment.
mixin _Steps<T extends StatefulWidget> on State<T> {
  int i = 0;
  bool? answered;
  final List<bool> _results = [];
  Timer? _timer;

  int get count;
  void Function(List<bool>) get finished;
  void onItem() {}

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => onItem());
  }

  void answer(bool ok) {
    if (answered != null) return;
    setState(() => answered = ok);
    _results.add(ok);
    _timer = Timer(Duration(milliseconds: ok ? 850 : 1700), () {
      if (!mounted) return;
      if (_results.length >= count) {
        finished(_results);
      } else {
        setState(() {
          i++;
          answered = null;
        });
        onItem();
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }
}

Widget _dots(int count, int at) => Row(mainAxisAlignment: MainAxisAlignment.center, children: [
      for (var k = 0; k < count; k++)
        AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          margin: EdgeInsets.symmetric(horizontal: 3.w),
          width: k == at ? 22.w : 8.w,
          height: 8.w,
          decoration: BoxDecoration(
              color: k < at ? _green : k == at ? AppColors.primary : AppColors.lineStrong, borderRadius: BorderRadius.circular(4.r)),
        ),
    ]);

Widget _feedback(bool? ok, String answer) {
  if (ok == null) return SizedBox(height: 48.h);
  return Container(
    height: 48.h,
    margin: EdgeInsets.only(top: 12.h),
    padding: EdgeInsets.symmetric(horizontal: 14.w),
    decoration: BoxDecoration(color: ok ? AppColors.successSoft : AppColors.errorSoft, borderRadius: BorderRadius.circular(14.r)),
    alignment: Alignment.center,
    child: Text(ok ? '✓ Giỏi lắm!' : '✗ Đáp án đúng: $answer',
        style: TextStyle(fontSize: 16.sp, fontWeight: FontWeight.w700, color: ok ? AppColors.success : AppColors.error)),
  );
}

Widget _speaker(dynamic audio, {double size = 64}) => GestureDetector(
      onTap: () => _sayAudio(audio),
      child: Container(
        width: size.w,
        height: size.w,
        decoration: BoxDecoration(color: AppColors.primary, shape: BoxShape.circle, boxShadow: [BoxShadow(color: AppColors.primaryDark, offset: Offset(0, 4.h))]),
        child: Icon(Icons.volume_up_rounded, color: Colors.white, size: (size * 0.45).sp),
      ),
    );

Widget _picture(Json p, double size) {
  final image = asString(p['image']);
  final emoji = asString(p['emoji']);
  if (image.isEmpty && emoji.isEmpty) return const SizedBox.shrink();
  return WordPicture(imageUrl: image.isEmpty ? null : image, emoji: emoji, size: size);
}

Widget _optionFace(Json o, String lang, {double fontSize = 20, Color? color}) {
  if (asString(o['image']).isNotEmpty || asString(o['emoji']).isNotEmpty) return _picture(o, 80.w);
  final s = asString(o['s']);
  return Column(mainAxisSize: MainAxisSize.min, children: [
    Text(asString(o['t']), textAlign: TextAlign.center, locale: localeFor(lang),
        style: TextStyle(fontSize: fontSize.sp, fontWeight: FontWeight.w700, color: color ?? AppColors.textPrimary)),
    if (s.isNotEmpty) Text(s, style: TextStyle(fontSize: 12.sp, color: color?.withValues(alpha: 0.8) ?? AppColors.textSecondary)),
  ]);
}

class _Tile extends StatelessWidget {
  const _Tile({required this.child, required this.onTap, this.state, this.selected = false, this.padding});

  final Widget child;
  final VoidCallback? onTap;
  final bool? state; // true right, false wrong, null neutral
  final bool selected;
  final EdgeInsets? padding;

  @override
  Widget build(BuildContext context) {
    final border = state == true ? AppColors.beamMint : state == false ? AppColors.error : selected ? AppColors.primary : AppColors.line;
    final bg = state == true ? AppColors.successSoft : state == false ? AppColors.errorSoft : selected ? AppColors.primarySoft : AppColors.surface;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: padding ?? EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(14.r),
          border: Border(
            top: BorderSide(color: border, width: 2), left: BorderSide(color: border, width: 2),
            right: BorderSide(color: border, width: 2), bottom: BorderSide(color: border, width: 4)),
        ),
        child: child,
      ),
    );
  }
}

// ---------------------------------------------------------------------- choose games

const _bubbleColors = [Color(0xFFFF86C8), Color(0xFF1CB0F6), Color(0xFFFFC800), Color(0xFF58CC02), Color(0xFFCE82FF), Color(0xFFFF9600)];

class _ChooseGame extends StatefulWidget {
  const _ChooseGame({required this.kind, required this.items, required this.lang, required this.onDone});

  final String kind;
  final List<Json> items;
  final String lang;
  final void Function(List<bool>) onDone;

  @override
  State<_ChooseGame> createState() => _ChooseGameState();
}

class _ChooseGameState extends State<_ChooseGame> with _Steps<_ChooseGame>, SingleTickerProviderStateMixin {
  String? picked;
  late final AnimationController _float = AnimationController(vsync: this, duration: const Duration(seconds: 3))..repeat();

  @override
  int get count => widget.items.length;
  @override
  void Function(List<bool>) get finished => widget.onDone;

  Json get item => widget.items[i];

  @override
  void onItem() {
    setState(() => picked = null);
    Future.delayed(const Duration(milliseconds: 350), () => _sayAudio(item['prompt'] is Map ? item['prompt']['audio'] : null));
  }

  @override
  void dispose() {
    _float.dispose();
    super.dispose();
  }

  void pick(Json o) {
    if (answered != null) return;
    setState(() => picked = asString(o['t']));
    answer(asString(o['t']) == asString(item['answer']));
  }

  bool? stateOf(Json o) {
    if (answered == null) return null;
    final t = asString(o['t']);
    if (t == asString(item['answer'])) return true;
    return t == picked ? false : null;
  }

  @override
  Widget build(BuildContext context) {
    final prompt = asMap(item['prompt']);
    final options = asMapList(item['options']);
    final right = options.firstWhere((o) => asString(o['t']) == asString(item['answer']), orElse: () => <String, dynamic>{});
    final rightLabel = asString(right['image']).isNotEmpty || asString(right['emoji']).isNotEmpty ? '' : asString(right['t']);
    return Column(children: [
      _dots(count, i),
      SizedBox(height: 16.h),
      _picture(prompt, 120.w),
      if (asString(prompt['text']).isNotEmpty)
        GestureDetector(
          onTap: () => _sayAudio(prompt['audio']),
          child: Text(asString(prompt['text']), locale: localeFor(widget.lang),
              style: TextStyle(fontSize: (widget.kind == 'meaning' ? 40 : 52).sp, fontWeight: FontWeight.w800)),
        )
      else
        _speaker(prompt['audio']),
      if (asString(prompt['sub']).isNotEmpty)
        Padding(padding: EdgeInsets.only(top: 6.h), child: Text(asString(prompt['sub']), textAlign: TextAlign.center, style: TextStyle(fontSize: 15.sp, color: AppColors.textSecondary))),
      if (widget.kind == 'tone' && widget.lang == 'vi')
        Padding(padding: EdgeInsets.only(top: 6.h), child: Text('Thêm dấu nào thì thành tiếng vừa nghe?', style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp))),
      SizedBox(height: 18.h),
      _options(options),
      _feedback(answered, rightLabel),
    ]);
  }

  Widget _options(List<Json> options) {
    switch (widget.kind) {
      case 'pop':
        return AnimatedBuilder(
          animation: _float,
          builder: (_, __) => Wrap(
            alignment: WrapAlignment.center,
            spacing: 14.w,
            runSpacing: 18.h,
            children: [
              for (var k = 0; k < options.length; k++)
                Transform.translate(
                  offset: Offset(0, math.sin(_float.value * 2 * math.pi + k * 1.3) * 8.h),
                  child: AnimatedScale(
                    scale: answered == true && asString(options[k]['t']) == picked ? 1.4 : 1,
                    duration: const Duration(milliseconds: 250),
                    child: AnimatedOpacity(
                      opacity: answered == true && asString(options[k]['t']) == picked ? 0 : 1,
                      duration: const Duration(milliseconds: 300),
                      child: GestureDetector(
                        onTap: () => pick(options[k]),
                        child: Container(
                          width: 104.w,
                          height: 104.w,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: RadialGradient(center: const Alignment(-0.4, -0.45), radius: 0.9,
                                colors: [Colors.white.withValues(alpha: 0.75), _bubbleColors[k % _bubbleColors.length], _bubbleColors[k % _bubbleColors.length]],
                                stops: const [0, 0.22, 1]),
                            border: stateOf(options[k]) == true ? Border.all(color: _green, width: 4) : stateOf(options[k]) == false ? Border.all(color: AppColors.error, width: 4) : null,
                          ),
                          child: _optionFace(options[k], widget.lang, fontSize: 22, color: Colors.white),
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        );
      case 'fish':
        return Container(
          width: double.infinity,
          padding: EdgeInsets.symmetric(vertical: 14.h),
          decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(22.r),
              gradient: const LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [Color(0xFFBFE9FF), Color(0xFF38BDF8)])),
          child: AnimatedBuilder(
            animation: _float,
            builder: (_, __) => Column(children: [
              for (var k = 0; k < options.length; k++)
                Padding(
                  padding: EdgeInsets.symmetric(vertical: 5.h),
                  child: Transform.translate(
                    offset: Offset(math.sin(_float.value * 2 * math.pi + k * 1.7) * 18.w, 0),
                    child: _Tile(
                      onTap: () => pick(options[k]),
                      state: stateOf(options[k]),
                      padding: EdgeInsets.fromLTRB(14.w, 8.h, 26.w, 8.h),
                      child: Row(mainAxisSize: MainAxisSize.min, children: [
                        Text('🐟', style: TextStyle(fontSize: 22.sp)),
                        SizedBox(width: 8.w),
                        _optionFace(options[k], widget.lang, fontSize: 22),
                      ]),
                    ),
                  ),
                ),
            ]),
          ),
        );
      case 'gate':
        return Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          for (final o in options)
            Padding(
              padding: EdgeInsets.symmetric(horizontal: 12.w),
              child: GestureDetector(
                onTap: () => pick(o),
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: stateOf(o) == true ? 1 : 0),
                  duration: const Duration(milliseconds: 450),
                  builder: (_, t, child) => Transform(
                    alignment: Alignment.centerLeft,
                    transform: Matrix4.identity()..setEntry(3, 2, 0.002)..rotateY(-t * 0.9),
                    child: child,
                  ),
                  child: Container(
                    width: 104.w,
                    height: 160.h,
                    decoration: BoxDecoration(
                      color: const Color(0xFFC98546),
                      border: Border.all(color: stateOf(o) == false ? AppColors.error : const Color(0xFFA0662F), width: 4),
                      borderRadius: BorderRadius.vertical(top: Radius.circular(52.r), bottom: Radius.circular(8.r)),
                    ),
                    alignment: Alignment.center,
                    child: Text(asString(o['t']), style: TextStyle(fontSize: 36.sp, fontWeight: FontWeight.w800, color: Colors.white)),
                  ),
                ),
              ),
            ),
        ]);
      default:
        return GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: 10.h,
          crossAxisSpacing: 10.w,
          childAspectRatio: widget.kind == 'picture' ? 1.1 : 1.9,
          children: [
            for (final o in options)
              _Tile(onTap: () => pick(o), state: stateOf(o), child: Center(child: _optionFace(o, widget.lang, fontSize: widget.kind == 'tone' ? 28 : 18))),
          ],
        );
    }
  }
}

// ---------------------------------------------------------------------- train

class _TrainGame extends StatefulWidget {
  const _TrainGame({required this.items, required this.onDone});

  final List<Json> items;
  final void Function(List<bool>) onDone;

  @override
  State<_TrainGame> createState() => _TrainGameState();
}

class _TrainGameState extends State<_TrainGame> with _Steps<_TrainGame> {
  final Map<String, String> pick = {};

  @override
  int get count => widget.items.length;
  @override
  void Function(List<bool>) get finished => widget.onDone;
  Json get item => widget.items[i];

  @override
  void onItem() {
    setState(pick.clear);
    Future.delayed(const Duration(milliseconds: 350), () => _sayAudio(item['audio']));
  }

  @override
  Widget build(BuildContext context) {
    final a = asMap(item['answer']);
    final tones = asMapList(item['tones']);
    String? toneShown() {
      final t = tones.where((x) => asString(x['code']) == pick['tone']).toList();
      if (t.isEmpty) return null;
      return asString(t.first['symbol']).isEmpty ? 'ngang' : asString(t.first['symbol']);
    }

    final cars = [('Âm đầu', pick['onset'] == '∅' ? '–' : pick['onset']), ('Vần', pick['rhyme']), ('Dấu', toneShown())];
    Widget row(String key, String label, List<(String, String)> opts) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: TextStyle(fontSize: 12.sp, color: AppColors.textHint)),
          SizedBox(height: 4.h),
          Wrap(spacing: 8.w, runSpacing: 8.h, children: [
            for (final (v, l) in opts)
              _Tile(
                onTap: answered == null ? () => setState(() => pick[key] = v) : null,
                selected: pick[key] == v,
                padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 8.h),
                child: Text(l, style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w600)),
              ),
          ]),
          SizedBox(height: 12.h),
        ]);
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      _dots(count, i),
      SizedBox(height: 12.h),
      Center(child: _speaker(item['audio'])),
      SizedBox(height: 14.h),
      AnimatedSlide(
        offset: answered == true ? const Offset(1.5, 0) : Offset.zero,
        duration: const Duration(milliseconds: 800),
        curve: Curves.easeIn,
        child: Row(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text('🚂', style: TextStyle(fontSize: 40.sp)),
          for (final (label, value) in cars)
            Padding(
              padding: EdgeInsets.only(left: 4.w),
              child: Column(children: [
                Container(
                  constraints: BoxConstraints(minWidth: 56.w),
                  height: 52.h,
                  padding: EdgeInsets.symmetric(horizontal: 8.w),
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: value != null ? AppColors.primary : AppColors.surfaceMuted,
                    borderRadius: BorderRadius.circular(10.r),
                    border: Border(bottom: BorderSide(color: value != null ? AppColors.primaryDark : AppColors.lineStrong, width: 4)),
                  ),
                  child: Text(value ?? '?', style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800, color: value != null ? Colors.white : AppColors.textHint)),
                ),
                Text(label, style: TextStyle(fontSize: 10.sp, color: AppColors.textHint)),
              ]),
            ),
        ]),
      ),
      SizedBox(height: 16.h),
      row('onset', 'Âm đầu', [for (final o in (item['onsets'] as List).map((e) => '$e')) (o, o == '∅' ? '(không có)' : o)]),
      row('rhyme', 'Vần', [for (final r in (item['rhymes'] as List).map((e) => '$e')) (r, r)]),
      row('tone', 'Dấu', [for (final t in tones) (asString(t['code']), '${asString(t['symbol'])} ${asString(t['label'])}'.trim())]),
      if (answered == null)
        FilledButton(
          onPressed: pick.length == 3
              ? () => answer(pick['onset'] == asString(a['onset']) && pick['rhyme'] == asString(a['rhyme']) && pick['tone'] == asString(a['tone']))
              : null,
          child: const Text('Cho tàu chạy'),
        )
      else
        _feedback(answered, asString(item['text'])),
    ]);
  }
}

// ---------------------------------------------------------------------- sort

class _SortGame extends StatefulWidget {
  const _SortGame({required this.baskets, required this.items, required this.onDone});

  final List<String> baskets;
  final List<Json> items;
  final void Function(List<bool>) onDone;

  @override
  State<_SortGame> createState() => _SortGameState();
}

class _SortGameState extends State<_SortGame> with _Steps<_SortGame> {
  final Map<String, int> counts = {};
  String? target;

  @override
  int get count => widget.items.length;
  @override
  void Function(List<bool>) get finished => widget.onDone;
  Json get item => widget.items[i];

  @override
  void onItem() {
    setState(() => target = null);
    Future.delayed(const Duration(milliseconds: 300), () => _sayAudio(item['audio']));
  }

  void drop(String b) {
    if (answered != null) return;
    final ok = b == asString(item['answer']);
    setState(() {
      target = b;
      if (ok) counts[b] = (counts[b] ?? 0) + 1;
    });
    answer(ok);
  }

  @override
  Widget build(BuildContext context) {
    final towards = target == null ? 0.0 : (widget.baskets.indexOf(target!) == 0 ? -0.6 : 0.6);
    return Column(children: [
      _dots(count, i),
      SizedBox(height: 14.h),
      SizedBox(
        height: 140.h,
        child: AnimatedSlide(
          offset: answered != null ? Offset(towards, 0.9) : Offset.zero,
          duration: const Duration(milliseconds: 550),
          child: AnimatedOpacity(
            opacity: answered != null ? 0 : 1,
            duration: const Duration(milliseconds: 550),
            child: GestureDetector(
              onTap: () => _sayAudio(item['audio']),
              child: Stack(alignment: Alignment.center, children: [
                Text('🍎', style: TextStyle(fontSize: 100.sp)),
                Padding(
                  padding: EdgeInsets.only(top: 18.h),
                  child: Text(asString(item['t']), style: TextStyle(fontSize: 22.sp, fontWeight: FontWeight.w800, color: Colors.white, shadows: const [Shadow(color: Colors.black54, offset: Offset(0, 2))])),
                ),
              ]),
            ),
          ),
        ),
      ),
      SizedBox(height: 16.h),
      Row(mainAxisAlignment: MainAxisAlignment.center, children: [
        for (final b in widget.baskets)
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 8.w),
            child: _Tile(
              onTap: () => drop(b),
              state: answered == null ? null : b == asString(item['answer']) ? true : b == target ? false : null,
              padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 10.h),
              child: Column(children: [
                Text('🧺', style: TextStyle(fontSize: 42.sp)),
                Text('vần $b', style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w800, color: AppColors.primary)),
                Text('${counts[b] ?? 0} quả', style: TextStyle(fontSize: 11.sp, color: AppColors.textHint)),
              ]),
            ),
          ),
      ]),
      _feedback(answered, 'vần ${asString(item['answer'])}'),
    ]);
  }
}

// ---------------------------------------------------------------------- match (memory cards)

class _MatchGame extends StatefulWidget {
  const _MatchGame({required this.items, required this.lang, required this.onDone});

  final List<Json> items;
  final String lang;
  final void Function(List<bool>) onDone;

  @override
  State<_MatchGame> createState() => _MatchGameState();
}

class _MatchGameState extends State<_MatchGame> {
  late final List<(String, int, Json)> cards; // key, pair, face
  final List<String> open = [];
  final Set<int> found = {};
  final Set<int> missed = {};
  bool busy = false;

  @override
  void initState() {
    super.initState();
    cards = [
      for (var k = 0; k < widget.items.length; k++) ...[('a$k', k, asMap(widget.items[k]['a'])), ('b$k', k, asMap(widget.items[k]['b']))],
    ]..shuffle();
  }

  void flip((String, int, Json) c) {
    if (busy || open.contains(c.$1) || found.contains(c.$2)) return;
    setState(() => open.add(c.$1));
    if (open.length < 2) return;
    final x = cards.firstWhere((cc) => cc.$1 == open[0]);
    final y = cards.firstWhere((cc) => cc.$1 == open[1]);
    busy = true;
    Future.delayed(Duration(milliseconds: x.$2 == y.$2 ? 350 : 900), () {
      if (!mounted) return;
      setState(() {
        if (x.$2 == y.$2) {
          found.add(x.$2);
        } else {
          missed..add(x.$2)..add(y.$2);
        }
        open.clear();
        busy = false;
      });
      if (found.length == widget.items.length) {
        Future.delayed(const Duration(milliseconds: 500), () {
          if (mounted) widget.onDone([for (var k = 0; k < widget.items.length; k++) !missed.contains(k)]);
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Text('Đã tìm được ${found.length}/${widget.items.length} cặp', style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp)),
      SizedBox(height: 12.h),
      GridView.count(
        crossAxisCount: 3,
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        mainAxisSpacing: 10.h,
        crossAxisSpacing: 10.w,
        childAspectRatio: 0.9,
        children: [
          for (final c in cards)
            GestureDetector(
              onTap: () => flip(c),
              child: TweenAnimationBuilder<double>(
                tween: Tween(begin: 0, end: open.contains(c.$1) || found.contains(c.$2) ? 1 : 0),
                duration: const Duration(milliseconds: 300),
                builder: (_, t, __) {
                  final shown = t > 0.5;
                  return Transform(
                    alignment: Alignment.center,
                    transform: Matrix4.identity()..setEntry(3, 2, 0.002)..rotateY((1 - t) * math.pi),
                    child: Container(
                      decoration: BoxDecoration(
                        color: found.contains(c.$2) ? AppColors.successSoft : shown ? AppColors.surface : AppColors.primary,
                        borderRadius: BorderRadius.circular(14.r),
                        border: Border.all(color: found.contains(c.$2) ? AppColors.beamMint : shown ? AppColors.primaryLight : AppColors.primaryDark, width: 2),
                      ),
                      alignment: Alignment.center,
                      padding: EdgeInsets.all(4.w),
                      child: shown
                          ? Transform(alignment: Alignment.center, transform: Matrix4.rotationY(t < 1 ? math.pi : 0), child: _optionFace(c.$3, widget.lang, fontSize: 16))
                          : Transform(  // the card is turned over: turn its back face round so "?" reads normally
                              alignment: Alignment.center,
                              transform: Matrix4.rotationY(math.pi),
                              child: Text('?', style: TextStyle(fontSize: 28.sp, color: Colors.white, fontWeight: FontWeight.w800))),
                    ),
                  );
                },
              ),
            ),
        ],
      ),
    ]);
  }
}

// ---------------------------------------------------------------------- tiles (spell a word / order a sentence)

class _TilesGame extends StatefulWidget {
  const _TilesGame({required this.items, required this.lang, required this.onDone});

  final List<Json> items;
  final String lang;
  final void Function(List<bool>) onDone;

  @override
  State<_TilesGame> createState() => _TilesGameState();
}

class _TilesGameState extends State<_TilesGame> with _Steps<_TilesGame> {
  final List<int> used = [];

  @override
  int get count => widget.items.length;
  @override
  void Function(List<bool>) get finished => widget.onDone;
  Json get item => widget.items[i];
  List<String> get tiles => (item['tiles'] as List).map((e) => '$e').toList();

  @override
  void onItem() {
    setState(used.clear);
    Future.delayed(const Duration(milliseconds: 350), () => _sayAudio(asMap(item['prompt'])['audio']));
  }

  @override
  Widget build(BuildContext context) {
    final prompt = asMap(item['prompt']);
    final joiner = asString(item['joiner']);
    final built = used.map((k) => tiles[k]).join(joiner);
    Widget tile(String text, VoidCallback? onTap, {bool faded = false}) => Opacity(
          opacity: faded ? 0.25 : 1,
          child: _Tile(
            onTap: onTap,
            padding: EdgeInsets.symmetric(horizontal: joiner == ' ' ? 12.w : 0, vertical: 8.h),
            child: SizedBox(
              width: joiner == ' ' ? null : 34.w,
              child: Text(text, textAlign: TextAlign.center, locale: localeFor(widget.lang), style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.w700)),
            ),
          ),
        );
    return Column(children: [
      _dots(count, i),
      SizedBox(height: 12.h),
      Row(mainAxisAlignment: MainAxisAlignment.center, children: [
        _picture(prompt, 90.w),
        SizedBox(width: 12.w),
        _speaker(prompt['audio'], size: 56),
      ]),
      if (asString(prompt['sub']).isNotEmpty)
        Padding(padding: EdgeInsets.only(top: 8.h), child: Text('“${asString(prompt['sub'])}”', textAlign: TextAlign.center, style: TextStyle(fontSize: 15.sp, color: AppColors.textSecondary))),
      SizedBox(height: 14.h),
      Container(
        width: double.infinity,
        constraints: BoxConstraints(minHeight: 64.h),
        padding: EdgeInsets.all(8.w),
        decoration: BoxDecoration(
          color: answered == null ? null : answered! ? AppColors.successSoft : AppColors.errorSoft,
          borderRadius: BorderRadius.circular(14.r),
          border: Border.all(color: answered == null ? AppColors.lineStrong : answered! ? AppColors.beamMint : AppColors.error, width: 2),
        ),
        child: Wrap(alignment: WrapAlignment.center, spacing: 6.w, runSpacing: 6.h, children: [
          for (var p = 0; p < used.length; p++) tile(tiles[used[p]], answered == null ? () => setState(() => used.removeAt(p)) : null),
        ]),
      ),
      SizedBox(height: 14.h),
      Wrap(alignment: WrapAlignment.center, spacing: 6.w, runSpacing: 6.h, children: [
        for (var k = 0; k < tiles.length; k++)
          tile(tiles[k], used.contains(k) || answered != null ? null : () => setState(() => used.add(k)), faded: used.contains(k)),
      ]),
      SizedBox(height: 16.h),
      if (answered == null)
        FilledButton(onPressed: used.isEmpty ? null : () => answer(_normalize(built) == _normalize(asString(item['answer']))), child: const Text('Kiểm tra'))
      else
        _feedback(answered, asString(item['answer'])),
    ]);
  }
}

// ---------------------------------------------------------------------- type (picture -> write the word)

class _TypeGame extends StatefulWidget {
  const _TypeGame({required this.items, required this.lang, required this.onDone});

  final List<Json> items;
  final String lang;
  final void Function(List<bool>) onDone;

  @override
  State<_TypeGame> createState() => _TypeGameState();
}

class _TypeGameState extends State<_TypeGame> with _Steps<_TypeGame> {
  final input = TextEditingController();

  @override
  int get count => widget.items.length;
  @override
  void Function(List<bool>) get finished => widget.onDone;
  Json get item => widget.items[i];

  @override
  void onItem() {
    input.clear();
    setState(() {});
    Future.delayed(const Duration(milliseconds: 350), () => _sayAudio(asMap(item['prompt'])['audio']));
  }

  @override
  void dispose() {
    input.dispose();
    super.dispose();
  }

  void check() {
    if (input.text.trim().isEmpty) return;
    final accepted = (item['accepted'] as List? ?? [item['answer']]).map((e) => _normalize('$e'));
    answer(accepted.contains(_normalize(input.text)));
  }

  void _insert(String Function(String text, int cursor) fn, int Function(int cursor) moveTo) {
    final sel = input.selection;
    final cursor = sel.isValid ? sel.baseOffset : input.text.length;
    input.value = TextEditingValue(text: fn(input.text, cursor), selection: TextSelection.collapsed(offset: moveTo(cursor)));
  }

  @override
  Widget build(BuildContext context) {
    final prompt = asMap(item['prompt']);
    return Column(children: [
      _dots(count, i),
      SizedBox(height: 12.h),
      _picture(prompt, 140.w),
      SizedBox(height: 10.h),
      _speaker(prompt['audio'], size: 52),
      SizedBox(height: 14.h),
      TextField(
        controller: input,
        enabled: answered == null,
        textAlign: TextAlign.center,
        style: TextStyle(fontSize: 24.sp),
        onSubmitted: (_) => check(),
        decoration: InputDecoration(border: OutlineInputBorder(borderRadius: BorderRadius.circular(14.r))),
      ),
      if (widget.lang == 'vi' && answered == null) ...[
        SizedBox(height: 8.h),
        Wrap(alignment: WrapAlignment.center, spacing: 4.w, runSpacing: 4.h, children: [
          for (final l in specialLetters)
            OutlinedButton(
                onPressed: () => _insert((t, c) => t.substring(0, c) + l + t.substring(c), (c) => c + l.length),
                child: Text(l, style: TextStyle(fontSize: 18.sp))),
          for (final (tone, label) in [('huyen', '`'), ('sac', '´'), ('hoi', '?'), ('nga', '~'), ('nang', '.')])
            OutlinedButton(
              onPressed: () {
                final sel = input.selection;
                final cursor = sel.isValid ? sel.baseOffset : input.text.length;
                final (text, pos) = toneAtCursor(input.text, cursor, tone);
                input.value = TextEditingValue(text: text, selection: TextSelection.collapsed(offset: pos));
              },
              child: Text(label, style: TextStyle(fontSize: 18.sp)),
            ),
        ]),
      ],
      SizedBox(height: 14.h),
      if (answered == null)
        ListenableBuilder(
          listenable: input,
          builder: (_, __) => FilledButton(onPressed: input.text.trim().isEmpty ? null : check, child: const Text('Kiểm tra')),
        )
      else
        _feedback(answered, asString(item['answer'])),
    ]);
  }
}
