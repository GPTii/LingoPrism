import '../../../core/utils/brand_assets.dart';
import 'common.dart';

class GameSummary {
  GameSummary({
    this.lifetimeXp = 0,
    this.level = 1,
    this.todayXp = 0,
    this.dailyXpCap = 500,
    this.streak = 0,
    this.longestStreak = 0,
    this.studiedToday = false,
    this.scales = 0,
    this.gems = 0,
    this.streakFreezes = 0,
    this.freezesUsed = 0,
    this.wordsLearned = 0,
    this.wordsMastered = 0,
    this.newLearned = 0,
    this.newTarget = 10,
    this.reviewsDone = 0,
    this.reviewTarget = 20,
    this.activeBoosts = const [],
    this.leagueTier,
    this.weeklyXp = 0,
  });

  final int lifetimeXp;
  final int level;
  final int todayXp;
  final int dailyXpCap;
  final int streak;
  final int longestStreak;
  final bool studiedToday;
  final int scales;
  final int gems;
  final int streakFreezes;
  final int freezesUsed;
  final int wordsLearned;
  final int wordsMastered;
  final int newLearned;
  final int newTarget;
  final int reviewsDone;
  final int reviewTarget;
  final List<Map<String, dynamic>> activeBoosts;
  final String? leagueTier;
  final int weeklyXp;

  factory GameSummary.fromJson(Map<String, dynamic> j) {
    final today = asMap(j['today']);
    final league = j['league'] is Map ? asMap(j['league']) : null;
    return GameSummary(
      lifetimeXp: asInt(j['lifetime_xp']),
      level: asInt(j['level'], 1),
      todayXp: asInt(j['today_xp']),
      dailyXpCap: asInt(j['daily_xp_cap'], 500),
      streak: asInt(j['streak']),
      longestStreak: asInt(j['longest_streak']),
      studiedToday: j['studied_today'] == true,
      scales: asInt(j['scales']),
      gems: asInt(j['gems']),
      streakFreezes: asInt(j['streak_freezes']),
      freezesUsed: asInt(j['freezes_used']),
      wordsLearned: asInt(j['words_learned']),
      wordsMastered: asInt(j['words_mastered']),
      newLearned: asInt(today['new_learned']),
      newTarget: asInt(today['new_target'], 10),
      reviewsDone: asInt(today['reviews_done']),
      reviewTarget: asInt(today['review_target'], 20),
      activeBoosts: asMapList(j['active_boosts']),
      leagueTier: league?['tier'] as String?,
      weeklyXp: asInt(league?['weekly_xp']),
    );
  }
}

class DayProgress {
  DayProgress({required this.date, this.xp = 0, this.newLearned = 0, this.reviewsDone = 0, this.active = false, this.freezeUsed = false});

  final DateTime date;
  final int xp;
  final int newLearned;
  final int reviewsDone;
  final bool active;
  final bool freezeUsed;

  factory DayProgress.fromJson(Map<String, dynamic> j) => DayProgress(
        date: DateTime.parse(asString(j['date'])),
        xp: asInt(j['xp']),
        newLearned: asInt(j['new_learned']),
        reviewsDone: asInt(j['reviews_done']),
        active: j['active'] == true,
        freezeUsed: j['freeze_used'] == true,
      );
}

class DailyQuest {
  DailyQuest({
    required this.id,
    required this.kind,
    required this.title,
    required this.target,
    required this.progress,
    required this.completed,
    required this.rewardClaimed,
    this.rewardScales = 15,
  });

  final int id;
  final String kind;
  final String title;
  final int target;
  final int progress;
  final bool completed;
  final bool rewardClaimed;
  final int rewardScales;

  double get ratio => target == 0 ? 0 : (progress / target).clamp(0, 1).toDouble();

  factory DailyQuest.fromJson(Map<String, dynamic> j) => DailyQuest(
        id: asInt(j['id']),
        kind: asString(j['kind']),
        title: asString(j['title']),
        target: asInt(j['target']),
        progress: asInt(j['progress']),
        completed: j['completed'] == true,
        rewardClaimed: j['reward_claimed'] == true,
        rewardScales: asInt(j['reward_scales'], 15),
      );
}

class MonthlyQuest {
  MonthlyQuest({required this.month, this.completedCount = 0, this.target = 20, this.rewardGems = 2, this.rewardClaimed = false});

  final String month;
  final int completedCount;
  final int target;
  final int rewardGems;
  final bool rewardClaimed;

  bool get canClaim => completedCount >= target && !rewardClaimed;

  factory MonthlyQuest.fromJson(Map<String, dynamic> j) => MonthlyQuest(
        month: asString(j['month']),
        completedCount: asInt(j['completed_count']),
        target: asInt(j['target'], 20),
        rewardGems: asInt(j['reward_gems'], 2),
        rewardClaimed: j['reward_claimed'] == true,
      );
}

