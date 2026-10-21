import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/target_word.dart';
import '../../../data/models/api/learning_extra.dart';
import '../../../data/models/api/vocab.dart';
import '../../../data/repositories/repositories.dart';
import '../../../data/services/auth_service.dart';
import '../../../data/services/game_service.dart';
import '../../../data/services/offline_detections.dart';

/// Detected objects → vocabulary in the language being learned. The learner picks the words to save,
/// marks wrong detections (feedback feeds the VIP algorithm) and can share the photo to the community.
/// When the model is unsure (or marked wrong) the learner is asked "Có phải: A / B / C?" and learns the picked word.
class DetectionResultView extends StatefulWidget {
  const DetectionResultView({super.key});

  @override
  State<DetectionResultView> createState() => _DetectionResultViewState();
}

class _DetectionResultViewState extends State<DetectionResultView> {
  late final DetectionResult result;
  late final File? image;
  List<Topic> topics = [];
  Topic? topic;
  bool saving = false;
  List<DetectionAlternative>? allLabels; // loaded when the learner opens "Vật khác…"
  List<Map<String, dynamic>>? offlineItems; // phone boxes of a result made without network (sent later)

  bool get offline => offlineItems != null;

  @override
  void initState() {
    super.initState();
    final args = Get.arguments as Map<String, dynamic>;
    result = args['result'] as DetectionResult;
    image = args['image'] as File?;
    offlineItems = args['offline_items'] as List<Map<String, dynamic>>?;
    for (final it in result.items) {
      // an unsure object is only selected once the learner says which one it is
      it.selected = it.card != null && it.card!.personal == null && it.confidence >= 0.4 && !it.uncertain;
    }
    VocabRepository.topics().then((t) => mounted ? setState(() => topics = t) : null).catchError((_) => null);
  }

  // one entry per distinct word, best confidence first
  List<DetectedItem> get _items {
    final seen = <String>{};
    return result.items.where((i) => seen.add(i.label)).toList();
  }

  void _pick(DetectedItem it, String label, {WordCard? card}) => setState(() {
        it.notObject = false;
        it.pickedCard = card;
        if (label == it.label) {
          it.picked = null;
          it.feedback = 'correct';
        } else {
          it.picked = label;
          it.feedback = 'wrong';
        }
        it.selected = it.shownCard != null && it.shownCard!.personal == null;
      });

  // error report: nothing of the kind in the photo – the server remembers it and stops showing this box
  void _notObject(DetectedItem it) => setState(() {
        it.picked = null;
        it.pickedCard = null;
        it.notObject = true;
        it.feedback = 'wrong';
        it.selected = false;
      });

