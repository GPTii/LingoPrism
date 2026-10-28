import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:get_storage/get_storage.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/navigation/back.dart';
import '../../core/network/api_client.dart';
import '../../core/network/api_config.dart';
import '../../core/theme/app_colors.dart';
import '../../data/repositories/repositories.dart';
import '../../data/services/auth_service.dart';
import '../../routes/app_pages.dart';

/// The public site (Privacy policy, Terms, deleting an account, release notes): the server the app talks to when it
/// is a real one, otherwise the live site.
String get siteUrl => ApiConfig.baseUrl.startsWith('https://') ? ApiConfig.baseUrl : 'https://lingoprism.id.vn';

Future<void> openSite(String path) => launchUrl(Uri.parse('$siteUrl$path'), mode: LaunchMode.externalApplication);

TextSpan _link(String text, String path) => TextSpan(
      text: text,
      style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.w700),
      recognizer: TapGestureRecognizer()..onTap = () => openSite(path),
    );

/// Sign-up: "I have read and accept the Terms and the Privacy policy" (links open the site).
class TermsCheckbox extends StatelessWidget {
  const TermsCheckbox({super.key, required this.accepted, this.error = false});

  final RxBool accepted;
  final bool error;

  @override
  Widget build(BuildContext context) {
    return Obx(() => Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Checkbox(value: accepted.value, onChanged: (v) => accepted.value = v ?? false,
                side: BorderSide(color: error && !accepted.value ? AppColors.error : AppColors.lineStrong, width: 1.5)),
            Expanded(
              child: Padding(
                padding: EdgeInsets.only(top: 12.h),
                child: Text.rich(TextSpan(
                  style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary, height: 1.4),
                  children: [
                    const TextSpan(text: 'Tôi đã đọc và đồng ý '),
                    _link('Điều khoản sử dụng', '/terms'),
                    const TextSpan(text: ' và '),
                    _link('Chính sách quyền riêng tư', '/privacy'),
                  ],
                )),
              ),
            ),
          ],
        ));
  }
}

/// Under the Google button: signing up with Google accepts the Terms too (the server records it).
class GoogleTermsNote extends StatelessWidget {
  const GoogleTermsNote({super.key});

  @override
  Widget build(BuildContext context) {
    return Text.rich(
      TextSpan(
        style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary, height: 1.4),
        children: [
          const TextSpan(text: 'Tiếp tục với Google nghĩa là bạn đồng ý '),
          _link('Điều khoản', '/terms'),
          const TextSpan(text: ' và '),
          _link('Chính sách quyền riêng tư', '/privacy'),
          const TextSpan(text: '.'),
        ],
      ),
      textAlign: TextAlign.center,
    );
  }
}

void _snack(String title, String text, {bool error = false}) => Get.snackbar(title, text,
    snackPosition: SnackPosition.BOTTOM, backgroundColor: error ? AppColors.error : AppColors.success, colorText: Colors.white);

/// Above the home tabs until the e-mail is verified: type the mailed code, or get a new one.
class VerifyEmailBanner extends StatefulWidget {
  const VerifyEmailBanner({super.key});

  @override
  State<VerifyEmailBanner> createState() => _VerifyEmailBannerState();
}

