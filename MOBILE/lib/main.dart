import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import 'app/core/theme/app_theme.dart';
import 'app/core/theme/theme_service.dart';
import 'app/core/widgets/target_word.dart';
import 'app/data/services/auth_service.dart';
import 'app/data/services/service_binding.dart';
import 'app/routes/app_pages.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Local storage, API client, auth session, local notifications
  await AppInitializer.initialize();
  ThemeService.init(); // light / dark chosen on this device

  runApp(const LingoPrismApp());
}

class LingoPrismApp extends StatelessWidget {
  const LingoPrismApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ScreenUtilInit(
      designSize: const Size(375, 812), // iPhone X design size
      minTextAdapt: true,
      splitScreenMode: true,
      builder: (context, child) {
        return GetMaterialApp(
          title: 'LingoPrism',
          theme: AppTheme.lightTheme,
          darkTheme: AppTheme.darkTheme,
          themeMode: ThemeService.mode,
          initialBinding: ServiceBinding(),
          initialRoute: AppPages.initial,
          getPages: AppPages.routes,
          debugShowCheckedModeBanner: false,
          builder: (context, child) => _LearningLocale(child: child ?? const SizedBox()),
        );
      },
    );
  }
}

/// Gives every text the locale of the language being learned so Chinese characters are drawn
/// with mainland (zh-Hans-CN) or Taiwan (zh-Hant-TW) glyph forms. The Vietnamese UI is unaffected.
class _LearningLocale extends StatelessWidget {
  const _LearningLocale({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final code = AuthService.to.user.value?.targetCode ?? 'vi';
      final locale = code.startsWith('zh') ? localeFor(code) : null;
      if (locale == null) return child;
      final theme = Theme.of(context);
      TextStyle? withLocale(TextStyle? s) => s?.copyWith(locale: locale);
      final t = theme.textTheme;
      final textTheme = t.copyWith(
        displayLarge: withLocale(t.displayLarge), displayMedium: withLocale(t.displayMedium), displaySmall: withLocale(t.displaySmall),
        headlineLarge: withLocale(t.headlineLarge), headlineMedium: withLocale(t.headlineMedium), headlineSmall: withLocale(t.headlineSmall),
        titleLarge: withLocale(t.titleLarge), titleMedium: withLocale(t.titleMedium), titleSmall: withLocale(t.titleSmall),
        bodyLarge: withLocale(t.bodyLarge), bodyMedium: withLocale(t.bodyMedium), bodySmall: withLocale(t.bodySmall),
        labelLarge: withLocale(t.labelLarge), labelMedium: withLocale(t.labelMedium), labelSmall: withLocale(t.labelSmall),
      );
      return Theme(
        data: theme.copyWith(textTheme: textTheme),
        child: DefaultTextStyle.merge(style: TextStyle(locale: locale), child: child),
      );
    });
  }
}
