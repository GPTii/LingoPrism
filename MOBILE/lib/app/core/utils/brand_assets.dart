/// LingoPrism's own artwork (assets/brand, drawn by MOBILE/tool/brand_assets.py – same design as the web).
///
/// [brandAsset] also translates the asset paths of the earlier app ("assets/images/...") that may still be stored on
/// a server (avatar presets, badges, shop items, notifications) to the new artwork.
class BrandAssets {
  BrandAssets._();

  static const String _m = 'assets/brand/mascot';
  static const String happy = '$_m/prismo_happy.png';
  static const String wink = '$_m/prismo_wink.png';
  static const String love = '$_m/prismo_love.png';
  static const String hello = '$_m/prismo_hello.png';
  static const String celebrate = '$_m/prismo_celebrate.png';
  static const String party = '$_m/prismo_party.png';
  static const String gift = '$_m/prismo_gift.png';
  static const String think = '$_m/prismo_think.png';
  static const String reminder = '$_m/prismo_reminder.png';
  static const String sad = '$_m/prismo_sad.png';
  static const String sorry = '$_m/prismo_sorry.png';
  static const String sleepy = '$_m/prismo_sleepy.png';
  static const String camera = '$_m/prismo_camera.png';
  static const String explore = '$_m/prismo_explore.png';
  static const String graduate = '$_m/prismo_graduate.png';
  static const String ok = '$_m/prismo_ok.png';
  static const String wow = '$_m/prismo_wow.png';
  static const String group = '$_m/prismo_group.png';

  /// Avatar presets: Prismo in six colours.
  static const List<String> avatars = [
    'assets/brand/avatar/avatar_1.png',
    'assets/brand/avatar/avatar_2.png',
    'assets/brand/avatar/avatar_3.png',
    'assets/brand/avatar/avatar_4.png',
    'assets/brand/avatar/avatar_5.png',
    'assets/brand/avatar/avatar_6.png',
  ];
  static const String defaultAvatar = 'assets/brand/avatar/avatar_1.png';

  static const String xp = 'assets/brand/icons/xp.png';
  static const String xpDouble = 'assets/brand/icons/xp_x2.png';
  static const String xpPotion = 'assets/brand/icons/xp_potion.png';
  static const String scale = 'assets/brand/icons/scale.png';
  static const String gem = 'assets/brand/icons/gem.png';
  static const String bell = 'assets/brand/icons/bell.png';
  static const String streakFreeze = 'assets/brand/icons/streak_freeze.png';
  static String streak(int level) => 'assets/brand/icons/streak_${level.clamp(0, 6)}.png';

  /// League tier 1..10 (lowest first).
  static String rank(int tier) => 'assets/brand/rank/rank_${tier.clamp(1, 10)}.png';
  static const String rankLocked = 'assets/brand/rank/rank_locked.png';

  /// Group icons 1..5.
  static String groupIcon(int i) => 'assets/brand/group/group_${i.clamp(1, 5)}.png';
  static const String groupDefault = 'assets/brand/group/group_default.png';
  static const List<String> groupIcons = [
    'assets/brand/group/group_1.png',
    'assets/brand/group/group_2.png',
    'assets/brand/group/group_3.png',
    'assets/brand/group/group_4.png',
    'assets/brand/group/group_5.png',
  ];

  static const String logo = 'assets/brand/logo.png';

  static const Map<String, String> _mascot = {
    'chim_vui1': 'assets/brand/avatar/avatar_1.png',
    'chim_ok': ok,
    'chim_vui': 'assets/brand/avatar/avatar_4.png',
    'chim_mung': celebrate,
    'chim_thich': love,
    'chim_yeu': love,
    'chim_xinchao': hello,
    'chim_chaomung': hello,
    'chim_chienthang': celebrate,
    'chim_yes': celebrate,
    'chim_thoibong': party,
    'chim_moqua': gift,
    'chim_camqua': wink,
    'chim_camon': wink,
    'chim_nhachoc': reminder,
    'chim_hoi': think,
    'chim_xinloi': sorry,
    'chim_chupanh': camera,
    'chim_totnghiep': graduate,
  };

  /// Old path (earlier app) → new artwork; any other path is returned unchanged.
  static String resolve(String path) {
    if (!path.startsWith('assets/images/')) return path;
    final name = path.split('/').last.replaceAll('.png', '');
    if (path.contains('/chimcanhcut/')) {
      final exact = _mascot[name];
      if (exact != null) return exact;
      final base = name.replaceAll(RegExp(r'\d+$'), '');
      if (base == 'chim_buon') return sad;
      if (base == 'chim_ngu') return sleepy;
      if (base == 'chim_hocnhom') return group;
      if (base == 'chim_muadong') return explore;
      if (base == 'chim_lolang') return think;
      return happy;
    }
    final streakMatch = RegExp(r'^streak(\d)$').firstMatch(name);
    if (streakMatch != null) return streak(int.parse(streakMatch.group(1)!));
    if (name == 'streakbang') return streakFreeze;
    final rankMatch = RegExp(r'^rank(\d+)$').firstMatch(name);
    if (rankMatch != null) return rank(int.parse(rankMatch.group(1)!));
    final groupMatch = RegExp(r'^nhom(\d)$').firstMatch(name);
    if (groupMatch != null) return groupIcon(int.parse(groupMatch.group(1)!));
    return switch (name) {
      'XP' => xp,
      'XPx2' => xpDouble,
      'binhcucquang' => xpPotion,
      'vay' => scale,
      'ngoc' => gem,
      'thongbao' => bell,
      'nhom_default' => groupDefault,
      'logo' => logo,
      _ => happy,
    };
  }
}

/// Shorthand used by widgets that show an asset path coming from the API.
String brandAsset(String path) => BrandAssets.resolve(path);
