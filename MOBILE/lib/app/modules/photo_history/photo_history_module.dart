import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/target_word.dart';
import '../../data/models/api/learning_extra.dart';
import '../../data/models/api/vocab.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/local_shots.dart';
import '../../routes/app_pages.dart';
import '../photo_dialogue/photo_dialogue_module.dart';

const _boxColor = Color(0xFF10C79A);

/// One word found in a photo: three slices of watermelon are one word, ×3.
class ShotWord {
  ShotWord(this.item);

  final DetectedItem item;
  int count = 1;
  bool saved = false;

  WordCard? get card => item.savedCard;
  String get label => item.correctedLabel.isNotEmpty ? item.correctedLabel : item.label;
}

List<ShotWord> wordsOf(DetectionResult d) {
  final byKey = <String, ShotWord>{};
  for (final i in d.items.where((i) => !i.dismissed)) {
    final key = i.correctedLabel.isNotEmpty ? i.correctedLabel : i.label;
    final w = byKey[key];
    if (w == null) {
      byKey[key] = ShotWord(i)..saved = i.selected;
    } else {
      w.count++;
      w.saved |= i.selected;
    }
  }
  // saved words first: they are what the learner chose to learn from this photo
  return byKey.values.toList()..sort((a, b) => (b.saved ? 1 : 0) - (a.saved ? 1 : 0));
}

String shotTime(DateTime? t) {
  if (t == null) return '';
  final d = DateTime.now().difference(t);
  if (d.inMinutes < 1) return 'Vừa xong';
  if (d.inMinutes < 60) return '${d.inMinutes} phút trước';
  if (d.inHours < 24) return '${d.inHours} giờ trước';
  if (d.inDays < 7) return '${d.inDays} ngày trước';
  return '${t.day.toString().padLeft(2, '0')}/${t.month.toString().padLeft(2, '0')}/${t.year}';
}

/// The photo: from the server, else the copy kept on the phone (detected on the phone), else a placeholder.
class ShotPhoto extends StatelessWidget {
  const ShotPhoto(this.shot, {super.key, this.fit = BoxFit.cover});

  final DetectionResult shot;
  final BoxFit fit;

  @override
  Widget build(BuildContext context) {
    final placeholder = Container(
      color: AppColors.primarySoft,
      alignment: Alignment.center,
      padding: EdgeInsets.all(12.w),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Icon(Icons.phone_android_rounded, color: AppColors.textSecondary, size: 28.sp),
        SizedBox(height: 6.h),
        Text('Nhận diện trên máy, ảnh không được lưu', textAlign: TextAlign.center,
            style: TextStyle(fontSize: 11.sp, color: AppColors.textSecondary)),
      ]),
    );
    if (shot.image != null) {
      return CachedNetworkImage(imageUrl: shot.image!, fit: fit, width: double.infinity,
          placeholder: (_, __) => Container(color: AppColors.primarySoft), errorWidget: (_, __, ___) => placeholder);
    }
    return FutureBuilder<File?>(
      future: LocalShots.fileFor(shot.id),
      builder: (_, snap) => snap.data != null ? Image.file(snap.data!, fit: fit, width: double.infinity) : placeholder,
    );
  }
}

// ---------------------------------------------------------------- gallery

enum ShotFilter { all, saved, unsaved }

class PhotoHistoryView extends StatefulWidget {
  const PhotoHistoryView({super.key});

  @override
  State<PhotoHistoryView> createState() => _PhotoHistoryViewState();
}