class _VerifyEmailBannerState extends State<VerifyEmailBanner> {
  final _code = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _code.dispose();
    super.dispose();
  }

  Future<void> _verify() async {
    setState(() => _busy = true);
    try {
      await AuthService.to.applyUser(await AuthRepository.verifyEmail(_code.text.trim()));
      _snack('Đã xác minh', 'Giờ bạn dùng được đầy đủ Cộng đồng.');
    } catch (e) {
      _snack('Lỗi', ApiClient.toApiException(e).message, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _resend() async {
    try {
      _snack('Đã gửi', await AuthRepository.resendEmailCode());
    } catch (e) {
      _snack('Lỗi', ApiClient.toApiException(e).message, error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final user = AuthService.to.user.value;
      if (user == null || user.emailVerified) return const SizedBox.shrink();
      return SafeArea(
        bottom: false,
        child: Container(
          margin: EdgeInsets.fromLTRB(16.w, 8.h, 16.w, 0),
          padding: EdgeInsets.all(14.w),
          decoration: BoxDecoration(
            color: AppColors.beamAmber.withValues(alpha: 0.12),
            border: Border.all(color: AppColors.beamAmber.withValues(alpha: 0.6)),
            borderRadius: BorderRadius.circular(16.r),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Xác minh email của bạn', style: TextStyle(fontSize: 15.sp, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
              SizedBox(height: 4.h),
              Text('Nhập mã 6 số đã gửi tới ${user.email}. Đăng bài, kết bạn và nhắn tin cần bước này.',
                  style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
              SizedBox(height: 10.h),
              Row(children: [
                Expanded(
                  child: TextField(
                    controller: _code,
                    keyboardType: TextInputType.number,
                    maxLength: 6,
                    decoration: const InputDecoration(hintText: 'Mã 6 số', counterText: '', isDense: true),
                    onSubmitted: (_) => _verify(),
                  ),
                ),
                SizedBox(width: 8.w),
                FilledButton(onPressed: _busy ? null : _verify, child: const Text('Xác minh')),
                TextButton(onPressed: _resend, child: const Text('Gửi lại')),
              ]),
            ],
          ),
        ),
      );
    });
  }
}

/// Settings: delete the account for good (password, or the word XOA for a Google-only account).
Future<void> confirmDeleteAccount() async {
  final user = AuthService.to.user.value;
  if (user == null) return;
  final field = TextEditingController();
  final ok = await Get.dialog<bool>(AlertDialog(
    title: const Text('Xoá vĩnh viễn tài khoản?'),
    content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Tiến độ học, từ đã lưu, ảnh, bài đăng, tin nhắn và bạn bè của ${user.email} sẽ bị xoá ngay và không khôi phục được.'),
      SizedBox(height: 12.h),
      TextField(
        controller: field,
        obscureText: user.hasPassword,
        autofocus: true,
        decoration: InputDecoration(hintText: user.hasPassword ? 'Nhập mật khẩu để xác nhận' : 'Gõ XOA để xác nhận'),
      ),
    ]),
    actions: [
      TextButton(onPressed: () => goBack(result: false), child: const Text('Huỷ')),
      TextButton(onPressed: () => goBack(result: true), style: TextButton.styleFrom(foregroundColor: AppColors.error),
          child: const Text('Xoá vĩnh viễn')),
    ],
  ));
  if (ok != true || field.text.isEmpty) return;
  try {
    await AuthRepository.deleteAccount(password: user.hasPassword ? field.text : null, confirm: user.hasPassword ? null : field.text);
    await AuthService.to.logout(remote: false);
    Get.offAllNamed(Routes.login);
    _snack('Đã xoá tài khoản', 'Cảm ơn bạn đã học cùng LingoPrism!');
  } catch (e) {
    _snack('Không xoá được', ApiClient.toApiException(e).message, error: true);
  }
}

/// "Có gì mới": once after each update; someone opening the app for the first time is not shown the history.
class WhatsNew {
  static const _seenKey = 'release.seen';

  static Future<void> maybeShow() async {
    try {
      final latest = (await AuthRepository.releases()).first;
      final box = GetStorage();
      final seen = box.read<String>(_seenKey);
      await box.write(_seenKey, latest['version']);
      if (seen == null || seen == latest['version']) return;
      List<String> lines(String key) => (latest[key] as List? ?? const []).map((e) => e.toString()).toList();
      final sections = [('Mới', lines('new')), ('Cải thiện', lines('improved')), ('Sửa lỗi', lines('fixed'))];
      await Get.dialog(AlertDialog(
        title: Text('Có gì mới · ${latest['version']}'),
        content: SingleChildScrollView(
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('${latest['title']}', style: const TextStyle(fontWeight: FontWeight.w700)),
            for (final (title, items) in sections)
              if (items.isNotEmpty) ...[
                SizedBox(height: 10.h),
                Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
                for (final line in items) Padding(padding: EdgeInsets.only(top: 4.h), child: Text('• $line')),
              ],
          ]),
        ),
        actions: [
          TextButton(onPressed: () => openSite('/releases'), child: const Text('Mọi phiên bản')),
          FilledButton(onPressed: Get.back, child: const Text('Tuyệt!')),
        ],
      ));
    } catch (_) {
      // offline or an older server: nothing to show
    }
  }
}
