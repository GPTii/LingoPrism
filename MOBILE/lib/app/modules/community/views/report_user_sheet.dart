import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../../../core/network/api_client.dart';
import '../../../core/theme/app_colors.dart';
import '../../../data/repositories/repositories.dart';
import 'package:lingoprism/app/core/navigation/back.dart';

const _reasons = {
  'harassment': 'Quấy rối, đe doạ, xúc phạm',
  'spam': 'Spam, lừa đảo, xin tiền',
  'inappropriate': 'Nội dung không phù hợp',
  'impersonation': 'Giả mạo người khác',
  'other': 'Khác',
};

/// "Báo cáo" a learner to the moderators. From a conversation ([threadId]) the server keeps its last messages as
/// evidence; "chặn luôn" also blocks them at once. Returns true when the report was sent.
Future<bool> showReportUserSheet({required int userId, required String name, int? threadId, bool blocked = false}) async {
  final sent = await Get.bottomSheet<bool>(
    _ReportUserSheet(userId: userId, name: name, threadId: threadId, blocked: blocked),
    isScrollControlled: true,
    backgroundColor: AppColors.surface,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20.r))),
  );
  return sent == true;
}

class _ReportUserSheet extends StatefulWidget {
  const _ReportUserSheet({required this.userId, required this.name, this.threadId, this.blocked = false});

  final int userId;
  final String name;
  final int? threadId;
  final bool blocked;

  @override
  State<_ReportUserSheet> createState() => _ReportUserSheetState();
}

class _ReportUserSheetState extends State<_ReportUserSheet> {
  String _reason = 'harassment';
  late bool _block = !widget.blocked;
  bool _busy = false;
  final _details = TextEditingController();

  @override
  void dispose() {
    _details.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _busy = true);
    try {
      final block = _block && !widget.blocked;
      await CommunityRepository.reportUser(widget.userId,
          reason: _reason, details: _details.text.trim(), block: block, thread: widget.threadId);
      goBack(result: true);
      Get.snackbar('Đã gửi báo cáo',
          block ? 'Đã chặn ${widget.name}. Đội ngũ kiểm duyệt sẽ xem xét sớm nhất.' : 'Đội ngũ kiểm duyệt sẽ xem xét sớm nhất.',
          snackPosition: SnackPosition.BOTTOM);
    } catch (e) {
      if (mounted) setState(() => _busy = false);
      Get.snackbar('Lỗi', ApiClient.toApiException(e).message, snackPosition: SnackPosition.BOTTOM);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(20.w, 16.h, 20.w, 16.h + MediaQuery.of(context).viewInsets.bottom),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
            Text('Báo cáo ${widget.name}',
                style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
            SizedBox(height: 6.h),
            Text(
              widget.threadId != null
                  ? 'Đội ngũ kiểm duyệt sẽ xem các tin nhắn gần đây trong cuộc trò chuyện này. Người kia không biết ai đã báo cáo.'
                  : 'Người kia không biết ai đã báo cáo.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13.sp),
            ),
            RadioGroup<String>(
              groupValue: _reason,
              onChanged: (v) => setState(() => _reason = v ?? _reason),
              child: Column(children: [
                for (final e in _reasons.entries)
                  RadioListTile<String>(value: e.key, title: Text(e.value), dense: true, contentPadding: EdgeInsets.zero),
              ]),
            ),
            TextField(
              controller: _details,
              maxLength: 500,
              maxLines: 3,
              decoration: InputDecoration(
                hintText: _reason == 'other' ? 'Mô tả chuyện gì đã xảy ra (bắt buộc)' : 'Thêm chi tiết (không bắt buộc)',
                border: const OutlineInputBorder(),
              ),
            ),
            if (!widget.blocked)
              CheckboxListTile(
                value: _block,
                onChanged: (v) => setState(() => _block = v ?? false),
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
                title: Text('Chặn ${widget.name} luôn', style: const TextStyle(fontWeight: FontWeight.w600)),
                subtitle: const Text('Hai bạn không nhắn tin và không thấy bài của nhau nữa'),
              ),
            SizedBox(height: 8.h),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: _busy ? null : _submit,
                style: FilledButton.styleFrom(backgroundColor: Colors.red.shade600),
                child: Text(_busy ? 'Đang gửi…' : 'Gửi báo cáo'),
              ),
            ),
          ]),
        ),
      ),
    );
  }
}
