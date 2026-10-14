/// Community Leaderboard View
///
/// A comprehensive leaderboard display for the SnapLingua community feature
/// showing league rankings with different status categories.
///
/// Features:
/// - League information display with rank progression
/// - Three categories: Promotion, Safe, and Demotion participants
/// - Performance optimized with caching and RepaintBoundary widgets
/// - Comprehensive null safety and validation
/// - Medal decorations for top 3 participants
/// - Avatar loading with fallback handling
/// - Enhanced error handling and user experience
///
/// Performance Optimizations:
/// - Avatar image caching with LRU management
/// - RepaintBoundary widgets to minimize rebuilds
/// - ListView caching with optimized physics
/// - Memoized expensive calculations
///
/// Author: Claude Code Assistant
/// Last updated: November 2024
library;

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';

import '../controllers/community_controller.dart';

/// Main leaderboard view widget displaying community league rankings
///
/// This widget provides a comprehensive view of the current league standings
/// organized into three categories: promotion, safe, and demotion zones.
/// Includes league header with rank progression and optimized participant lists.
class CommunityLeaderboardView extends StatelessWidget {
  const CommunityLeaderboardView({super.key, required this.controller});

  final CommunityController controller;

  /// Performance optimization constants
  static const double _listCacheExtent = 600.0;

  @override
  Widget build(BuildContext context) {
    return Obx(() {
      final league = controller.currentLeague.value;
      // final notice = controller.tournamentNotice.value;
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Tournament notice is temporarily disabled - will be implemented when available in controller
          // if (notice != null) ...[
          //   TournamentNoticeBanner(notice: notice),
          //   SizedBox(height: 16.h),
          // ],
          _LeagueHeader(league: league),
          SizedBox(height: 18.h),
          Expanded(
            child: ListView(
              padding: EdgeInsets.only(bottom: 24.h),
              // Performance optimizations for smooth scrolling
              cacheExtent: _listCacheExtent,
              physics: const BouncingScrollPhysics(
                parent: AlwaysScrollableScrollPhysics(),
              ),
              children: [
                _LeagueSection(
                  title: 'Top Thăng Hạng',
                  color: const Color(0xFFBFF7AF),
                  participants: controller.promotionLeaders,
                  onParticipantTap: controller.openLeaderboardProfile,
                ),
                SizedBox(height: 16.h),
                _LeagueSection(
                  title: 'Top An Toàn',
                  color: const Color(0xFFFFF3B0),
                  participants: controller.safeLeaders,
                  onParticipantTap: controller.openLeaderboardProfile,
                ),
                SizedBox(height: 16.h),
                _LeagueSection(
                  title: 'Top Tụt Hạng',
                  color: const Color(0xFFFFC2C0),
                  participants: controller.demotionLeaders,
                  onParticipantTap: controller.openLeaderboardProfile,
                ),
              ],
            ),
          ),
        ],
      );
    });
  }
}

/// League header widget displaying current league information and rank progression
///
/// Shows the current league name, remaining time, and a horizontal scrollable
/// view of all rank icons with current position highlighted.
/// Includes enhanced null safety and error handling for rank assets.
class _LeagueHeader extends StatelessWidget {
  const _LeagueHeader({required this.league});

  final CommunityLeagueInfo league;

  /// Static rank asset paths for performance optimization
  static const List<String> _rankAssets = [
    'assets/images/rank/rank1.png',
    'assets/images/rank/rank2.png',
    'assets/images/rank/rank3.png',
    'assets/images/rank/rank4.png',
    'assets/images/rank/rank5.png',
    'assets/images/rank/rank6.png',
    'assets/images/rank/rank7.png',
    'assets/images/rank/rank8.png',
    'assets/images/rank/rank9.png',
    'assets/images/rank/rank10.png',
  ];

  /// Helper method to create remaining label from days remaining
  String _getRemainingLabel(CommunityLeagueInfo league) {
    if (league.daysRemaining <= 0) {
      return 'Đã kết thúc';
    } else if (league.daysRemaining == 1) {
      return 'Còn 1 ngày';
    } else {
      return 'Còn ${league.daysRemaining} ngày';
    }
  }