class _PhotoHistoryViewState extends State<PhotoHistoryView> {
  final _scroll = ScrollController();
  final List<DetectionResult> _shots = [];
  ShotFilter _filter = ShotFilter.all;
  int _page = 0;
  bool _more = true;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _scroll.addListener(() {
      if (_scroll.position.pixels > _scroll.position.maxScrollExtent - 400) _next();
    });
    _next();
  }

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _reload() async {
    setState(() {
      _shots.clear();
      _page = 0;
      _more = true;
      _error = null;
    });
    await _next();
  }

  Future<void> _next() async {
    if (_loading || !_more) return;
    _loading = true;
    final filter = _filter;
    try {
      final (list, more) = await DetectionRepository.history(
          page: _page + 1, confirmed: filter == ShotFilter.all ? null : filter == ShotFilter.saved);
      if (!mounted || filter != _filter) return;
      setState(() {
        _shots.addAll(list);
        _page++;
        _more = more;
      });
    } catch (e) {
      if (mounted) setState(() => _error = ApiClient.toApiException(e).message);
    } finally {
      _loading = false;
      if (mounted) setState(() {});
    }
  }

  void _setFilter(ShotFilter f) {
    if (f == _filter) return;
    _filter = f;
    _loading = false;
    _reload();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Lịch sử ảnh'),
        backgroundColor: AppColors.appBarBackground,
        actions: [
          IconButton(
            tooltip: 'Chụp ảnh mới',
            icon: const Icon(Icons.photo_camera_outlined),
            onPressed: () => Get.toNamed(Routes.cameraDetection),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _reload,
        child: CustomScrollView(
          controller: _scroll,
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 4.h),
                child: Wrap(spacing: 8.w, children: [
                  for (final (f, label) in [
                    (ShotFilter.all, 'Tất cả'),
                    (ShotFilter.saved, 'Đã lưu từ'),
                    (ShotFilter.unsaved, 'Chưa lưu từ'),
                  ])
                    ChoiceChip(
                      label: Text(label),
                      selected: _filter == f,
                      onSelected: (_) => _setFilter(f),
                      showCheckmark: false,
                      selectedColor: AppColors.buttonActive,
                      labelStyle: TextStyle(
                          color: _filter == f ? Colors.white : AppColors.textPrimary, fontWeight: FontWeight.w600),
                      shape: const StadiumBorder(),
                    ),
                ]),
              ),
            ),
            if (_shots.isEmpty)
              SliverFillRemaining(hasScrollBody: false, child: _empty())
            else
              SliverPadding(
                padding: EdgeInsets.fromLTRB(16.w, 8.h, 16.w, 24.h),
                sliver: SliverGrid(
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: MediaQuery.of(context).size.width > 600 ? 3 : 2,
                    mainAxisSpacing: 18.h,
                    crossAxisSpacing: 12.w,
                    childAspectRatio: 0.74,
                  ),
                  delegate: SliverChildBuilderDelegate((_, i) => _tile(_shots[i]), childCount: _shots.length),
                ),
              ),
            if (_shots.isNotEmpty && _more)
              const SliverToBoxAdapter(
                  child: Padding(padding: EdgeInsets.all(16), child: Center(child: CircularProgressIndicator()))),
          ],
        ),
      ),
    );
  }

  Widget _empty() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    final (title, body) = _error != null
        ? ('Không tải được ảnh', _error!)
        : switch (_filter) {
            ShotFilter.saved => ('Chưa có ảnh nào đã lưu từ', 'Chụp ảnh rồi chọn những từ muốn học để lưu vào thư viện.'),
            ShotFilter.unsaved => ('Ảnh nào cũng đã lưu từ', 'Bạn đã lưu từ của mọi ảnh đã chụp.'),
            ShotFilter.all => ('Bạn chưa chụp ảnh nào', 'Chụp một đồ vật quanh bạn để học tên của nó.'),
          };
    return Padding(
      padding: EdgeInsets.all(32.w),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.photo_library_outlined, size: 56.sp, color: AppColors.textHint),
        SizedBox(height: 12.h),
        Text(title, textAlign: TextAlign.center,
            style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
        SizedBox(height: 6.h),
        Text(body, textAlign: TextAlign.center, style: TextStyle(color: AppColors.textSecondary)),
        SizedBox(height: 16.h),
        if (_error != null)
          OutlinedButton(onPressed: _reload, child: const Text('Thử lại'))
        else if (_filter == ShotFilter.all)
          FilledButton.icon(
            onPressed: () => Get.toNamed(Routes.cameraDetection),
            icon: const Icon(Icons.photo_camera_outlined),
            label: const Text('Chụp ảnh đầu tiên'),
          )
        else
          OutlinedButton(onPressed: () => _setFilter(ShotFilter.all), child: const Text('Xem tất cả ảnh')),
      ]),
    );
  }

  /// A photo with a quiet caption under it: the main word, then its meaning and when (no card chrome).
  Widget _tile(DetectionResult d) {
    final words = wordsOf(d);
    final main = words.isEmpty ? null : words.first;
    final target = main?.card?.target;
    return GestureDetector(
      onTap: () => Get.toNamed(Routes.photoShot, arguments: d),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        AspectRatio(
          aspectRatio: 1,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(14.r),
            child: Stack(fit: StackFit.expand, children: [
              ShotPhoto(d),
              if (d.confirmed)
                Positioned(
                  top: 6.w,
                  right: 6.w,
                  child: Container(
                    padding: EdgeInsets.all(3.w),
                    decoration: const BoxDecoration(color: _boxColor, shape: BoxShape.circle),
                    child: Icon(Icons.check_rounded, color: Colors.white, size: 14.sp, semanticLabel: 'Đã lưu từ'),
                  ),
                ),
            ]),
          ),
        ),
        SizedBox(height: 8.h),
        Row(children: [
          Flexible(
            child: target != null
                ? LangText(target.text, language: target.language, maxLines: 1,
                    style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary))
                : Text(main?.label ?? 'Không có đồ vật', maxLines: 1, overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
          ),
          if (words.length > 1)
            Text('  +${words.length - 1}', style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
        ]),
        Text(
          [if ((main?.card?.meaningVi ?? '').isNotEmpty) main!.card!.meaningVi, shotTime(d.createdAt)].join(' · '),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary),
        ),
      ]),
    );
  }
}

