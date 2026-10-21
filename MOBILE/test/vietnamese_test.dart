import 'package:flutter_test/flutter_test.dart';
import 'package:lingoprism/app/core/utils/vietnamese.dart';

void main() {
  test('tone placement matches the server (kiểu cũ)', () {
    expect(applyTone('ba', 'huyen'), 'bà');
    expect(applyTone('hoa', 'huyen'), 'hòa');
    expect(applyTone('thuyen', 'huyen'), 'thuỳen'); // half-typed word: same as the server
    expect(applyTone('thuyên', 'huyen'), 'thuyền');
    expect(applyTone('qua', 'hoi'), 'quả');
    expect(applyTone('gi', 'huyen'), 'gì');
    expect(applyTone('nươc', 'sac'), 'nước');
    expect(applyTone('bà', 'sac'), 'bá');
    expect(applyTone('bá', 'ngang'), 'ba');
    expect(applyTone('Mẹ', 'nga'), 'Mẽ');
  });

  test('tone at cursor edits only the word before the cursor', () {
    expect(toneAtCursor('con meo', 7, 'huyen'), ('con mèo', 7));
    expect(toneAtCursor('con meo', 3, 'nang'), ('cọn meo', 3));
  });
}
