import 'common.dart';

/// A word in one language as returned by the API (only verified data reaches learners).
class TargetText {
  TargetText({
    required this.id,
    required this.language,
    required this.text,
    required this.ttsLocale,
    this.ipa = '',
    this.pinyin = '',
    this.zhuyin = '',
    this.measureWord = '',
    this.level = '',
    this.regionalDifference = false,
    this.unverified = false,
  });

  final int id;
  final String language; // vi | en | zh-Hans | zh-Hant
  final String text;
  final String ttsLocale; // vi-VN | en-US | zh-CN | zh-TW
  final String ipa;
  final String pinyin;
  final String zhuyin;
  final String measureWord;
  final String level;
  final bool regionalDifference;
  final bool unverified;

  bool get isChinese => language.startsWith('zh');
  bool get isTraditional => language == 'zh-Hant';

  /// Reading line shown under the word (IPA for English, pinyin for Chinese).
  String get reading {
    if (ipa.isNotEmpty) return '/$ipa/';
    return pinyin;
  }

  factory TargetText.fromJson(Map<String, dynamic> j) => TargetText(
        id: asInt(j['id']),
        language: asString(j['language']),
        text: asString(j['text']),
        ttsLocale: asString(j['tts_locale']),
        ipa: asString(j['ipa']),
        pinyin: asString(j['pinyin']),
        zhuyin: asString(j['zhuyin']),
        measureWord: asString(j['measure_word']),
        level: asString(j['level']),
        regionalDifference: j['regional_difference'] == true,
        unverified: j['unverified'] == true,
      );
}

class ExampleSentence {
  ExampleSentence({required this.text, this.transliteration = '', this.translationVi = '', this.translationEn = ''});

  final String text;
  final String transliteration;
  final String translationVi;
  final String translationEn;

  factory ExampleSentence.fromJson(Map<String, dynamic> j) => ExampleSentence(
        text: asString(j['text']),
        transliteration: asString(j['transliteration']),
        translationVi: asString(j['translation_vi']),
        translationEn: asString(j['translation_en']),
      );
}

class PersonalInfo {
  PersonalInfo({required this.id, required this.status, required this.stage, this.dueAt, this.lastReviewedAt});

  final int id;
  final String status; // new | learning | mastered
  final int stage;
  final DateTime? dueAt;
  final DateTime? lastReviewedAt;

  String get statusLabel => {'new': 'chưa học', 'learning': 'đang học', 'mastered': 'đã học'}[status] ?? status;

  factory PersonalInfo.fromJson(Map<String, dynamic> j) => PersonalInfo(
        id: asInt(j['id']),
        status: asString(j['status'], 'new'),
        stage: asInt(j['stage']),
        dueAt: parseDate(j['due_at']),
        lastReviewedAt: parseDate(j['last_reviewed_at']),
      );
}

/// Learner-facing word card (concept + target-language translation + Vietnamese meaning).
class WordCard {
  WordCard({
    required this.id,
    required this.slug,
    this.image,
    this.emoji = '',
    this.level,
    this.partOfSpeech = 'noun',
    this.difficulty = 1,
    this.yoloLabel = '',
    this.target,
    this.meaningVi = '',
    this.english,
    this.examples = const [],
    this.personal,
  });

  final int id;
  final String slug;
  final String? image;
  final String emoji; // picture for children (Unicode emoji)
  final int? level; // 1–4 on the learning path of the active language
  final String partOfSpeech;
  final int difficulty;
  final String yoloLabel;
  final TargetText? target;
  final String meaningVi;
  final String? english;
  final List<ExampleSentence> examples;
  final PersonalInfo? personal;

  String get text => target?.text ?? slug;

  /// Learning Vietnamese (children): the "meaning" is a picture, never an English gloss.
  bool get isVietnameseTarget => target?.language == 'vi';
  bool get saved => personal != null;

  factory WordCard.fromJson(Map<String, dynamic> j) => WordCard(
        id: asInt(j['id']),
        slug: asString(j['slug']),
        image: j['image'] as String?,
        emoji: asString(j['emoji']),
        level: j['level'] == null ? null : asInt(j['level']),
        partOfSpeech: asString(j['part_of_speech'], 'noun'),
        difficulty: asInt(j['difficulty'], 1),
        yoloLabel: asString(j['yolo_label']),
        target: j['target'] is Map ? TargetText.fromJson(asMap(j['target'])) : null,
        meaningVi: asString(j['meaning_vi']),
        english: j['english'] as String?,
        examples: asMapList(j['examples']).map(ExampleSentence.fromJson).toList(),
        personal: j['personal'] is Map ? PersonalInfo.fromJson(asMap(j['personal'])) : null,
      );
}

class Topic {
  Topic({
    required this.id,
    required this.slug,
    required this.nameVi,
    this.nameEn = '',
    this.nameZhHans = '',
    this.nameZhHant = '',
    this.icon = '',
    this.image,
    this.audience = 'all',
    this.isSystem = true,
    this.wordCount = 0,
    this.learnedCount = 0,
    this.savedCount = 0,
  });