// ---------------------------------------------------------------- one photo

/// The whole photo with its boxes, then every word in it: tap the speaker to hear it. Photos the learner saved words
/// from can open the AI practice dialogue. Argument: the DetectionResult.
class PhotoShotView extends StatefulWidget {
  const PhotoShotView({super.key});

  @override
  State<PhotoShotView> createState() => _PhotoShotViewState();
}

class _PhotoShotViewState extends State<PhotoShotView> {
  late final DetectionResult shot = Get.arguments as DetectionResult;
  late final List<ShotWord> words = wordsOf(shot);
  bool _talk = false;

  @override
  void initState() {
    super.initState();
    if (shot.confirmed && words.any((w) => w.saved)) {
      PhotoDialogueView.available().then((ok) {
        if (mounted) setState(() => _talk = ok);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final boxes = shot.items.where((i) => !i.dismissed && i.bbox.length == 4).toList();
    final locale = words.map((w) => w.card?.target?.ttsLocale ?? '').firstWhere((l) => l.isNotEmpty, orElse: () => '');
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: Text(shotTime(shot.createdAt)), backgroundColor: AppColors.appBarBackground),
      body: ListView(padding: EdgeInsets.only(bottom: 24.h), children: [
        // the whole photo, never cropped, so the boxes (fractions of the photo) land on their objects
        Stack(children: [
          ShotPhoto(shot, fit: BoxFit.fitWidth),
          Positioned.fill(
            child: LayoutBuilder(
              builder: (_, c) => Stack(children: [
                for (final i in boxes)
                  Positioned(
                    left: i.bbox[0] * c.maxWidth,
                    top: i.bbox[1] * c.maxHeight,
                    width: (i.bbox[2] - i.bbox[0]) * c.maxWidth,
                    height: (i.bbox[3] - i.bbox[1]) * c.maxHeight,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        border: Border.all(color: _boxColor, width: 2),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ),
              ]),
            ),
          ),
        ]),
        Padding(
          padding: EdgeInsets.fromLTRB(16.w, 16.h, 16.w, 0),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(words.isEmpty ? 'Không có đồ vật nào trong ảnh này.' : '${words.length} từ trong ảnh',
                style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary, fontWeight: FontWeight.w600)),
            SizedBox(height: 8.h),
            for (final w in words) _word(w),
            if (_talk) ...[
              SizedBox(height: 8.h),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: () => Get.toNamed(Routes.photoDialogue, arguments: {'detection': shot.id, 'locale': locale}),
                  icon: const Icon(Icons.forum_outlined),
                  label: const Text('Luyện hội thoại AI từ ảnh này'),
                ),
              ),
            ],
          ]),
        ),
      ]),
    );
  }

  Widget _word(ShotWord w) {
    final c = w.card;
    return Container(
      margin: EdgeInsets.only(bottom: 10.h),
      padding: EdgeInsets.all(12.w),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14.r),
        border: Border.all(color: w.saved ? _boxColor : AppColors.line),
      ),
      child: Row(children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (c?.target != null)
              TargetWordView(target: c!.target!, fontSize: 22, center: false)
            else
              Text(w.label, style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
            if ((c?.meaningVi ?? '').isNotEmpty)
              Text(c!.meaningVi, style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
          ]),
        ),
        if (w.count > 1) Text('×${w.count}', style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
        if (w.saved) ...[
          SizedBox(width: 8.w),
          Text('Đã lưu', style: TextStyle(fontSize: 12.sp, color: _boxColor, fontWeight: FontWeight.w700)),
        ],
      ]),
    );
  }
}