class BadgeInfo {
  BadgeInfo({required this.code, required this.name, this.description = '', this.icon = '', this.owned = false, this.awardedAt});

  final String code;
  final String name;
  final String description;
  final String icon;
  final bool owned;
  final DateTime? awardedAt;

  factory BadgeInfo.fromJson(Map<String, dynamic> j) => BadgeInfo(
        code: asString(j['code']),
        name: asString(j['name']),
        description: asString(j['description']),
        icon: brandAsset(asString(j['icon'])),
        owned: j['owned'] == true,
        awardedAt: parseDate(j['awarded_at']),
      );
}

class LeaderboardEntry {
  LeaderboardEntry({required this.rank, required this.userId, required this.displayName, this.avatar, this.xp = 0, this.zone = 'safe', this.isMe = false});

  final int rank;
  final int userId;
  final String displayName;
  final String? avatar;
  final int xp;
  final String zone; // promotion | safe | demotion
  final bool isMe;

  factory LeaderboardEntry.fromJson(Map<String, dynamic> j) => LeaderboardEntry(
        rank: asInt(j['rank']),
        userId: asInt(j['user_id']),
        displayName: asString(j['display_name']),
        avatar: _brandOrNull(j['avatar'] as String?),
        xp: asInt(j['xp']),
        zone: asString(j['zone'], 'safe'),
        isMe: j['is_me'] == true,
      );
}

class LeagueTierInfo {
  LeagueTierInfo({required this.code, required this.name, this.order = 0, this.icon = ''});

  final String code;
  final String name;
  final int order;
  final String icon;

  factory LeagueTierInfo.fromJson(Map<String, dynamic> j) =>
      LeagueTierInfo(code: asString(j['code']), name: asString(j['name']), order: asInt(j['order']), icon: brandAsset(asString(j['icon'])));
}

class Leaderboard {
  Leaderboard({required this.scope, this.tierName, this.tierCode, this.endsAt, this.tiers = const [], this.members = const []});

  final String scope;
  final String? tierName;
  final String? tierCode;
  final DateTime? endsAt;
  final List<LeagueTierInfo> tiers;
  final List<LeaderboardEntry> members;

  factory Leaderboard.fromJson(Map<String, dynamic> j) {
    final tier = j['tier'] is Map ? asMap(j['tier']) : null;
    return Leaderboard(
      scope: asString(j['scope']),
      tierName: tier?['name'] as String?,
      tierCode: tier?['code'] as String?,
      endsAt: parseDate(j['ends_at']),
      tiers: asMapList(j['tiers']).map(LeagueTierInfo.fromJson).toList(),
      members: asMapList(j['members']).map(LeaderboardEntry.fromJson).toList(),
    );
  }
}

class ShopItem {
  ShopItem({required this.id, required this.code, required this.name, required this.description, required this.image,
      required this.effect, this.costScales, this.costGems, this.owned = 0});

  final int id;
  final String code;
  final String name;
  final String description;
  final String image;
  final String effect;
  final int? costScales;
  final int? costGems;
  final int owned;

  bool get paidWithScales => costScales != null && costScales! > 0;
  int get price => paidWithScales ? costScales! : (costGems ?? 0);
  bool get isBoost => effect == 'xp_double_15m' || effect == 'xp_plus25_24h';
  bool get isSticker => effect == 'sticker';

  factory ShopItem.fromJson(Map<String, dynamic> j) => ShopItem(
        id: asInt(j['id']),
        code: asString(j['code']),
        name: asString(j['name']),
        description: asString(j['description']),
        image: brandAsset(asString(j['image'])),
        effect: asString(j['effect']),
        costScales: j['cost_scales'] == null ? null : asInt(j['cost_scales']),
        costGems: j['cost_gems'] == null ? null : asInt(j['cost_gems']),
        owned: asInt(j['owned']),
      );
}

class AppNotification {
  AppNotification({required this.id, required this.kind, required this.title, this.body = '', this.image = '',
      this.data = const {}, this.read = false, required this.createdAt});

  final int id;
  final String kind;
  final String title;
  final String body;
  final String image;
  final Map<String, dynamic> data;
  final bool read;
  final DateTime createdAt;

  String? get route => data['route'] as String?;

  AppNotification copyWith({bool? read}) =>
      AppNotification(id: id, kind: kind, title: title, body: body, image: image, data: data, read: read ?? this.read, createdAt: createdAt);

  factory AppNotification.fromJson(Map<String, dynamic> j) => AppNotification(
        id: asInt(j['id']),
        kind: asString(j['kind']),
        title: asString(j['title']),
        body: asString(j['body']),
        image: brandAsset(asString(j['image'])),
        data: asMap(j['data']),
        read: j['read'] == true,
        createdAt: parseDate(j['created_at']) ?? DateTime.now(),
      );
}

String? _brandOrNull(String? path) => path == null ? null : brandAsset(path);
