import 'common.dart';
import 'vocab.dart';

/// One of the 4 levels of the learning path (BE apps/learning/levels.py).
class LevelRow {
  LevelRow({
    required this.level,
    required this.name,
    required this.description,
    required this.total,
    required this.started,
    required this.mastered,
    required this.percent,
    required this.unlocked,
    required this.current,
    required this.needed,
  });

  final int level;
  final String name;
  final String description;
  final int total;
  final int started;
  final int mastered;
  final int percent;
  final bool unlocked;
  final bool current;
  final int needed;

  factory LevelRow.fromJson(Map<String, dynamic> j) => LevelRow(
        level: asInt(j['level']),
        name: asString(j['name']),
        description: asString(j['description']),
        total: asInt(j['total']),
        started: asInt(j['started']),
        mastered: asInt(j['mastered']),
        percent: asInt(j['percent']),
        unlocked: j['unlocked'] == true,
        current: j['current'] == true,
        needed: asInt(j['needed']),
      );
}

class LevelProgress {
  LevelProgress({required this.language, required this.current, required this.unlockPercent,
      required this.testSize, required this.testPass, required this.levels});

  final String language;
  final int current;
  final int unlockPercent;
  final int testSize;
  final int testPass;
  final List<LevelRow> levels;

  factory LevelProgress.fromJson(Map<String, dynamic> j) {
    final test = asMap(j['test']);
    return LevelProgress(
      language: asString(j['language']),
      current: asInt(j['current'], 1),
      unlockPercent: asInt(j['unlock_percent'], 70),
      testSize: asInt(test['size'], 10),
      testPass: asInt(test['pass'], 8),
      levels: asMapList(j['levels']).map(LevelRow.fromJson).toList(),
    );
  }
}

class LevelTestQuestion {
  LevelTestQuestion({required this.options, this.word, this.audio, this.emoji = ''});

  final List<String> options;
  final TargetText? word; // "what does this word mean?"
  final TargetText? audio; // children: listen, pick the written word
  final String emoji;

  factory LevelTestQuestion.fromJson(Map<String, dynamic> j) {
    final p = asMap(j['prompt']);
    return LevelTestQuestion(
      options: (j['options'] as List? ?? const []).map((e) => e.toString()).toList(),
      word: p['word'] is Map ? TargetText.fromJson(asMap(p['word'])) : null,
      audio: p['audio'] is Map ? TargetText.fromJson(asMap(p['audio'])) : null,
      emoji: asString(p['emoji']),
    );
  }
}

class LevelTest {
  LevelTest({required this.level, required this.pass, required this.token, required this.questions});

  final int level;
  final int pass;
  final String token;
  final List<LevelTestQuestion> questions;

  factory LevelTest.fromJson(Map<String, dynamic> j) => LevelTest(
        level: asInt(j['level']),
        pass: asInt(j['pass'], 8),
        token: asString(j['token']),
        questions: asMapList(j['questions']).map(LevelTestQuestion.fromJson).toList(),
      );
}

class LevelTestResult {
  LevelTestResult({required this.score, required this.total, required this.passed, this.unlocked});

  final int score;
  final int total;
  final bool passed;
  final int? unlocked;

  factory LevelTestResult.fromJson(Map<String, dynamic> j) => LevelTestResult(
        score: asInt(j['score']),
        total: asInt(j['total']),
        passed: j['passed'] == true,
        unlocked: j['unlocked'] == null ? null : asInt(j['unlocked']),
      );
}
