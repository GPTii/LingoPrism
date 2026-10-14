import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../data/models/api/vocab.dart';
import '../../data/services/auth_service.dart';
import '../../data/services/tts_service.dart';
import '../theme/app_colors.dart';

/// Locale for a translation so CJK text renders with the right glyph forms (Han unification):
/// simplified → zh-Hans-CN, traditional → zh-Hant-TW.
Locale? localeFor(String language) {
  switch (language) {
    case 'zh-Hans':
      return const Locale.fromSubtags(languageCode: 'zh', scriptCode: 'Hans', countryCode: 'CN');
    case 'zh-Hant':
      return const Locale.fromSubtags(languageCode: 'zh', scriptCode: 'Hant', countryCode: 'TW');
    case 'vi':
      return const Locale('vi', 'VN');
    case 'en':
      return const Locale('en', 'US');
  }
  return null;
}

/// Text in a given language with the correct locale.
class LangText extends StatelessWidget {
  const LangText(this.text, {super.key, required this.language, this.style, this.textAlign, this.maxLines});

  final String text;
  final String language;
  final TextStyle? style;
  final TextAlign? textAlign;
  final int? maxLines;

  @override
  Widget build(BuildContext context) =>
      Text(text, locale: localeFor(language), style: style, textAlign: textAlign, maxLines: maxLines, overflow: maxLines != null ? TextOverflow.ellipsis : null);
}

/// Word + reading (IPA / pinyin / zhuyin) + measure word + speaker button.
class TargetWordView extends StatelessWidget {
  const TargetWordView({super.key, required this.target, this.fontSize = 28, this.showReading = true, this.center = true});

  final TargetText target;
  final double fontSize;
  final bool showReading;
  final bool center;

  @override
  Widget build(BuildContext context) {
    final showZhuyin = AuthService.to.currentUser?.showZhuyin == true;
    final reading = <String>[
      if (target.ipa.isNotEmpty) '/${target.ipa}/',
      if (target.isChinese && target.pinyin.isNotEmpty) target.pinyin,
    ];
    return Column(
      crossAxisAlignment: center ? CrossAxisAlignment.center : CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Flexible(
              child: LangText(target.text,
                  language: target.language,
                  style: TextStyle(fontSize: fontSize.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
            ),
            SizedBox(width: 6.w),
            InkWell(
              onTap: () => TtsService.to.speak(target.text, target.ttsLocale),
              borderRadius: BorderRadius.circular(20.r),
              child: Padding(
                padding: EdgeInsets.all(4.w),
                child: Icon(Icons.volume_up_rounded, color: AppColors.buttonActive, size: (fontSize * 0.8).sp),
              ),
            ),
          ],
        ),
        if (showReading && reading.isNotEmpty)
          Text(reading.join('  '), style: TextStyle(fontSize: 14.sp, color: AppColors.textSecondary)),
        if (showReading && target.isTraditional && showZhuyin && target.zhuyin.isNotEmpty)
          LangText(target.zhuyin, language: 'zh-Hant', style: TextStyle(fontSize: 13.sp, color: AppColors.textSecondary)),
        if (showReading && target.isChinese && target.measureWord.isNotEmpty)
          Row(mainAxisSize: MainAxisSize.min, children: [
            Text('Lượng từ: ', style: TextStyle(fontSize: 12.sp, color: AppColors.textHint)),
            LangText(target.measureWord, language: target.language, style: TextStyle(fontSize: 12.sp, color: AppColors.textHint)),
          ]),
        if (target.unverified)
          Text('Chưa được kiểm tra', style: TextStyle(fontSize: 11.sp, color: Colors.orange)),
      ],
    );
  }
}
