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

/// Detected objects → vocabulary in the language being learned. The learner picks the words to save,
/// marks wrong detections (feedback feeds the VIP algorithm) and can share the photo to the community.
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

  @override
  void initState() {
    super.initState();
    final args = Get.arguments as Map<String, dynamic>;
    result = args['result'] as DetectionResult;
    image = args['image'] as File?;
    for (final it in result.items) {
      it.selected = it.card != null && it.card!.personal == null && it.confidence >= 0.4;
    }
    VocabRepository.topics().then((t) => mounted ? setState(() => topics = t) : null).catchError((_) => null);
  }

  // one entry per distinct word, best confidence first
  List<DetectedItem> get _items {
    final seen = <String>{};
    return result.items.where((i) => seen.add(i.label)).toList();
  }

  Future<void> _save({bool share = false}) async {
    final chosen = _items.where((i) => i.selected && i.card != null && i.feedback != 'wrong').toList();
    if (chosen.isEmpty && !share) {
      Get.snackbar('Chưa chọn từ', 'Hãy chọn ít nhất một từ để lưu.', snackPosition: SnackPosition.BOTTOM);
      return;
    }
    setState(() => saving = true);
    try {
      final saved = await DetectionRepository.confirm(result.id, result.items, topic: topic?.id);
      if (share && image != null) {
        final caption = chosen.map((i) => i.card!.text).join(' · ');
        await CommunityRepository.createPost(image!.path, caption, chosen.map((i) => i.card!.id).toList(),
            topicLabel: topic?.nameVi ?? '');
      }
      GameService.to.refreshAll();
      Get.back();
      Get.snackbar('Thành công', share ? 'Đã lưu $saved từ và chia sẻ lên cộng đồng' : 'Đã lưu $saved từ vào thư viện',
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
                    border: Border.all(color: it.feedback == 'wrong' ? Colors.red : AppColors.primaryGreen, width: 2),
                    borderRadius: BorderRadius.circular(6.r),
                  ),
                  alignment: Alignment.topLeft,
                  child: Container(
                    color: Colors.black54,
                    padding: EdgeInsets.symmetric(horizontal: 4.w, vertical: 1.h),
                    child: Text('${it.card?.text ?? it.label} ${(it.confidence * 100).round()}%',
                        style: TextStyle(color: Colors.white, fontSize: 10.sp), locale: localeFor(it.card?.target?.language ?? 'en')),
                  ),
                ),
              ),
        ]),
      );
    });
  }

  Widget _itemTile(DetectedItem it) {
    final card = it.card;
    final target = card?.target;
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
            onChanged: card == null || it.feedback == 'wrong' ? null : (v) => setState(() => it.selected = v ?? false),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (target != null)
                  TargetWordView(target: target, fontSize: 22, center: false)
                else
                  Text(it.label, style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w600)),
                SizedBox(height: 4.h),
                Text(card?.meaningVi.isNotEmpty == true ? card!.meaningVi : 'Chưa có trong bộ từ vựng đã kiểm tra',
                    style: TextStyle(fontSize: 15.sp, color: card == null ? AppColors.textHint : AppColors.textPrimary)),
                SizedBox(height: 4.h),
                Text('Độ tin cậy ${(it.confidence * 100).round()}%'
                    '${card?.personal != null ? ' · đã có trong thư viện (${card!.personal!.statusLabel})' : ''}',
                    style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
              ],
            ),
          ),
          Column(children: [
            IconButton(
              tooltip: 'Nhận diện đúng',
              icon: Icon(Icons.thumb_up_alt_rounded, color: it.feedback == 'correct' ? AppColors.buttonSuccess : AppColors.textHint),
              onPressed: () => setState(() => it.feedback = it.feedback == 'correct' ? 'unknown' : 'correct'),
            ),
            IconButton(
              tooltip: 'Nhận diện sai',
              icon: Icon(Icons.thumb_down_alt_rounded, color: it.feedback == 'wrong' ? Colors.red : AppColors.textHint),
              onPressed: () => setState(() {
                it.feedback = it.feedback == 'wrong' ? 'unknown' : 'wrong';
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
            if (!isKid) ...[
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
