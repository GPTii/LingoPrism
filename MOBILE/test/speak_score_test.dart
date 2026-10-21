import 'package:flutter_test/flutter_test.dart';
import 'package:lingoprism/app/core/widgets/speak_check.dart';

/// Same cases as the web's check of FE/src/lib/pronounce.ts, so both apps score alike.
void main() {
  final cases = <(String, List<String>, String, String)>[
    ('apple', ['Apple'], 'en', 'right'),
    ('apple', ['able', 'apple pie'], 'en', 'right'),
    ('elephant', ['elegant'], 'en', 'close'),
    ('cat', ['dog'], 'en', 'wrong'),
    ('买', ['卖'], 'zh-Hans', 'wrong'), // a wrong tone heard as another character
    ('苹果', ['苹果。'], 'zh-Hans', 'right'),
    ('电脑', ['电老'], 'zh-Hans', 'close'),
    ('quả táo', ['Quả táo'], 'vi', 'right'),
    ('bà', ['ba'], 'vi', 'close'), // right syllable, wrong tone mark
  ];
  for (final (want, heard, lang, verdict) in cases) {
    test('$want ← ${heard.join('|')} is $verdict', () {
      final s = scoreSpeech(want, heard, lang);
      expect(s.verdict, verdict);
    });
  }

  test('the part heard wrong is marked', () {
    final s = scoreSpeech('bà', ['ba'], 'vi');
    expect(s.units.where((u) => !u.$2).map((u) => u.$1), ['à']);
  });
}
