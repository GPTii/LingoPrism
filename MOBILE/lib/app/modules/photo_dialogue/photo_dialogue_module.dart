import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../core/network/api_client.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/target_word.dart';
import '../../data/services/tts_service.dart';

/// "Hội thoại từ ảnh" (same as the web): a short dialogue an AI model writes around the words of one photo.
/// Marked "AI tạo" – the words are verified, the sentences are not. Arguments: {detection, locale}.
class PhotoDialogueView extends StatefulWidget {
  const PhotoDialogueView({super.key});

  /// Whether the server has the AI dialogue switched on (asked once per app run).
  static Future<bool> available() async {
    try {
      final d = await ApiClient.to.get<dynamic>('/ai/status/');
      return d is Map && d['dialogue'] == true;
    } catch (_) {
      return false;
    }
  }

  @override
  State<PhotoDialogueView> createState() => _PhotoDialogueViewState();
}

class _PhotoDialogueViewState extends State<PhotoDialogueView> {
  late final int detection;
  late final String locale;
  late Future<Map<String, dynamic>> _dialogue = _load();

  @override
  void initState() {
    final args = Get.arguments as Map<String, dynamic>;
    detection = args['detection'] as int;
    locale = args['locale'] as String? ?? '';
    super.initState();
  }

  Future<Map<String, dynamic>> _load() async {
    final path = '/detections/$detection/dialogue/';
    try {
      return Map<String, dynamic>.from(await ApiClient.to.get<dynamic>(path) as Map);
    } catch (e) {
      if (ApiClient.toApiException(e).statusCode != 404) rethrow;
      return Map<String, dynamic>.from(await ApiClient.to.post<dynamic>(path) as Map); // not written yet
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(title: const Text('Hội thoại từ ảnh')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _dialogue,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const CircularProgressIndicator(),
                SizedBox(height: 12.h),
                Text('AI đang viết hội thoại…', style: TextStyle(color: AppColors.textSecondary)),
              ]),
            );
          }
          if (snap.hasError) {
            return Center(
              child: Padding(
                padding: EdgeInsets.all(24.w),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(ApiClient.toApiException(snap.error!).message, textAlign: TextAlign.center,
                      style: TextStyle(color: AppColors.textPrimary)),
                  SizedBox(height: 12.h),
                  OutlinedButton(onPressed: () => setState(() => _dialogue = _load()), child: const Text('Thử lại')),
                ]),
              ),
            );
          }
          final d = snap.data!;
          final language = d['language'] as String? ?? '';
          final lines = (d['lines'] as List? ?? const []).cast<Map>();
          final words = (d['words'] as List? ?? const []).cast<Map>().map((w) => w['text']).join(', ');
          return ListView(
            padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 32.h),
            children: [
              Row(children: [
                Expanded(
                  child: Text(d['title_vi'] as String? ?? 'Hội thoại',
                      style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                  decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(6.r),
                      border: Border.all(color: AppColors.line)),
                  child: Text('AI tạo', style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w700, color: AppColors.textSecondary)),
                ),
              ]),
              SizedBox(height: 14.h),
              for (final l in lines) _line(l, language),
              SizedBox(height: 8.h),
              Text('Câu do AI viết, chưa được kiểm duyệt như từ vựng. Từ trong ảnh: $words.',
                  style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary)),
            ],
          );
        },
      ),
    );
  }

  Widget _line(Map l, String language) {
    final a = l['speaker'] == 'A';
    final text = l['text'] as String? ?? '';
    final reading = l['reading'] as String? ?? '';
    return Padding(
      padding: EdgeInsets.only(bottom: 12.h),
      child: InkWell(
        borderRadius: BorderRadius.circular(12.r),
        onTap: () {
          if (locale.isNotEmpty && Get.isRegistered<TtsService>()) TtsService.to.speak(text, locale);
        },
        child: Container(
          padding: EdgeInsets.all(12.w),
          decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(12.r),
              border: Border.all(color: AppColors.line)),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            CircleAvatar(
              radius: 13.r,
              backgroundColor: a ? AppColors.primary.withValues(alpha: 0.14) : AppColors.background,
              child: Text(l['speaker'] as String? ?? '', style: TextStyle(fontSize: 12.sp, fontWeight: FontWeight.w800, color: a ? AppColors.primary : AppColors.textSecondary)),
            ),
            SizedBox(width: 10.w),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                LangText(text, language: language,
                    style: TextStyle(fontSize: 17.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                if (reading.isNotEmpty) Text(reading, style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
                SizedBox(height: 2.h),
                Text(l['translation'] as String? ?? '', style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
              ]),
            ),
            Icon(Icons.volume_up_rounded, color: AppColors.primary, size: 20.sp),
          ]),
        ),
      ),
    );
  }
}
