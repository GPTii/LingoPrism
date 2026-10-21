import 'common.dart';

/// One word / punctuation mark of a sentence, with its reading from the server (never generated on the device).
class SentenceToken {
  const SentenceToken({required this.text, this.pinyin = '', this.zhuyin = '', this.punct = false, this.blank = false});

  final String text;
  final String pinyin;
  final String zhuyin;
  final bool punct;
  final bool blank;

  factory SentenceToken.fromJson(Map<String, dynamic> j) => SentenceToken(
        text: asString(j['t']),
        pinyin: asString(j['p']),
        zhuyin: asString(j['z']),
        punct: j['x'] == 1 || j['x'] == true,
        blank: j['blank'] == 1 || j['blank'] == true,
      );
}

List<SentenceToken> parseTokens(dynamic v) => asMapList(v).map(SentenceToken.fromJson).toList();

class SentenceSource {
  const SentenceSource({required this.name, this.id = '', this.url = '', this.license = ''});

  final String name;
  final String id;
  final String url;
  final String license;

  String get label => url.isEmpty ? name : 'Câu #$id · $name · $license';

  factory SentenceSource.fromJson(Map<String, dynamic> j) => SentenceSource(
      name: asString(j['name']), id: asString(j['id']), url: asString(j['url']), license: asString(j['license']));
}

class SentenceTranslation {
  const SentenceTranslation({required this.language, required this.text});

  final String language; // vi | en
  final String text;

  static SentenceTranslation? fromJson(dynamic v) {
    final j = asMap(v);
    if (j.isEmpty) return null;
    return SentenceTranslation(language: asString(j['language']), text: asString(j['text']));
  }
}

class Sentence {
  Sentence({
    required this.id,
    required this.language,
    required this.text,
    required this.tokens,
    this.targetTokens = const [],
    this.ttsLocale = '',
    this.translation,
    required this.source,
  });

  final int id;
  final String language; // vi | en | zh-Hans | zh-Hant
  final String text;
  final List<SentenceToken> tokens;
  final List<int> targetTokens;
  final String ttsLocale;
  final SentenceTranslation? translation;
  final SentenceSource source;

  factory Sentence.fromJson(Map<String, dynamic> j) => Sentence(
        id: asInt(j['id']),
        language: asString(j['language']),
        text: asString(j['text']),
        tokens: parseTokens(j['tokens']),
        targetTokens: (j['target_tokens'] as List? ?? const []).map((e) => asInt(e)).toList(),
        ttsLocale: asString(j['tts_locale']),
        translation: SentenceTranslation.fromJson(j['translation']),
        source: SentenceSource.fromJson(asMap(j['source'])),
      );
}

/// Exercise types: arrange | listen (tiles), fill (choose the missing word), meaning (choose the translation).
class SentenceExercise {
  SentenceExercise({
    required this.id,
    required this.type,
    required this.wordText,
    this.tiles = const [],
    this.joiner = ' ',
    this.prompt,
    this.ttsText = '',
    this.ttsLocale = '',
    this.tokens = const [],
    this.options = const [],
    this.sentence,
  });

  final int id;
  final String type;
  final String wordText;
  final List<SentenceToken> tiles;
  final String joiner;
  final SentenceTranslation? prompt;
  final String ttsText;
  final String ttsLocale;
  final List<SentenceToken> tokens;
  final List<String> options;
  final Sentence? sentence;

  bool get isTiles => type == 'arrange' || type == 'listen';

  factory SentenceExercise.fromJson(Map<String, dynamic> j) {
    final tts = asMap(j['tts']);
    return SentenceExercise(
      id: asInt(j['id']),
      type: asString(j['type']),
      wordText: asString(asMap(j['word'])['text']),
      tiles: parseTokens(j['tiles']),
      joiner: asString(j['joiner'], ' '),
      prompt: SentenceTranslation.fromJson(j['prompt']),
      ttsText: asString(tts['text']),
      ttsLocale: asString(tts['locale']),
      tokens: parseTokens(j['tokens']),
      options: (j['options'] as List? ?? const []).map((e) => e.toString()).toList(),
      sentence: j['sentence'] is Map ? Sentence.fromJson(asMap(j['sentence'])) : null,
    );
  }
}

class SentenceLesson {
  SentenceLesson({required this.language, required this.scope, required this.exercises});

  final String language;
  final String scope; // topic | my_words | all
  final List<SentenceExercise> exercises;

  factory SentenceLesson.fromJson(Map<String, dynamic> j) => SentenceLesson(
        language: asString(j['language']),
        scope: asString(j['scope']),
        exercises: asMapList(j['exercises']).map(SentenceExercise.fromJson).toList(),
      );
}

class SentenceCheck {
  SentenceCheck({required this.correct, required this.xp, this.answer, required this.sentence});

  final bool correct;
  final int xp;
  final String? answer;
  final Sentence sentence;

  factory SentenceCheck.fromJson(Map<String, dynamic> j) => SentenceCheck(
        correct: j['correct'] == true,
        xp: asInt(j['xp']),
        answer: j['answer']?.toString(),
        sentence: Sentence.fromJson(asMap(j['sentence'])),
      );
}
