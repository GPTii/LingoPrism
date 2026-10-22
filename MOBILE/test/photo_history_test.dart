import 'package:flutter_test/flutter_test.dart';
import 'package:lingoprism/app/data/models/api/learning_extra.dart';
import 'package:lingoprism/app/modules/photo_history/photo_history_module.dart';

Map<String, dynamic> _card(String text, String vi) => {
      'id': text.hashCode,
      'slug': text,
      'meaning_vi': vi,
      'target': {'id': 1, 'language': 'zh-Hans', 'text': text, 'tts_locale': 'zh-CN', 'pinyin': ''},
    };

void main() {
  test('a photo groups one word per object, keeps corrections and drops "not an object"', () {
    final d = DetectionResult.fromJson({
      'id': 5,
      'model': 'yolov8m',
      'device': 'server',
      'image': null,
      'created_at': '2026-10-22T10:00:00+00:00',
      'confirmed': true,
      'items': [
        {'id': 1, 'label': 'Apple', 'bbox': [0, 0, 0.5, 0.5], 'card': _card('苹果', 'quả táo'), 'selected': false},
        // the model said apple, the learner said watermelon: the watermelon word is what was saved
        {'id': 2, 'label': 'Apple', 'bbox': [0.5, 0, 1, 0.5], 'card': _card('苹果', 'quả táo'), 'selected': true,
            'feedback': 'wrong', 'corrected_label': 'Watermelon', 'corrected_card': _card('西瓜', 'dưa hấu')},
        {'id': 3, 'label': 'Watermelon', 'bbox': [0, 0.5, 0.5, 1], 'card': _card('西瓜', 'dưa hấu'), 'selected': false},
        {'id': 4, 'label': 'Cup', 'bbox': [0.5, 0.5, 1, 1], 'feedback': 'wrong', 'corrected_label': ''}, // not an object
      ],
    });
    expect(d.confirmed, isTrue);
    expect(d.createdAt, isNotNull);
    final words = wordsOf(d);
    expect(words.map((w) => w.label), ['Watermelon', 'Apple']); // saved first, the cup is gone
    expect(words.first.count, 2);
    expect(words.first.saved, isTrue);
    expect(words.first.card!.target!.text, '西瓜');
    expect(words.last.saved, isFalse);
  });

  test('times read like the feed', () {
    expect(shotTime(DateTime.now().subtract(const Duration(minutes: 5))), '5 phút trước');
    expect(shotTime(DateTime(2026, 1, 2)), '02/01/2026');
    expect(shotTime(null), '');
  });
}
