import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:get_storage/get_storage.dart';

import '../../data/services/auth_service.dart';
import '../../data/services/offline_translator.dart';
import '../../data/services/tts_service.dart';
import '../../routes/app_pages.dart';
import '../network/api_client.dart';
import '../theme/app_colors.dart';

/// Nút dịch nổi: a round button that follows the learner on every screen (drag it anywhere), opening a quick
/// translator. Online = the server's AI translation; offline = Google ML Kit on the phone, used automatically
/// when there is no network or the server does not answer.
class TranslateBubble extends StatefulWidget {
  const TranslateBubble({super.key});

  /// The current route, fed by GetMaterialApp.routingCallback: the bubble hides where it would be in the way.
  static final route = ''.obs;

  /// Dialogs, menus and bottom sheets open now (BubblePopupObserver): the bubble would cover their buttons.
  static final popups = 0.obs;

  @override
  State<TranslateBubble> createState() => _TranslateBubbleState();
}

class _TranslateBubbleState extends State<TranslateBubble> {
  static const _key = 'translate_bubble_pos';
  static const _size = 56.0;
  static const _hidden = {
    Routes.splash, Routes.onboarding, Routes.login, Routes.register, Routes.survey, Routes.forgotPassword,
    Routes.verifyResetCode, Routes.newPassword, Routes.translate,
  };
  Offset? _pos; // from the right / bottom edges

  @override
  void initState() {
    super.initState();
    final saved = GetStorage().read<List>(_key);
    if (saved != null && saved.length == 2) _pos = Offset((saved[0] as num).toDouble(), (saved[1] as num).toDouble());
  }

  void _open() => Get.bottomSheet(const _QuickTranslateSheet(), isScrollControlled: true, backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20.r))));

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      if (!AuthService.to.isLoggedIn || _hidden.contains(TranslateBubble.route.value) || TranslateBubble.popups.value > 0) {
        return const SizedBox.shrink();
      }
      final size = MediaQuery.of(context).size;
      final pos = _pos ?? Offset(16, 96 + MediaQuery.of(context).padding.bottom); // above the tab bar
      return Positioned(
        right: pos.dx,
        bottom: pos.dy,
        child: GestureDetector(
          onTap: _open,
          onPanUpdate: (d) => setState(() {
            final p = _pos ?? pos;
            _pos = Offset((p.dx - d.delta.dx).clamp(4, size.width - _size - 4), (p.dy - d.delta.dy).clamp(4, size.height - _size - 4));
          }),
          onPanEnd: (_) => GetStorage().write(_key, [_pos!.dx, _pos!.dy]),
          child: Material(
            color: AppColors.primary,
            shape: const CircleBorder(),
            elevation: 6,
            child: const SizedBox(
              width: _size,
              height: _size,
              child: Icon(Icons.translate_rounded, color: Colors.white, size: 28),
            ),
          ),
        ),
      );
    });
  }
}

const _langs = <(String, String, String)>[
  ('vi', 'Việt', 'vi-VN'),
  ('en', 'Anh', 'en-US'),
  ('zh-Hans', 'Trung giản', 'zh-CN'),
  ('zh-Hant', 'Trung phồn', 'zh-TW'),
];
bool _zh(String l) => l.startsWith('zh');

class _QuickTranslateSheet extends StatefulWidget {
  const _QuickTranslateSheet();

  @override
  State<_QuickTranslateSheet> createState() => _QuickTranslateSheetState();
}

class _QuickTranslateSheetState extends State<_QuickTranslateSheet> {
  final _text = TextEditingController();
  late String _source, _target, _learning;
  String _mode = 'auto'; // auto | online | offline
  bool _busy = false;
  String _status = '';
  String _error = '';
  (String text, String reading, String target, bool offline)? _out;

  @override
  void initState() {
    super.initState();
    final user = AuthService.to.currentUser;
    _learning = user?.activeLanguage == 'zh' ? user!.targetCode : 'en';
    _source = user?.activeLanguage == 'vi' ? 'en' : 'vi';
    _target = user?.activeLanguage == 'vi' ? 'vi' : _learning;
  }

  @override
  void dispose() {
    _text.dispose();
    super.dispose();
  }

  Future<(String, String, String, bool)> _offline(String t) async {
    final text = await OfflineTranslator.translate(t, _source, _target,
        onDownload: () => mounted ? setState(() => _status = 'Đang tải gói dịch offline (~30 MB, chỉ lần đầu)…') : null);
    return (text, '', _target, true);
  }

