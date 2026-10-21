import 'common.dart';

class LitUnit {
  const LitUnit({required this.kind, required this.code, required this.label, required this.sound, this.symbol = ''});

  final String kind; // am | thanh | van
  final String code;
  final String label;
  final String sound;
  final String symbol;

  /// What to show big: the letters, or the tone mark.
  String get display => kind == 'thanh' ? (symbol.isEmpty ? '–' : symbol) : code;

  /// What to say aloud when tapped.
  String get spoken => kind == 'thanh' ? label : sound.split(' – ').last;

  factory LitUnit.fromJson(Map<String, dynamic> j) => LitUnit(
      kind: asString(j['kind']), code: asString(j['code']), label: asString(j['label']),
      sound: asString(j['sound']), symbol: asString(j['symbol']));
}

class LitLessonInfo {
  LitLessonInfo({required this.n, required this.title, required this.review, required this.units,
      required this.status, required this.stars});

  final int n;
  final String title;
  final bool review;
  final List<LitUnit> units;
  final String status; // done | open | locked
  final int stars;

  bool get locked => status == 'locked';

  factory LitLessonInfo.fromJson(Map<String, dynamic> j) => LitLessonInfo(
        n: asInt(j['n']),
        title: asString(j['title']),
        review: j['review'] == true,
        units: asMapList(j['units']).map(LitUnit.fromJson).toList(),
        status: asString(j['status'], 'locked'),
        stars: asInt(j['stars']),
      );
}

class SpellExample {
  SpellExample({required this.text, required this.spell});

  final String text;
  final List<String> spell;

  factory SpellExample.fromJson(Map<String, dynamic> j) =>
      SpellExample(text: asString(j['text']), spell: _strings(j['spell']));
}

List<String> _strings(dynamic v) => (v as List? ?? const []).map((e) => e.toString()).toList();

class LitWord {
  LitWord({required this.text, required this.emoji, this.image});

  final String text;
  final String emoji;
  final String? image;
}

class LitIntro {
  LitIntro({required this.unit, required this.examples, required this.words, required this.rhymeSpell});

  final LitUnit unit;
  final List<SpellExample> examples;
  final List<LitWord> words;
  final List<String> rhymeSpell;

  factory LitIntro.fromJson(Map<String, dynamic> j) => LitIntro(
        unit: LitUnit.fromJson(asMap(j['unit'])),
        examples: asMapList(j['examples']).map(SpellExample.fromJson).toList(),
        words: asMapList(j['words']).map((w) => LitWord(text: asString(w['text']), emoji: asString(w['emoji']), image: w['image'] as String?)).toList(),
        rhymeSpell: _strings(j['rhyme_spell']),
      );
}

class LitTone {
  LitTone({required this.code, required this.label, required this.symbol});

  final String code;
  final String label;
  final String symbol;
}

/// listen_choose | find_unit | build | rule | dictation | sentence
class LitExercise {
  LitExercise({
    required this.type,
    required this.token,
    required this.ttsText,
    this.options = const [],
    this.question = '',
    this.syllable = '',
    this.onsets = const [],
    this.rhymes = const [],
    this.tones = const [],
    this.pattern = '',
    this.emoji = '',
    this.image,
    this.syllables = 0,
    this.sourceLabel = '',
    this.sourceUrl = '',
  });

  final String type;
  final String token;
  final String ttsText;
  final List<String> options;
  final String question;
  final String syllable;
  final List<String> onsets;
  final List<String> rhymes;
  final List<LitTone> tones;
  final String pattern;
  final String emoji;
  final String? image;
  final int syllables;
  final String sourceLabel;
  final String sourceUrl;

  factory LitExercise.fromJson(Map<String, dynamic> j) {
    final src = asMap(j['source']);
    return LitExercise(
      type: asString(j['type']),
      token: asString(j['token']),
      ttsText: asString(asMap(j['tts'])['text']),
      options: _strings(j['options']),
      question: asString(j['question']),
      syllable: asString(j['syllable']),
      onsets: _strings(j['onsets']),
      rhymes: _strings(j['rhymes']),
      tones: asMapList(j['tones'])
          .map((t) => LitTone(code: asString(t['code']), label: asString(t['label']), symbol: asString(t['symbol'])))
          .toList(),
      pattern: asString(j['pattern']),
      emoji: asString(j['emoji']),
      image: j['image'] as String?,
      syllables: asInt(j['syllables']),
      sourceLabel: src.isEmpty ? '' : 'Câu #${src['id']} · Tatoeba · ${src['license']}',
      sourceUrl: asString(src['url']),
    );
  }
}

class LitLesson {
  LitLesson({required this.n, required this.title, required this.session, required this.intro, required this.exercises});

  final int n;
  final String title;
  final String session;
  final List<LitIntro> intro;
  final List<LitExercise> exercises;

  factory LitLesson.fromJson(Map<String, dynamic> j) => LitLesson(
        n: asInt(j['n']),
        title: asString(j['title']),
        session: asString(j['session']),
        intro: asMapList(j['intro']).map(LitIntro.fromJson).toList(),
        exercises: asMapList(j['exercises']).map(LitExercise.fromJson).toList(),
      );
}

class LitDiff {
  LitDiff({required this.expected, required this.given, required this.ok, this.hint = ''});

  final String expected;
  final String given;
  final bool ok;
  final String hint;
}

class LitCheck {
  LitCheck({required this.correct, required this.xp, required this.expected, this.word = '', this.spell = const [], this.diff = const []});

  final bool correct;
  final int xp;
  final String expected;
  final String word;
  final List<String> spell;
  final List<LitDiff> diff;

  factory LitCheck.fromJson(Map<String, dynamic> j) => LitCheck(
        correct: j['correct'] == true,
        xp: asInt(j['xp']),
        expected: asString(j['expected']),
        word: asString(j['word']),
        spell: _strings(j['spell']),
        diff: asMapList(j['diff'])
            .map((d) => LitDiff(expected: asString(d['expected']), given: asString(d['given']), ok: d['ok'] == true, hint: asString(d['hint'])))
            .toList(),
      );
}

class LitFinish {
  LitFinish({required this.correct, required this.total, required this.stars, required this.passed, required this.nextUnlocked});

  final int correct;
  final int total;
  final int stars;
  final bool passed;
  final bool nextUnlocked;

  factory LitFinish.fromJson(Map<String, dynamic> j) => LitFinish(
      correct: asInt(j['correct_first_try']), total: asInt(j['total']), stars: asInt(j['stars']),
      passed: j['passed'] == true, nextUnlocked: j['next_unlocked'] == true);
}
