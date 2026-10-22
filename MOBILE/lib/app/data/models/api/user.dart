import '../../../core/utils/brand_assets.dart';
import 'common.dart';

class UserGoal {
  UserGoal({this.dailyNewTarget = 10, this.dailyReviewTarget = 20, this.remindMorning, this.remindEvening, this.smartRemind = true});

  final int dailyNewTarget;
  final int dailyReviewTarget;
  final String? remindMorning;
  final String? remindEvening;
  final bool smartRemind;

  factory UserGoal.fromJson(Map<String, dynamic> j) => UserGoal(
        dailyNewTarget: asInt(j['daily_new_target'], 10),
        dailyReviewTarget: asInt(j['daily_review_target'], 20),
        remindMorning: j['remind_morning'] as String?,
        remindEvening: j['remind_evening'] as String?,
        smartRemind: j['smart_remind'] != false,
      );
}

class AppUser {
  AppUser({
    required this.id,
    this.publicId = '',
    required this.email,
    required this.displayName,
    this.avatar,
    this.avatarPreset = '',
    this.bio = '',
    this.role = 'learner',
    this.learnerType = 'adult',
    this.learningLanguages = const [],
    this.activeLanguage = 'en',
    this.zhScript = 'hans',
    this.showZhuyin = false,
    this.birthDate,
    this.gender = '',
    this.purpose = '',
    this.dailyMinutes = 10,
    this.onboardingCompleted = false,
    this.scales = 0,
    this.gems = 0,
    this.goal,
  });

  final int id;

  /// 8 digits, "ID của tôi" – friends find each other by it
  final String publicId;
  final String email;
  final String displayName;
  final String? avatar;
  final String avatarPreset;
  final String bio;
  final String role;
  final String learnerType;
  final List<String> learningLanguages;
  final String activeLanguage;
  final String zhScript;
  final bool showZhuyin;
  final DateTime? birthDate;
  final String gender;
  final String purpose;
  final int dailyMinutes;
  final bool onboardingCompleted;
  final int scales;
  final int gems;
  final UserGoal? goal;

  static const String defaultAvatar = 'assets/brand/avatar/avatar_1.png';

  bool get isKid => learnerType == 'kid';
  bool get isStaff => role == 'admin' || role == 'staff';
  String get avatarOrDefault {
    if (avatar != null && avatar!.isNotEmpty) return avatar!;
    return avatarPreset.isNotEmpty ? avatarPreset : defaultAvatar;
  }

  /// Language code of the translations being learned (vi | en | zh-Hans | zh-Hant).
  String get targetCode => activeLanguage == 'zh' ? (zhScript == 'hant' ? 'zh-Hant' : 'zh-Hans') : activeLanguage;

  String get languageLabel {
    switch (activeLanguage) {
      case 'zh':
        return zhScript == 'hant' ? 'Tiếng Trung phồn thể' : 'Tiếng Trung giản thể';
      case 'vi':
        return 'Tiếng Việt';
      default:
        return 'Tiếng Anh';
    }
  }

  factory AppUser.fromJson(Map<String, dynamic> j) => AppUser(
        id: asInt(j['id']),
        publicId: asString(j['public_id']),
        email: asString(j['email']),
        displayName: asString(j['display_name']),
        avatar: _brandOrNull(j['avatar'] as String?),
        avatarPreset: brandAsset(asString(j['avatar_preset'])),
        bio: asString(j['bio']),
        role: asString(j['role'], 'learner'),
        learnerType: asString(j['learner_type'], 'adult'),
        learningLanguages: (j['learning_languages'] as List? ?? const []).map((e) => e.toString()).toList(),
        activeLanguage: asString(j['active_language'], 'en'),
        zhScript: asString(j['zh_script'], 'hans'),
        showZhuyin: j['show_zhuyin'] == true,
        birthDate: parseDate(j['birth_date']),
        gender: asString(j['gender']),
        purpose: asString(j['purpose']),
        dailyMinutes: asInt(j['daily_minutes'], 10),
        onboardingCompleted: j['onboarding_completed'] == true,
        scales: asInt(j['scales_balance']),
        gems: asInt(j['gems_balance']),
        goal: j['goal'] is Map ? UserGoal.fromJson(asMap(j['goal'])) : null,
      );

  Map<String, dynamic> toJson() => {
        'public_id': publicId,
        'id': id,
        'email': email,
        'display_name': displayName,
        'avatar': avatar,
        'avatar_preset': avatarPreset,
        'bio': bio,
        'role': role,
        'learner_type': learnerType,
        'learning_languages': learningLanguages,
        'active_language': activeLanguage,
        'zh_script': zhScript,
        'show_zhuyin': showZhuyin,
        'birth_date': birthDate?.toIso8601String().substring(0, 10),
        'gender': gender,
        'purpose': purpose,
        'daily_minutes': dailyMinutes,
        'onboarding_completed': onboardingCompleted,
        'scales_balance': scales,
        'gems_balance': gems,
        if (goal != null)
          'goal': {
            'daily_new_target': goal!.dailyNewTarget,
            'daily_review_target': goal!.dailyReviewTarget,
            'remind_morning': goal!.remindMorning,
            'remind_evening': goal!.remindEvening,
            'smart_remind': goal!.smartRemind,
          },
      };
}

String? _brandOrNull(String? path) => path == null ? null : brandAsset(path);