  final int id;
  final String slug;
  final String nameVi;
  final String nameEn;
  final String nameZhHans;
  final String nameZhHant;
  final String icon;
  final String? image;
  final String audience;
  final bool isSystem;
  final int wordCount;
  final int learnedCount;
  final int savedCount; // words of this topic in the learner's library

  bool get inLibrary => savedCount > 0 || !isSystem;

  double get progress => wordCount == 0 ? 0 : learnedCount / wordCount;

  String targetName(String activeLanguage, String zhScript) {
    if (activeLanguage == 'zh') return zhScript == 'hant' ? nameZhHant : nameZhHans;
    if (activeLanguage == 'en') return nameEn;
    return '';
  }

  factory Topic.fromJson(Map<String, dynamic> j) => Topic(
        id: asInt(j['id']),
        slug: asString(j['slug']),
        nameVi: asString(j['name_vi']),
        nameEn: asString(j['name_en']),
        nameZhHans: asString(j['name_zh_hans']),
        nameZhHant: asString(j['name_zh_hant']),
        icon: asString(j['icon']),
        image: j['image'] as String?,
        audience: asString(j['audience'], 'all'),
        isSystem: j['is_system'] != false,
        wordCount: asInt(j['word_count']),
        learnedCount: asInt(j['learned_count']),
        savedCount: asInt(j['saved_count']),
      );
}

class LibrarySummary {
  LibrarySummary({this.total = 0, this.newCount = 0, this.learning = 0, this.mastered = 0, this.due = 0});

  final int total;
  final int newCount;
  final int learning;
  final int mastered;
  final int due;

  factory LibrarySummary.fromJson(Map<String, dynamic> j) => LibrarySummary(
        total: asInt(j['total']),
        newCount: asInt(j['new']),
        learning: asInt(j['learning']),
        mastered: asInt(j['mastered']),
        due: asInt(j['due']),
      );
}

/// Questions generated by the server for a study session.
class SessionQuestion {
  SessionQuestion({
    required this.type,
    this.prompt = '',
    this.promptText,
    this.options = const [],
    this.answer = '',
    this.accepted = const [],
    this.back = '',
  });

  /// flashcard | choose_target | choose_meaning | choose_pinyin | type_target | listen_type
  final String type;
  final String prompt; // plain-text prompt (meaning, hanzi…)
  final TargetText? promptText; // word shown/spoken (flashcard front, choose_meaning, listen_type)
  final List<String> options;
  final String answer;
  final List<String> accepted;
  final String back;

  factory SessionQuestion.fromJson(Map<String, dynamic> j) {
    final p = j['prompt'] ?? j['front'] ?? j['audio'];
    return SessionQuestion(
      type: asString(j['type']),
      prompt: p is String ? p : '',
      promptText: p is Map ? TargetText.fromJson(asMap(p)) : null,
      options: (j['options'] as List? ?? const []).map((e) => e.toString()).toList(),
      answer: asString(j['answer']),
      accepted: (j['accepted'] as List? ?? const []).map((e) => e.toString()).toList(),
      back: asString(j['back']),
    );
  }
}

class SessionItem {
  SessionItem({required this.itemId, required this.personalWordId, required this.card, required this.questions, this.answered = false});

  final int itemId;
  final int personalWordId;
  final WordCard card;
  final List<SessionQuestion> questions;
  final bool answered;

  SessionQuestion? question(String type) {
    for (final q in questions) {
      if (q.type == type) return q;
    }
    return null;
  }

  factory SessionItem.fromJson(Map<String, dynamic> j) => SessionItem(
        itemId: asInt(j['item_id']),
        personalWordId: asInt(j['personal_word']),
        card: WordCard.fromJson(asMap(j['card'])),
        questions: asMapList(j['questions']).map(SessionQuestion.fromJson).toList(),
        answered: j['answered'] == true,
      );
}

class StudySession {
  StudySession({required this.id, required this.kind, required this.language, this.script = '', required this.items});

  final int id;
  final String kind; // learn | review | practice
  final String language;
  final String script;
  final List<SessionItem> items;

  factory StudySession.fromJson(Map<String, dynamic> j) => StudySession(
        id: asInt(j['id']),
        kind: asString(j['kind']),
        language: asString(j['language']),
        script: asString(j['script']),
        items: asMapList(j['items']).map(SessionItem.fromJson).toList(),
      );
}

class SessionSummary {
  SessionSummary({this.completed = 0, this.correctFirstTry = 0, this.xp = 0, this.needsMorePractice = const []});

  final int completed;
  final int correctFirstTry;
  final int xp;
  final List<int> needsMorePractice;

  factory SessionSummary.fromJson(Map<String, dynamic> j) => SessionSummary(
        completed: asInt(j['completed_count']),
        correctFirstTry: asInt(j['correct_first_try']),
        xp: asInt(j['xp_earned']),
        needsMorePractice: (j['needs_more_practice'] as List? ?? const []).map((e) => asInt(e)).toList(),
      );
}
