/// Vietnamese typing helper for children whose phone has no Vietnamese keyboard: put a tone mark on the word before
/// the cursor, with the same placement rule as the server (BE apps/vocab/lang/vietnamese.py – "kiểu cũ": hòa, thủy).
library;

const specialLetters = ['ă', 'â', 'đ', 'ê', 'ô', 'ơ', 'ư'];
const _tones = ['ngang', 'huyen', 'sac', 'hoi', 'nga', 'nang'];

/// Precomposed forms, index = tone (ngang, huyền, sắc, hỏi, ngã, nặng).
const _forms = {
  'a': 'aàáảãạ', 'ă': 'ăằắẳẵặ', 'â': 'âầấẩẫậ', 'e': 'eèéẻẽẹ', 'ê': 'êềếểễệ', 'i': 'iìíỉĩị',
  'o': 'oòóỏõọ', 'ô': 'ôồốổỗộ', 'ơ': 'ơờớởỡợ', 'u': 'uùúủũụ', 'ư': 'ưừứửữự', 'y': 'yỳýỷỹỵ',
};
final Map<String, String> _baseOf = {
  for (final e in _forms.entries)
    for (final ch in e.value.split('')) ...{ch: e.key, ch.toUpperCase(): e.key.toUpperCase()},
};

String _withTone(String vowel, String tone) {
  final lower = vowel.toLowerCase();
  final forms = _forms[lower];
  if (forms == null) return vowel;
  final out = forms[_tones.indexOf(tone).clamp(0, 5)];
  return vowel == lower ? out : out.toUpperCase();
}

String applyTone(String syllable, String tone) {
  final chars = syllable.split('').map((c) => _baseOf[c] ?? c).toList(); // strip any tone
  if (tone == 'ngang') return chars.join();
  final lower = chars.map((c) => c.toLowerCase()).toList();
  var idx = [for (var i = 0; i < lower.length; i++) if (_forms.containsKey(lower[i])) i];
  if (idx.isEmpty) return chars.join();
  final word = lower.join();
  if ((word.startsWith('qu') || word.startsWith('gi')) && idx.length > 1 && idx[0] == 1) idx = idx.sublist(1);
  var target = idx[0];
  final special = idx.where((i) => 'ăâêôơư'.contains(lower[i])).toList();
  if (special.isNotEmpty) {
    target = lower[special.last] == 'ơ' && special.length > 1 ? special.last : special.first;
  } else if (idx.length >= 2) {
    final endsWithVowel = idx.last == lower.length - 1;
    target = idx.length == 3 ? idx[1] : (endsWithVowel ? idx[0] : idx[1]);
  }
  chars[target] = _withTone(chars[target], tone);
  return chars.join();
}

/// Applies [tone] to the word ending at [cursor] in [text]; returns the new text and cursor offset.
(String, int) toneAtCursor(String text, int cursor, String tone) {
  final before = text.substring(0, cursor);
  final m = RegExp(r'[\p{L}]+$', unicode: true).firstMatch(before);
  if (m == null) return (text, cursor);
  final replaced = applyTone(m.group(0)!, tone);
  return (text.substring(0, m.start) + replaced + text.substring(cursor), m.start + replaced.length);
}
