import '../../../core/utils/brand_assets.dart';

/// Small JSON helpers shared by the API models.
DateTime? parseDate(dynamic v) => v == null ? null : DateTime.tryParse(v.toString())?.toLocal();

int asInt(dynamic v, [int fallback = 0]) {
  if (v is int) return v;
  if (v is num) return v.toInt();
  return int.tryParse(v?.toString() ?? '') ?? fallback;
}

double asDouble(dynamic v, [double fallback = 0]) {
  if (v is num) return v.toDouble();
  return double.tryParse(v?.toString() ?? '') ?? fallback;
}

String asString(dynamic v, [String fallback = '']) => v == null ? fallback : v.toString();

Map<String, dynamic> asMap(dynamic v) => v is Map ? Map<String, dynamic>.from(v) : <String, dynamic>{};

List<Map<String, dynamic>> asMapList(dynamic v) =>
    v is List ? v.map((e) => Map<String, dynamic>.from(e as Map)).toList() : <Map<String, dynamic>>[];

class Author {
  Author({required this.id, required this.displayName, this.avatar, this.publicId = '', this.mascot});

  final int id;
  final String displayName;
  final String? avatar;

  /// the 8-digit ID people find each other by
  final String publicId;

  /// their Prismo (null: plain)
  final MascotLook? mascot;

  static const String defaultAvatar = 'assets/brand/avatar/avatar_1.png';

  String get avatarOrDefault => (avatar == null || avatar!.isEmpty) ? defaultAvatar : avatar!;

  factory Author.fromJson(Map<String, dynamic> j) =>
      Author(id: asInt(j['id']), displayName: asString(j['display_name'], 'Người học LingoPrism'), avatar: _brandOrNull(j['avatar'] as String?),
          publicId: asString(j['public_id']), mascot: MascotLook.fromJson(j['mascot']));
}

String? _brandOrNull(String? path) => path == null ? null : brandAsset(path);

/// What someone's Prismo wears (one outfit code per slot, '' for nothing) and whether it stands in for their photo.
class MascotLook {
  const MascotLook({this.name = 'Prismo', this.asAvatar = false, this.background = '', this.hat = '', this.glasses = '',
      this.neck = '', this.hand = ''});

  final String name;
  final bool asAvatar;
  final String background;
  final String hat;
  final String glasses;
  final String neck;
  final String hand;

  static const slots = ['background', 'hat', 'glasses', 'neck', 'hand'];

  /// the layers in front of Prismo, back to front
  List<String> get front => [neck, hand, glasses, hat].where((c) => c.isNotEmpty).toList();

  String slot(String s) => switch (s) { 'background' => background, 'hat' => hat, 'glasses' => glasses, 'neck' => neck, _ => hand };

  MascotLook wearing(String slot, String code) => MascotLook(
        name: name,
        asAvatar: asAvatar,
        background: slot == 'background' ? code : background,
        hat: slot == 'hat' ? code : hat,
        glasses: slot == 'glasses' ? code : glasses,
        neck: slot == 'neck' ? code : neck,
        hand: slot == 'hand' ? code : hand,
      );

  static MascotLook? fromJson(dynamic v) {
    if (v is! Map) return null;
    final j = Map<String, dynamic>.from(v);
    return MascotLook(
      name: asString(j['name'], 'Prismo'),
      asAvatar: j['as_avatar'] == true,
      background: asString(j['background']),
      hat: asString(j['hat']),
      glasses: asString(j['glasses']),
      neck: asString(j['neck']),
      hand: asString(j['hand']),
    );
  }

  Map<String, dynamic> toJson() =>
      {'name': name, 'as_avatar': asAvatar, 'background': background, 'hat': hat, 'glasses': glasses, 'neck': neck, 'hand': hand};
}

String outfitAsset(String code) => 'assets/outfits/$code.svg';