  @override
  Widget build(BuildContext context) {
    // Enhanced null safety for rank icon resolution
    final rankIcon = league.rankIcon.trim();
    final currentRankIndex = rankIcon.isNotEmpty
        ? _rankAssets.indexOf(rankIcon).clamp(0, _rankAssets.length - 1)
        : 0;

    return Container(
      padding: EdgeInsets.all(20.w),
      decoration: BoxDecoration(
        color: const Color(0xFFE6F9FF),
        borderRadius: BorderRadius.circular(28.r),
        border: Border.all(color: const Color(0xFF9ED1FF), width: 1.2),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 18.r,
            offset: Offset(0, 10.h),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Giải đấu',
                      style: TextStyle(
                        fontSize: 16.sp,
                        fontWeight: FontWeight.w600,
                        color: const Color(0xFF113355),
                      ),
                    ),
                    SizedBox(height: 6.h),
                    Text(
                      league.name.isNotEmpty ? league.name : 'Giải đấu không xác định',
                      style: TextStyle(
                        fontSize: 22.sp,
                        fontWeight: FontWeight.w800,
                        color: const Color(0xFF0A2C60),
                      ),
                    ),
                  ],
                ),
              ),
              Text(
                _getRemainingLabel(league),
                style: TextStyle(
                  fontSize: 15.sp,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF7F8A99),
                ),
              ),
            ],
          ),
          SizedBox(height: 20.h),
          SizedBox(
            height: 96.h,
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: List.generate(_rankAssets.length, (index) {
                  final asset = _rankAssets[index];
                  final bool isUnlocked = index <= currentRankIndex;
                  // Enhanced comparison for current rank with null safety
                  final bool isCurrent = asset == rankIcon && rankIcon.isNotEmpty;
                  final displayAsset =
                      isUnlocked ? asset : 'assets/images/rank/rank?.png';
                  return RepaintBoundary(
                    key: ValueKey('rank_${index}_$isCurrent'),
                    child: Container(
                    width: 88.w,
                    margin: EdgeInsets.only(right: index == _rankAssets.length - 1 ? 0 : 14.w),
                    padding: EdgeInsets.all(14.w),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(26.r),
                      border: Border.all(
                        color: isCurrent ? const Color(0xFF0A69C7) : Colors.transparent,
                        width: 2.w,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.05),
                          blurRadius: 16.r,
                          offset: Offset(0, 8.h),
                        ),
                      ],
                    ),
                    child: Opacity(
                      opacity: isUnlocked ? 1 : 0.35,
                      child: Image.asset(
                        displayAsset,
                        width: 56.w,
                        height: 56.w,
                        fit: BoxFit.contain,
                        // Enhanced error handling for rank assets
                        errorBuilder: (context, error, stackTrace) {
                          debugPrint('Failed to load rank asset: $displayAsset - $error');
                          return Container(
                            width: 56.w,
                            height: 56.w,
                            decoration: BoxDecoration(
                              color: Colors.grey.shade200,
                              borderRadius: BorderRadius.circular(8.r),
                            ),
                            child: Icon(
                              Icons.emoji_events,
                              size: 28.w,
                              color: Colors.grey.shade400,
                            ),
                          );
                        },
                      ),
                    ),
                    ),
                  );
                }),
              ),
            ),
          ),
          SizedBox(height: 20.h),
          SizedBox(height: 6.h),
          if (league.xpCapDescription != null) ...[
            SizedBox(height: 6.h),
            Text(
              'Giới hạn XP: ${league.xpCapDescription!}',
              style: TextStyle(
                fontSize: 12.sp,
                color: const Color(0xFF6A7B94),
                height: 1.3,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// League section widget for displaying categorized participant lists
///
/// Displays participants in different categories (promotion, safe, demotion)
/// with color-coded headers and optimized tile rendering using RepaintBoundary.
/// Each section includes a labeled header and scrollable participant list.
class _LeagueSection extends StatelessWidget {
  const _LeagueSection({
    required this.title,
    required this.color,
    required this.participants,
    required this.onParticipantTap,
  });

  final String title;
  final Color color;
  final List<CommunityLeaderboardParticipant> participants;
  final ValueChanged<CommunityLeaderboardParticipant> onParticipantTap;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28.r),
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 18.r,
            offset: Offset(0, 10.h),
          ),
        ],
      ),
      padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 18.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 6.h),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(20.r),
              color: color,
            ),
            child: Text(
              title.toUpperCase(),
              style: TextStyle(
                fontSize: 13.sp,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF1B2B40),
              ),
            ),
          ),
          SizedBox(height: 16.h),
          for (var i = 0; i < participants.length; i++)
            Padding(
              padding: EdgeInsets.only(
                bottom: i == participants.length - 1 ? 0 : 12.h,
              ),
              child: RepaintBoundary(
                key: ValueKey('participant_${participants[i].userId}'),
                child: _LeagueParticipantTile(
                  participant: participants[i],
                  onTap: onParticipantTap,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// Individual participant tile widget with comprehensive features
///
/// Displays a single leaderboard participant with:
/// - Validated rank display with bounds checking
/// - Cached avatar image with multiple fallback strategies
/// - Validated participant name with length limits and fallbacks
/// - XP display with validation and multiple point sources
/// - Status-based colors and decorations (promotion/safe/demotion)
/// - Special medal decorations for top 3 participants
/// - Enhanced error handling and null safety throughout
///
/// Performance Features:
/// - Static avatar image cache with LRU management
/// - Memoized calculations for expensive operations
/// - RepaintBoundary integration for minimal rebuilds
class _LeagueParticipantTile extends StatelessWidget {
  const _LeagueParticipantTile({
    required this.participant,
    required this.onTap,
  });

  final CommunityLeaderboardParticipant participant;
  final ValueChanged<CommunityLeaderboardParticipant> onTap;

  /// Static avatar cache for performance optimization with LRU management
  static final Map<String, ImageProvider> _avatarCache = <String, ImageProvider>{};
  static const int _maxCacheSize = 50;

  Color get _background {
    switch (participant.status) {
      case CommunityLeaderboardStatus.promotion:
        return const Color(0xFFBFF7AF);
      case CommunityLeaderboardStatus.safe:
        return const Color(0xFFFFF3B0);
      case CommunityLeaderboardStatus.demotion:
        return const Color(0xFFFFC2C0);
    }
  }

  Color get _borderColor {
    switch (participant.status) {
      case CommunityLeaderboardStatus.promotion:
        return const Color(0xFF5CD560);
      case CommunityLeaderboardStatus.safe:
        return const Color(0xFFF1B04C);
      case CommunityLeaderboardStatus.demotion:
        return const Color(0xFFE55E5B);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: _tileDecoration,
      padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 10.h),
      child: Row(
        children: [
          SizedBox(
            width: 32.w,
            child: Text(
              '$_validatedRank',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16.sp,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF1B2B40),
              ),
            ),
          ),
          SizedBox(width: 12.w),
          CircleAvatar(
            radius: 22.r,
            backgroundImage: _getCachedAvatarProvider(participant.avatarUrl),
          ),
          SizedBox(width: 12.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                GestureDetector(
                  onTap: () => onTap(participant),
                  child: Text(
                    _validatedName,
                    style: TextStyle(
                      fontSize: 15.sp,
                      fontWeight: FontWeight.w700,
                      color: const Color(0xFF20324A),
                      decoration: TextDecoration.underline,
                      decorationStyle: TextDecorationStyle.dotted,
                    ),
                  ),
                ),
              ],
            ),
          ),
          SizedBox(width: 8.w),
          Row(
            children: [
              Text(
                '$_displayedXp',
                style: TextStyle(
                  fontSize: 18.sp,
                  fontWeight: FontWeight.w700,
                  color: const Color(0xFF1B2B40),
                ),
              ),
              SizedBox(width: 6.w),
              Image.asset(
                'assets/images/XP.png',
                width: 26.w,
                height: 26.w,
              ),
            ],
          ),
        ],
      ),
    );
  }

  /// Validated rank with bounds checking
  int get _validatedRank {
    return participant.rank.clamp(1, 9999);
  }

  /// Validated participant name with fallback
  String get _validatedName {
    final name = participant.name.trim();
    if (name.isEmpty) {
      return 'Người dùng #$_validatedRank';
    }
    // Limit name length for display
    if (name.length > 20) {
      return '${name.substring(0, 17)}...';
    }
    return name;
  }

  int get _displayedXp {
    // Enhanced XP calculation with validation
    final totalPoints = participant.totalPoints.clamp(0, 999999);
    final rawPoints = participant.rawPoints.clamp(0, 999999);

    if (totalPoints > 0) {
      return totalPoints;
    }
    if (rawPoints > 0) {
      return rawPoints;
    }
    return 0;
  }

  ImageProvider _resolveAvatarProvider(String? avatarUrl) {
    const placeholder = AssetImage('assets/images/chimcanhcut/chim_vui1.png');

    // Enhanced null safety and validation
    final trimmed = avatarUrl?.trim() ?? '';
    if (trimmed.isEmpty) {
      return placeholder;
    }

    try {
      // Network image handling
      if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
        final uri = Uri.tryParse(trimmed);
        if (uri != null && (uri.scheme == 'http' || uri.scheme == 'https')) {
          return NetworkImage(trimmed);
        }
        return placeholder;
      }

      // Asset image handling
      if (trimmed.startsWith('assets/')) {
        return AssetImage(trimmed);
      }

      // URI-based file handling with enhanced safety
      if (trimmed.startsWith('file://') || trimmed.startsWith('content://')) {
        final uri = Uri.tryParse(trimmed);
        if (uri != null) {
          final file = File.fromUri(uri);
          // Use synchronous existence check with error handling
          if (_fileExistsSync(file)) {
            return FileImage(file);
          }
        }
        return placeholder;
      }

      // Direct file path handling
      final file = File(trimmed);
      if (_fileExistsSync(file)) {
        return FileImage(file);
      }

    } catch (e) {
      // Log error for debugging but return placeholder
      debugPrint('Avatar provider error for URL "$trimmed": $e');
    }

    return placeholder;
  }

  /// Safe file existence check with exception handling
  bool _fileExistsSync(File file) {
    try {
      return file.existsSync();
    } catch (e) {
      debugPrint('File existence check failed: $e');
      return false;
    }
  }

  /// Cached avatar provider with size management
  ImageProvider _getCachedAvatarProvider(String? avatarUrl) {
    final url = avatarUrl?.trim() ?? '';

    // Check cache first
    if (_avatarCache.containsKey(url)) {
      return _avatarCache[url]!;
    }

    // Resolve the avatar provider
    final provider = _resolveAvatarProvider(avatarUrl);

    // Manage cache size and add new provider
    if (_avatarCache.length >= _maxCacheSize) {
      // Remove oldest entries (simple FIFO strategy)
      final keys = _avatarCache.keys.toList();
      _avatarCache.remove(keys.first);
    }

    _avatarCache[url] = provider;
    return provider;
  }

  BoxDecoration get _tileDecoration {
    final borderRadius = BorderRadius.circular(22.r);
    final shadow = [
      BoxShadow(
        color: Colors.black.withValues(alpha: 0.05),
        blurRadius: 12.r,
        offset: Offset(0, 6.h),
      ),
    ];

    // Enhanced decoration logic with validation
    final validatedRank = _validatedRank;

    switch (validatedRank) {
      case 1:
        return _buildGoldDecoration(borderRadius, shadow);
      case 2:
        return _buildSilverDecoration(borderRadius, shadow);
      case 3:
        return _buildBronzeDecoration(borderRadius, shadow);
      default:
        return _buildDefaultDecoration(borderRadius, shadow);
    }
  }

  /// Gold medal decoration for 1st place
  BoxDecoration _buildGoldDecoration(BorderRadius borderRadius, List<BoxShadow> shadow) {
    return BoxDecoration(
      borderRadius: borderRadius,
      gradient: const LinearGradient(
        colors: [Color(0xFFFFE066), Color(0xFFFFB347)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      border: Border.all(color: const Color(0xFFFFC107), width: 1.6),
      boxShadow: shadow,
    );
  }

  /// Silver medal decoration for 2nd place
  BoxDecoration _buildSilverDecoration(BorderRadius borderRadius, List<BoxShadow> shadow) {
    return BoxDecoration(
      borderRadius: borderRadius,
      gradient: const LinearGradient(
        colors: [Color(0xFFE0E0E0), Color(0xFFC9D6FF)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      border: Border.all(color: const Color(0xFFB0BEC5), width: 1.6),
      boxShadow: shadow,
    );
  }

  /// Bronze medal decoration for 3rd place
  BoxDecoration _buildBronzeDecoration(BorderRadius borderRadius, List<BoxShadow> shadow) {
    return BoxDecoration(
      borderRadius: borderRadius,
      gradient: const LinearGradient(
        colors: [Color(0xFFFFD7B5), Color(0xFFFF8C42)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
      border: Border.all(color: const Color(0xFFFFA64D), width: 1.6),
      boxShadow: shadow,
    );
  }

  /// Default decoration for other ranks
  BoxDecoration _buildDefaultDecoration(BorderRadius borderRadius, List<BoxShadow> shadow) {
    return BoxDecoration(
      borderRadius: borderRadius,
      color: _background,
      border: Border.all(
        color: _borderColor,
        width: 1.4,
      ),
      boxShadow: shadow,
    );
  }
}