  /// "Vật khác…": every object the detector knows, searchable by the word or its Vietnamese meaning.
  Future<void> _pickOther(DetectedItem it) async {
    try {
      allLabels ??= offline ? OfflineDetections.cachedLabels() : await DetectionRepository.labels();
    } catch (e) {
      final cached = OfflineDetections.cachedLabels();
      if (cached.isEmpty) {
        Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
        return;
      }
      allLabels = cached;
    }
    if (!mounted) return;
    var query = '';
    final chosen = await showModalBottomSheet<DetectionAlternative>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(builder: (ctx, setSheet) {
        final q = query.toLowerCase();
        final options = allLabels!
            .where((o) => q.isEmpty ||
                o.label.toLowerCase().contains(q) ||
                o.card.text.toLowerCase().contains(q) ||
                o.card.meaningVi.toLowerCase().contains(q))
            .toList();
        return SizedBox(
          height: MediaQuery.of(ctx).size.height * 0.75,
          child: Column(children: [
            Padding(
              padding: EdgeInsets.all(16.w),
              child: TextField(
                autofocus: true,
                decoration: InputDecoration(
                  hintText: 'Tìm vật trong ảnh (VD: con lợn, cái gối)',
                  prefixIcon: const Icon(Icons.search),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12.r)),
                ),
                onChanged: (v) => setSheet(() => query = v),
              ),
            ),
            Expanded(
              child: ListView(children: [
                for (final o in options)
                  ListTile(
                    title: Text(o.card.target?.text ?? o.label, locale: localeFor(o.card.target?.language ?? 'en')),
                    subtitle: o.card.meaningVi.isNotEmpty ? Text(o.card.meaningVi) : null,
                    onTap: () => Navigator.pop(ctx, o),
                  ),
              ]),
            ),
          ]),
        );
      }),
    );
    if (chosen != null) _pick(it, chosen.label, card: chosen.card);
  }

  Future<void> _save({bool share = false}) async {
    final chosen = _items.where((i) => i.selected && i.shownCard != null && (i.feedback != 'wrong' || i.picked != null)).toList();
    final reports = _items.any((i) => i.notObject || i.picked != null);
    if (chosen.isEmpty && !share && !reports) {
      Get.snackbar('Chưa chọn từ', 'Hãy chọn ít nhất một từ để lưu.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    if (offline) {
      await OfflineDetections.queue(result, offlineItems!, topic: topic?.id);
      Get.back();
      Get.snackbar('Đã lưu tạm', 'Đang offline: ${chosen.length} từ sẽ được lưu vào thư viện khi có mạng.',
          snackPosition: SnackPosition.BOTTOM, backgroundColor: AppColors.buttonSuccess, colorText: Colors.white);
      return;
    }
    setState(() => saving = true);
    try {
      final (saved, reported) = await DetectionRepository.confirm(result.id, result.items, topic: topic?.id);
      if (share && image != null) {
        final caption = chosen.map((i) => i.shownCard!.text).join(' · ');
        await CommunityRepository.createPost(image!.path, caption, chosen.map((i) => i.shownCard!.id).toList(),
            topicLabel: topic?.nameVi ?? '');
      }
      GameService.to.refreshAll();
      Get.back();
      Get.snackbar(
          'Thành công',
          '${share ? 'Đã lưu $saved từ và chia sẻ lên cộng đồng' : 'Đã lưu $saved từ vào thư viện'}'
              '${reported > 0 ? '\nCảm ơn bạn đã báo lỗi! Lần sau gặp vật tương tự, hệ thống sẽ nhận đúng.' : ''}',
          snackPosition: SnackPosition.BOTTOM, backgroundColor: AppColors.buttonSuccess, colorText: Colors.white);
    } catch (e) {
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Widget _image() {
    return LayoutBuilder(builder: (context, c) {
      final side = c.maxWidth;
      return SizedBox(
        width: side,
        height: side,
        child: Stack(children: [
          Positioned.fill(
            child: image != null
                ? Image.file(image!, fit: BoxFit.fill)
                : (result.image != null ? Image.network(result.image!, fit: BoxFit.fill) : const SizedBox()),
          ),
          for (final it in _items)
            if (it.bbox.length == 4)
              Positioned(
                left: it.bbox[0] * side,
                top: it.bbox[1] * side,
                width: (it.bbox[2] - it.bbox[0]) * side,
                height: (it.bbox[3] - it.bbox[1]) * side,
                child: Container(
                  decoration: BoxDecoration(
                    border: Border.all(
                        color: it.notObject || (it.feedback == 'wrong' && it.picked == null)
                            ? Colors.red
                            : (it.uncertain && it.picked == null && it.feedback == 'unknown' ? Colors.amber : AppColors.primaryGreen),
                        width: 2),
                    borderRadius: BorderRadius.circular(6.r),
                  ),
                  alignment: Alignment.topLeft,
                  child: Container(
                    color: Colors.black54,
                    padding: EdgeInsets.symmetric(horizontal: 4.w, vertical: 1.h),
                    child: Text(
                        it.picked != null
                            ? (it.shownCard?.text ?? it.picked!)
                            : '${it.card?.text ?? it.label} ${(it.confidence * 100).round()}%${it.uncertain && it.feedback == 'unknown' ? ' ?' : ''}',
                        style: TextStyle(color: Colors.white, fontSize: 10.sp),
                        locale: localeFor(it.shownCard?.target?.language ?? 'en')),
                  ),
                ),
              ),
        ]),
      );
    });
  }

  Widget _choices(DetectedItem it) {
    final options = [
      if (it.card != null) DetectionAlternative(label: it.label, confidence: it.confidence, card: it.card!),
      ...it.alternatives,
    ];
    final chosen = it.picked ?? (it.feedback == 'correct' ? it.label : null);
    return Padding(
      padding: EdgeInsets.only(top: 8.h),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(it.feedback == 'wrong' && it.picked == null ? 'Vậy đây là gì?' : 'Chưa chắc lắm – có phải là:',
            style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
        SizedBox(height: 4.h),
        Wrap(spacing: 6.w, runSpacing: 4.h, children: [
          for (final o in options)
            ChoiceChip(
              selected: chosen == o.label,
              onSelected: (_) => _pick(it, o.label),
              label: Text(
                  '${o.card.target?.text ?? o.card.text}${o.card.meaningVi.isNotEmpty ? ' (${o.card.meaningVi})' : ''}',
                  locale: localeFor(o.card.target?.language ?? 'en')),
            ),
          if (it.picked != null && !options.any((o) => o.label == it.picked))
            ChoiceChip(selected: true, onSelected: (_) {}, label: Text(it.shownCard?.target?.text ?? it.picked!)),
          ActionChip(avatar: const Icon(Icons.search, size: 18), label: const Text('Vật khác…'), onPressed: () => _pickOther(it)),
          ChoiceChip(
            selected: it.notObject,
            selectedColor: Colors.red.shade100,
            onSelected: (_) => _notObject(it),
            label: const Text('Không phải đồ vật'),
          ),
        ]),
      ]),
    );
  }

  Widget _itemTile(DetectedItem it) {
    final card = it.shownCard;
    final target = card?.target;
    final asking = it.uncertain || it.feedback == 'wrong';
    return Container(
      margin: EdgeInsets.only(bottom: 12.h),
      padding: EdgeInsets.all(12.w),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16.r),
          boxShadow: const [BoxShadow(color: AppColors.shadowLight, blurRadius: 8, offset: Offset(0, 2))]),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Checkbox(
            value: it.selected,
            onChanged: card == null || (it.feedback == 'wrong' && it.picked == null)
                ? null
                : (v) => setState(() => it.selected = v ?? false),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (target != null)
                  TargetWordView(target: target, fontSize: 22, center: false)
                else
                  Text(it.picked ?? it.label, style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w600)),
                SizedBox(height: 4.h),
                Text(card?.meaningVi.isNotEmpty == true ? card!.meaningVi : 'Chưa có trong bộ từ vựng đã kiểm tra',
                    style: TextStyle(fontSize: 15.sp, color: card == null ? AppColors.textHint : AppColors.textPrimary)),
                SizedBox(height: 4.h),
                if (it.learned && it.picked == null)
                  Padding(
                    padding: EdgeInsets.only(bottom: 4.h),
                    child: Text('✓ Đã học từ báo lỗi của người dùng',
                        style: TextStyle(fontSize: 12.sp, color: Colors.purple, fontWeight: FontWeight.w600)),
                  ),
                Text('${it.picked != null ? 'Bạn đã chọn' : it.notObject ? 'Đã báo: không phải đồ vật' : 'Độ tin cậy ${(it.confidence * 100).round()}%'}'
                    '${card?.personal != null ? ' · đã có trong thư viện (${card!.personal!.statusLabel})' : ''}',
                    style: TextStyle(fontSize: 12.sp, color: it.uncertain && it.picked == null ? Colors.orange : AppColors.textSecondary)),
                if (asking) _choices(it),
              ],
            ),
          ),
          Column(children: [
            IconButton(
              tooltip: 'Nhận diện đúng',
              icon: Icon(Icons.thumb_up_alt_rounded, color: it.feedback == 'correct' ? AppColors.buttonSuccess : AppColors.textHint),
              onPressed: () => it.feedback == 'correct' ? setState(() => it.feedback = 'unknown') : _pick(it, it.label),
            ),
            IconButton(
              tooltip: 'Nhận diện sai',
              icon: Icon(Icons.thumb_down_alt_rounded, color: it.feedback == 'wrong' ? Colors.red : AppColors.textHint),
              onPressed: () => setState(() {
                it.feedback = it.feedback == 'wrong' ? 'unknown' : 'wrong';
                it.picked = null;
                it.pickedCard = null;
                it.notObject = false;
                if (it.feedback == 'wrong') it.selected = false;
              }),
            ),
          ]),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isKid = AuthService.to.currentUser?.isKid == true;
    return Scaffold(
      backgroundColor: AppColors.backgroundLight,
      appBar: AppBar(
        backgroundColor: AppColors.backgroundLight,
        elevation: 0,
        title: Text('Kết quả nhận diện', style: TextStyle(fontSize: 20.sp, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
        iconTheme: const IconThemeData(color: AppColors.textPrimary),
      ),
      body: ListView(
        padding: EdgeInsets.all(16.w),
        children: [
          ClipRRect(borderRadius: BorderRadius.circular(16.r), child: _image()),
          SizedBox(height: 8.h),
          Text(
            '${result.device == 'server' ? 'Nhận diện trên máy chủ' : 'Nhận diện trên điện thoại'} · ${result.model}'
            '${result.inferenceMs != null ? ' · ${result.inferenceMs} ms' : ''}',
            style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary),
          ),
          if (offline)
            Container(
              margin: EdgeInsets.only(top: 8.h),
              padding: EdgeInsets.all(10.w),
              decoration: BoxDecoration(color: Colors.orange.shade50, borderRadius: BorderRadius.circular(12.r)),
              child: Text('Đang offline: nhận diện bằng mô hình trên điện thoại. Từ bạn lưu và lỗi bạn báo '
                  'sẽ được gửi lên máy chủ khi có mạng.',
                  style: TextStyle(fontSize: 13.sp, color: Colors.orange.shade900)),
            ),
          SizedBox(height: 16.h),
          Text('Chọn từ muốn lưu', style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.bold)),
          SizedBox(height: 8.h),
          ..._items.map(_itemTile),
          SizedBox(height: 8.h),
          DropdownButtonFormField<Topic?>(
            value: topic,
            decoration: InputDecoration(
              labelText: 'Chọn chủ đề cho tất cả từ (không bắt buộc)',
              filled: true,
              fillColor: Colors.white,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12.r)),
            ),
            items: [
              const DropdownMenuItem<Topic?>(value: null, child: Text('Không chọn')),
              for (final t in topics) DropdownMenuItem<Topic?>(value: t, child: Text('${t.icon} ${t.nameVi}')),
            ],
            onChanged: (t) => setState(() => topic = t),
          ),
          SizedBox(height: 24.h),
          Row(children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: saving ? null : () => _save(),
                icon: const Icon(Icons.bookmark_add_rounded),
                label: const Text('Lưu lại'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.buttonActive, foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(vertical: 14.h),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14.r)),
                ),
              ),
            ),
            if (!isKid && !offline) ...[
              SizedBox(width: 12.w),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: saving ? null : () => _save(share: true),
                  icon: const Icon(Icons.share_rounded),
                  label: const Text('Lưu & chia sẻ'),
                  style: OutlinedButton.styleFrom(
                    padding: EdgeInsets.symmetric(vertical: 14.h),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14.r)),
                  ),
                ),
              ),
            ],
          ]),
          if (saving) Padding(padding: EdgeInsets.only(top: 16.h), child: const Center(child: CircularProgressIndicator())),
        ],
      ),
    );
  }
}
