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
  Author({required this.id, required this.displayName, this.avatar});

  final int id;
  final String displayName;
  final String? avatar;

  static const String defaultAvatar = 'assets/brand/avatar/avatar_1.png';

  String get avatarOrDefault => (avatar == null || avatar!.isEmpty) ? defaultAvatar : avatar!;

  factory Author.fromJson(Map<String, dynamic> j) =>
      Author(id: asInt(j['id']), displayName: asString(j['display_name'], 'Người học LingoPrism'), avatar: _brandOrNull(j['avatar'] as String?));
}

String? _brandOrNull(String? path) => path == null ? null : brandAsset(path);