  Future<void> _translate() async {
    final t = _text.text.trim();
    if (t.isEmpty || _busy) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _busy = true;
      _error = '';
      _status = '';
    });
    try {
      if (_mode == 'offline') {
        _out = await _offline(t);
      } else {
        try {
          final d = Map<String, dynamic>.from(
              await ApiClient.to.post<dynamic>('/translate/', data: {'text': t, 'source': _source, 'target': _target}) as Map);
          _out = ('${d['translation'] ?? ''}', '${d['reading'] ?? ''}', _target, false);
        } catch (e) {
          // no network / server or AI down: the phone still translates (when the target script allows it)
          if (_mode == 'online' || OfflineTranslator.unsupported(_source, _target) != null) rethrow;
          _out = await _offline(t);
        }
      }
    } on OfflineTranslateException catch (e) {
      _error = e.message;
    } catch (e) {
      _error = e is ApiException ? e.message : ApiClient.toApiException(e).message;
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
          _status = '';
        });
      }
    }
  }

  void _pick(bool isSource, String v) => setState(() {
        final other = isSource ? _target : _source;
        final fix = v == other || (_zh(v) && _zh(other)) ? (v == 'vi' ? _learning : 'vi') : other;
        if (isSource) {
          _source = v;
          _target = fix;
        } else {
          _target = v;
          _source = fix;
        }
      });

  Widget _dropdown(bool isSource) => Expanded(
        child: DropdownButtonFormField<String>(
          initialValue: isSource ? _source : _target,
          isDense: true,
          decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true),
          items: [for (final l in _langs) DropdownMenuItem(value: l.$1, child: Text(l.$2))],
          onChanged: (v) => v == null ? null : _pick(isSource, v),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final out = _out;
    return Padding(
      padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 16.h + MediaQuery.of(context).viewInsets.bottom),
      child: SafeArea(
        top: false,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Row(children: [
            Icon(Icons.translate_rounded, color: AppColors.primary),
            SizedBox(width: 8.w),
            Expanded(child: Text('Dịch nhanh', style: TextStyle(fontSize: 18.sp, fontWeight: FontWeight.w800))),
            TextButton(
              onPressed: () {
                Get.back();
                Get.toNamed(Routes.translate);
              },
              child: const Text('Trang Dịch đầy đủ'),
            ),
          ]),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'auto', label: Text('Tự động')),
              ButtonSegment(value: 'online', label: Text('Online (AI)')),
              ButtonSegment(value: 'offline', label: Text('Offline')),
            ],
            selected: {_mode},
            onSelectionChanged: (v) => setState(() => _mode = v.first),
          ),
          SizedBox(height: 10.h),
          Row(key: ValueKey('$_source-$_target'), children: [
            _dropdown(true),
            IconButton(
              icon: const Icon(Icons.swap_horiz_rounded),
              onPressed: () => setState(() {
                final s = _source;
                _source = _target;
                _target = s;
              }),
            ),
            _dropdown(false),
          ]),
          SizedBox(height: 10.h),
          TextField(
            controller: _text,
            autofocus: true,
            minLines: 2,
            maxLines: 5,
            maxLength: 500,
            textInputAction: TextInputAction.done,
            onSubmitted: (_) => _translate(),
            decoration: const InputDecoration(hintText: 'Nhập câu cần dịch', border: OutlineInputBorder()),
          ),
          Row(children: [
            Expanded(child: Text(_status, style: TextStyle(fontSize: 12.sp, color: AppColors.textSecondary))),
            FilledButton(
              onPressed: _busy ? null : _translate,
              child: _busy
                  ? SizedBox(width: 18.w, height: 18.w, child: const CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Dịch'),
            ),
          ]),
          if (_error.isNotEmpty) Text(_error, style: TextStyle(color: AppColors.error)),
          if (out != null && _error.isEmpty)
            Container(
              margin: EdgeInsets.only(top: 10.h),
              padding: EdgeInsets.all(12.w),
              decoration: BoxDecoration(color: AppColors.surfaceMuted, borderRadius: BorderRadius.circular(12.r)),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                SelectableText(out.$1, style: TextStyle(fontSize: 17.sp, color: AppColors.textPrimary)),
                if (out.$2.isNotEmpty) Text(out.$2, style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
                Row(children: [
                  IconButton(
                    icon: const Icon(Icons.volume_up_rounded),
                    onPressed: () => TtsService.to.speak(out.$1, _langs.firstWhere((l) => l.$1 == out.$3).$3),
                  ),
                  IconButton(
                    icon: const Icon(Icons.copy_rounded),
                    onPressed: () {
                      Clipboard.setData(ClipboardData(text: out.$1));
                      Get.snackbar('Đã chép', out.$1, snackPosition: SnackPosition.BOTTOM, duration: const Duration(seconds: 2));
                    },
                  ),
                  const Spacer(),
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                    decoration: BoxDecoration(color: AppColors.line, borderRadius: BorderRadius.circular(6.r)),
                    child: Text(out.$4 ? 'Dịch offline trên máy' : 'Dịch online (AI)',
                        style: TextStyle(fontSize: 11.sp, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
                  ),
                ]),
              ]),
            ),
        ]),
      ),
    );
  }
}

/// Counts the popup routes (dialogs, menus, bottom sheets) on the app's navigator for [TranslateBubble].
class BubblePopupObserver extends NavigatorObserver {
  void _add(Route<dynamic>? r, int d) {
    if (r is PopupRoute) TranslateBubble.popups.value = (TranslateBubble.popups.value + d).clamp(0, 99);
  }

  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) => _add(route, 1);

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) => _add(route, -1);

  @override
  void didRemove(Route<dynamic> route, Route<dynamic>? previousRoute) => _add(route, -1);

  @override
  void didReplace({Route<dynamic>? newRoute, Route<dynamic>? oldRoute}) {
    _add(oldRoute, -1);
    _add(newRoute, 1);
  }
}
