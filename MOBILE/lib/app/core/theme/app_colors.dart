import 'package:flutter/material.dart';

/// One set of colour values per theme.
class AppPalette {
  const AppPalette({
    required this.primary,
    required this.primaryDark,
    required this.primarySoft,
    required this.primaryTint,
    required this.primaryLight,
    required this.ink,
    required this.inkSoft,
    required this.background,
    required this.surface,
    required this.surfaceMuted,
    required this.line,
    required this.lineStrong,
    required this.textPrimary,
    required this.textSecondary,
    required this.textHint,
    required this.success,
    required this.successSoft,
    required this.error,
    required this.errorSoft,
  });

  final Color primary, primaryDark, primarySoft, primaryTint, primaryLight, ink, inkSoft;
  final Color background, surface, surfaceMuted, line, lineStrong;
  final Color textPrimary, textSecondary, textHint;
  final Color success, successSoft, error, errorSoft;

  static const light = AppPalette(
    primary: Color(0xFF1899F0),
    primaryDark: Color(0xFF0F7AC4),
    primarySoft: Color(0xFFE8F5FE),
    primaryTint: Color(0xFFA6D8FB),
    primaryLight: Color(0xFF3DABF4),
    ink: Color(0xFF15233B),
    inkSoft: Color(0xFF1F3150),
    background: Color(0xFFF6F8FB),
    surface: Colors.white,
    surfaceMuted: Color(0xFFEEF2F7),
    line: Color(0xFFE3E8EF),
    lineStrong: Color(0xFFCDD6E1),
    textPrimary: Color(0xFF15233B), // all text ≥ 4.5:1 on its surface
    textSecondary: Color(0xFF556273),
    textHint: Color(0xFF6B7787),
    success: Color(0xFF0E9F7B),
    successSoft: Color(0xFFE3F8F1),
    error: Color(0xFFE11D48),
    errorSoft: Color(0xFFFDE8EC),
  );

  /// Same as the web's dark theme (FE/src/index.css `.dark`).
  static const dark = AppPalette(
    primary: Color(0xFF1899F0),
    primaryDark: Color(0xFF0F6FB0),
    primarySoft: Color(0xFF0E2236),
    primaryTint: Color(0xFF12304D),
    primaryLight: Color(0xFF3FA9F5),
    ink: Color(0xFF14233B),
    inkSoft: Color(0xFF1B2D4A),
    background: Color(0xFF0B111B),
    surface: Color(0xFF131B28),
    surfaceMuted: Color(0xFF1A2433),
    line: Color(0xFF243043),
    lineStrong: Color(0xFF33415A),
    textPrimary: Color(0xFFE8EDF3),
    textSecondary: Color(0xFF9AA8BB),
    textHint: Color(0xFF8292A8),
    success: Color(0xFF3DDBA5),
    successSoft: Color(0xFF0F2A24),
    error: Color(0xFFFB7185),
    errorSoft: Color(0xFF33141F),
  );
}

/// LingoPrism colours – the same tokens as the web.
///
/// The blue is the brand; the three beams leaving the prism (amber · mint · coral)
/// stand for the three languages and for the day's progress – they carry meaning,
/// they are not decoration.
///
/// The values follow the chosen theme (see ThemeService): when it changes the whole
/// app is rebuilt, so every `AppColors.x` read picks up the new palette.
class AppColors {
  AppColors._();

  static AppPalette _p = AppPalette.light;
  static bool get isDark => identical(_p, AppPalette.dark);
  static void use(Brightness b) => _p = b == Brightness.dark ? AppPalette.dark : AppPalette.light;

  // Brand
  static Color get primary => _p.primary;
  static Color get primaryDark => _p.primaryDark;
  static Color get primarySoft => _p.primarySoft;
  static Color get primaryTint => _p.primaryTint;
  static Color get primaryLight => _p.primaryLight;
  static Color get ink => _p.ink;
  static Color get inkSoft => _p.inkSoft;

  // The three beams (one per language: EN amber · 中文 coral · VI mint) – same in both themes
  static const Color beamAmber = Color(0xFFFFB020);
  static const Color beamMint = Color(0xFF10C79A);
  static const Color beamCoral = Color(0xFFFF6B81);

  // Surfaces
  static Color get background => _p.background;
  static Color get surface => _p.surface;
  static Color get surfaceMuted => _p.surfaceMuted;
  static Color get line => _p.line;
  static Color get lineStrong => _p.lineStrong;

  // Text
  static Color get textPrimary => _p.textPrimary;
  static Color get textSecondary => _p.textSecondary;
  static Color get textHint => _p.textHint;
  static const Color textWhite = Colors.white;
  static Color get textError => _p.error;

  // States
  static Color get success => _p.success;
  static Color get successSoft => _p.successSoft;
  static Color get error => _p.error;
  static Color get errorSoft => _p.errorSoft;

  // ---- older names, kept so every screen follows the same palette ----
  static Color get primaryBlue => primary;
  static const Color primaryGreen = beamMint;
  static Color get primaryAccent => primary;

  static Color get backgroundLight => background;
  static Color get backgroundWhite => surface;
  static Color get backgroundOverlay => surfaceMuted;
  static Color get appBarBackground => surface;

  static Color get buttonActive => primary;
  static Color get buttonDisabled => lineStrong;
  static Color get buttonSuccess => success;
  static Color get buttonDanger => error;

  static Color get cardBackground => surface;
  static Color get surfaceLight => surfaceMuted;

  static const Color streakFire = Color(0xFFFF8A3D);
  static Color get gemBlue => primary;
  static Color get heartRed => error;
  static const Color xpGold = beamAmber;

  static const Color google = Color(0xFF4285F4);
  static const Color facebook = Color(0xFF1877F2);

  static const Color progressComplete = beamMint;
  static Color get progressCurrent => primary;
  static Color get progressLocked => lineStrong;

  /// Was the violet → sky → mint sweep; now the ink surface, flat.
  static LinearGradient get primaryGradient => LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [ink, ink],
      );

  static LinearGradient get cardGradient => LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [surface, surface],
      );

  /// A pale tint chosen for the light theme; in dark it becomes the same hue, quietly, on the dark surface.
  static Color tint(Color light) => isDark ? Color.alphaBlend(light.withValues(alpha: 0.16), _p.surface) : light;

  static Color get shadow => isDark ? const Color(0x66000000) : const Color(0x1F15233B);
  static Color get shadowLight => isDark ? const Color(0x33000000) : const Color(0x0D15233B);
}
