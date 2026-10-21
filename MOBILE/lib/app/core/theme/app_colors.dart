import 'package:flutter/material.dart';

/// LingoPrism colours – the same tokens as the web (FE/src/index.css).
///
/// The violet is the brand; the three beams leaving the prism (amber · mint · coral)
/// stand for the three languages and for the day's progress – they carry meaning,
/// they are not decoration.
class AppColors {
  AppColors._();

  // Brand
  static const Color primary = Color(0xFF6D4AFF);
  static const Color primaryDark = Color(0xFF5533E0);
  static const Color primarySoft = Color(0xFFF2EFFF);
  static const Color primaryTint = Color(0xFFCDC2FF);
  static const Color primaryLight = Color(0xFF8F75FF);
  static const Color ink = Color(0xFF1B1538);
  static const Color inkSoft = Color(0xFF2A2350);

  // The three beams (one per language: EN amber · 中文 coral · VI mint)
  static const Color beamAmber = Color(0xFFFFB020);
  static const Color beamMint = Color(0xFF10C79A);
  static const Color beamCoral = Color(0xFFFF6B81);

  // Surfaces
  static const Color background = Color(0xFFF5F4F9);
  static const Color surface = Colors.white;
  static const Color surfaceMuted = Color(0xFFF0EEF6);
  static const Color line = Color(0xFFE7E4F0);
  static const Color lineStrong = Color(0xFFD3CEE3);

  // Text (all ≥ 4.5:1 on white)
  static const Color textPrimary = Color(0xFF1B1538);
  static const Color textSecondary = Color(0xFF5D5878);
  static const Color textHint = Color(0xFF767190);
  static const Color textWhite = Colors.white;
  static const Color textError = Color(0xFFE11D48);

  // States
  static const Color success = Color(0xFF0E9F7B);
  static const Color successSoft = Color(0xFFE3F8F1);
  static const Color error = Color(0xFFE11D48);
  static const Color errorSoft = Color(0xFFFDE8EC);

  // ---- older names, kept so every screen follows the same palette ----
  static const Color primaryBlue = primary;
  static const Color primaryGreen = beamMint;
  static const Color primaryAccent = primary;

  static const Color backgroundLight = background;
  static const Color backgroundWhite = surface;
  static const Color backgroundOverlay = surfaceMuted;
  static const Color appBarBackground = surface;

  static const Color buttonActive = primary;
  static const Color buttonDisabled = lineStrong;
  static const Color buttonSuccess = success;
  static const Color buttonDanger = error;

  static const Color cardBackground = surface;
  static const Color surfaceLight = surfaceMuted;

  static const Color streakFire = Color(0xFFFF8A3D);
  static const Color gemBlue = primary;
  static const Color heartRed = error;
  static const Color xpGold = beamAmber;

  static const Color google = Color(0xFF4285F4);
  static const Color facebook = Color(0xFF1877F2);

  static const Color progressComplete = beamMint;
  static const Color progressCurrent = primary;
  static const Color progressLocked = lineStrong;

  /// Was the violet → sky → mint sweep; now the ink surface, flat, so the screens
  /// that still ask for "the brand background" get one calm colour.
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [ink, ink],
  );

  static const LinearGradient cardGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [surface, surface],
  );

  static const Color shadow = Color(0x1F1B1538);
  static const Color shadowLight = Color(0x0D1B1538);
}
