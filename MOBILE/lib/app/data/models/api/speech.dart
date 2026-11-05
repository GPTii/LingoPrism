import 'common.dart';

/// Phone-level pronunciation scoring (BE apps.speech, docs/thiet-ke-luyen-noi.md).
class SpeechPhone {
  SpeechPhone(this.expected, this.heard, this.status, this.score);
  final String expected;
  final String? heard;
  final String status; // ok | close | wrong | missing
  final int score;

  factory SpeechPhone.fromJson(Map<String, dynamic> j) =>
      SpeechPhone(asString(j['expected']), j['heard'] == null ? null : asString(j['heard']), asString(j['status']), asInt(j['score']));
}

class SpeechTone {
  SpeechTone(this.expected, this.heard, this.status);
  final String expected; // zh: 1–4, vi: ngang / huyền / sắc / hỏi / ngã / nặng
  final String heard;
  final String status; // ok | close | wrong

  static SpeechTone? fromJson(dynamic j) {
    final m = asMap(j);
    return m.isEmpty ? null : SpeechTone(asString(m['expected']), asString(m['heard']), asString(m['status']));
  }
}

class SpeechUnit {
  SpeechUnit({required this.text, required this.reading, required this.score, required this.status, this.tone, this.phones = const []});
  final String text;
  final String reading;
  final int score;
  final String status; // right | close | wrong
  final SpeechTone? tone;
  final List<SpeechPhone> phones;

  factory SpeechUnit.fromJson(Map<String, dynamic> j) => SpeechUnit(
        text: asString(j['text']),
        reading: asString(j['reading']),
        score: asInt(j['score']),
        status: asString(j['status']),
        tone: SpeechTone.fromJson(j['tone']),
        phones: asMapList(j['phones']).map(SpeechPhone.fromJson).toList(),
      );
}

class SpeechError {
  SpeechError({required this.code, required this.unit, required this.expected, this.heard, required this.tip, required this.major});
  final String code;
  final int unit;
  final String expected;
  final String? heard;
  final String tip;
  final bool major;

  factory SpeechError.fromJson(Map<String, dynamic> j) => SpeechError(
        code: asString(j['code']),
        unit: asInt(j['unit'], -1),
        expected: asString(j['expected']),
        heard: j['heard'] == null ? null : asString(j['heard']),
        tip: asString(j['tip']),
        major: asString(j['severity']) != 'minor',
      );
}

class PronunciationResult {
  PronunciationResult({
    required this.score,
    required this.verdict,
    required this.phoneScore,
    this.toneScore,
    required this.completeness,
    required this.units,
    required this.errors,
    required this.heardIpa,
  });

  final int score;
  final String verdict; // right | close | wrong
  final int phoneScore;
  final int? toneScore;
  final int completeness;
  final List<SpeechUnit> units;
  final List<SpeechError> errors;
  final String heardIpa;

  factory PronunciationResult.fromJson(Map<String, dynamic> j) => PronunciationResult(
        score: asInt(j['score']),
        verdict: asString(j['verdict']),
        phoneScore: asInt(j['phone_score']),
        toneScore: j['tone_score'] == null ? null : asInt(j['tone_score']),
        completeness: asInt(j['completeness']),
        units: asMapList(j['units']).map(SpeechUnit.fromJson).toList(),
        errors: asMapList(j['errors']).map(SpeechError.fromJson).toList(),
        heardIpa: asString(j['heard_ipa']),
      );
}

class WeakSound {
  WeakSound(this.code, this.count, this.expected, this.heard, this.tip);
  final String code;
  final int count;
  final String expected;
  final String? heard;
  final String tip;
}

class SpeechProgress {
  SpeechProgress({required this.attempts, this.average7d, required this.byDay, required this.weak, required this.recent});
  final int attempts;
  final int? average7d;
  final List<(String, int, int)> byDay; // date, average, count
  final List<WeakSound> weak;
  final List<(String, int)> recent; // text, score

  factory SpeechProgress.fromJson(Map<String, dynamic> j) => SpeechProgress(
        attempts: asInt(j['attempts']),
        average7d: j['average_7d'] == null ? null : asInt(j['average_7d']),
        byDay: [for (final d in asMapList(j['by_day'])) (asString(d['date']), asInt(d['average']), asInt(d['count']))],
        weak: [
          for (final w in asMapList(j['weak_sounds']))
            WeakSound(asString(w['code']), asInt(w['count']), asString(w['expected']), w['heard'] == null ? null : asString(w['heard']),
                asString(w['tip']))
        ],
        recent: [for (final r in asMapList(j['recent'])) (asString(r['text']), asInt(r['score']))],
      );
}
