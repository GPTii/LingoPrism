class StreakAssetResolver {
  static const String _basePath = 'assets/images/streak';

  /// Returns the streak badge asset for the given streak count.
  ///
  /// When [hasActivityToday] is false we show the empty badge (`streak0`).
  /// Otherwise we select the badge according to the current streak range.
  static String assetFor({
    required int streak,
    required bool hasActivityToday,
  }) {
    if (!hasActivityToday) {
      return '$_basePath/streak0.png';
    }

    return assetByValue(streak);
  }

  /// Returns the streak badge asset purely based on streak value, ignoring
  /// whether the user has completed today's streak action.
  static String assetByValue(int streak) {
    if (streak <= 0) {
      return '$_basePath/streak1.png';
    }
    if (streak <= 6) {
      return '$_basePath/streak2.png';
    }
    if (streak <= 13) {
      return '$_basePath/streak3.png';
    }
    if (streak <= 20) {
      return '$_basePath/streak4.png';
    }
    if (streak <= 29) {
      return '$_basePath/streak5.png';
    }
    return '$_basePath/streak6.png';
  }
}
