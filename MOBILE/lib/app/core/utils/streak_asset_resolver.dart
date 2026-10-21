class StreakAssetResolver {
  static const String _basePath = 'assets/brand/icons';

  /// Returns the streak badge asset for the given streak count.
  ///
  /// When [hasActivityToday] is false we show the empty badge (`streak0`).
  /// Otherwise we select the badge according to the current streak range.
  static String assetFor({
    required int streak,
    required bool hasActivityToday,
  }) {
    if (!hasActivityToday) {
      return '$_basePath/streak_0.png';
    }

    return assetByValue(streak);
  }

  /// Returns the streak badge asset purely based on streak value, ignoring
  /// whether the user has completed today's streak action.
  static String assetByValue(int streak) {
    if (streak <= 0) {
      return '$_basePath/streak_1.png';
    }
    if (streak <= 6) {
      return '$_basePath/streak_2.png';
    }
    if (streak <= 13) {
      return '$_basePath/streak_3.png';
    }
    if (streak <= 20) {
      return '$_basePath/streak_4.png';
    }
    if (streak <= 29) {
      return '$_basePath/streak_5.png';
    }
    return '$_basePath/streak_6.png';
  }
}
