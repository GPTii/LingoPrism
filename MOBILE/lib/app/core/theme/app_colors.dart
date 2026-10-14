import 'package:flutter/material.dart';

class AppColors {
  AppColors._();

  // Primary gradient colors
  static const Color primaryBlue = Color(0xFF0571E6);
  static const Color primaryGreen = Color(0xFF90F3A7);
  static const Color primaryAccent = Color(0xFF0088FF);

  // Background colors
  static const Color backgroundLight = Color(0xFFE5FFFD);
  static const Color backgroundWhite = Colors.white;
  static const Color backgroundOverlay = Color(0x70FFFFFF);
  static const Color appBarBackground = Color(0xFFBBFFEE);

  // Text colors
  static const Color textPrimary = Color(0xFF1A1A1A);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color textHint = Color(0xFF9CA3AF);
  static const Color textWhite = Colors.white;
  static const Color textError = Color(0xFFEF4444);

  // Button colors
  static const Color buttonActive = Color(0xFF0088FF);
  static const Color buttonDisabled = Color(0xFFBDBDBD);
  static const Color buttonSuccess = Color(0xFF10B981);
  static const Color buttonDanger = Color(0xFFEF4444);

  // Card and surface colors
  static const Color cardBackground = Color(0xFFFFFFFF);
  static const Color surfaceLight = Color(0xFFF9FAFB);

  // Accent colors for learning features
  static const Color streakFire = Color(0xFFFF6B35);
  static const Color gemBlue = Color(0xFF3B82F6);
  static const Color heartRed = Color(0xFFEF4444);
  static const Color xpGold = Color(0xFFFBBF24);

  // Social colors
  static const Color google = Color(0xFF4285F4);
  static const Color facebook = Color(0xFF1877F2);

  // Progress colors
  static const Color progressComplete = Color(0xFF10B981);
  static const Color progressCurrent = Color(0xFF3B82F6);
  static const Color progressLocked = Color(0xFFD1D5DB);

  // Gradients
  static const LinearGradient primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    stops: [0.0, 0.43, 1.0],
    colors: [
      Color(0xFF0571E6), // 0%
      Color(0xFF90F3A7), // 43%
      Color(0xFF0088FF), // 100%
    ],
  );

  static const LinearGradient cardGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [
      Color(0xFFE5FFFD),
      Color(0xFFFFFFFF),
    ],
  );

  // Shadow colors
  static const Color shadow = Color(0x1A000000);
  static const Color shadowLight = Color(0x0D000000);
}