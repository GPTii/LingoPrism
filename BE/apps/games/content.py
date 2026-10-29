"""Mini games of one round of the game map.

A round is 3 mini games (a boss round 5), each a list of items. The items carry their answer so the game can
react at once (a game waits for nobody); the server keeps, in the signed round token, which word or lesson each
item came from, to score the round and to send a learner who failed back to exactly what to learn again.

Item shapes (same on the web and in the app):
  choose games – pop, fish, tone, picture, meaning, gate:
      {"prompt": {"text", "sub", "audio": {"text", "locale"}, "image", "emoji"}, "options": [{"t", "s", "image",
       "emoji"}], "answer": "<t of the right option>"}
  train  – {"audio", "onsets", "rhymes", "tones": [{"code", "label", "symbol"}], "answer": {"onset", "rhyme", "tone"}}
  sort   – game: {"baskets": [a, b]}; item: {"t", "audio", "answer": basket}
  match  – {"a": {"t", "s"}, "b": {"t", "image", "emoji"}}: one pair, right when found without a wrong flip
  spell, order – {"prompt", "tiles": [...], "joiner": "" | " ", "answer": "<tiles joined in order>"}
  type   – {"prompt", "answer", "accepted": [...]}
Every item but a match pair also has "hint": the meaning of the word (words track) or how the syllable is spelt out
(đánh vần, reading track) – shown only when the learner pays for it (views.HELPERS).

Words track: only words the learner has learned in this round (distractors may come from the whole level).
Reading track: only real syllables made of the sounds, rhymes and tones already taught (apps.literacy).
"""
import random

from django.core import signing

from apps.learning.levels import level_words
from apps.literacy import curriculum as cur
from apps.literacy import exercises as lit
from apps.vocab.lang import pinyin as py
from apps.vocab.lang import vi_phonics as ph
from apps.vocab.models import Word
from apps.vocab.services import tts_locale, words_for_target

from .path import READING_LEVELS, Stop, stops

SALT = "games.v1"
ITEMS = 5
ROUND_GAMES = 3
BOSS_GAMES = 5

WORD_GAMES = {
    "en": ["pop", "meaning", "picture", "spell", "match", "order"],
    "zh": ["pop", "tone", "meaning", "match", "spell", "order", "picture"],
    "vi": ["pop", "picture", "match", "spell", "order"],
}
READING_GAMES = {
    1: ["pop", "tone", "fish", "train", "gate", "match"],
    2: ["pop", "fish", "sort", "train", "match", "order"],
    3: ["sort", "train", "type", "order", "match", "pop"],
    4: ["sort", "type", "order", "train", "match", "pop"],
}
TITLES = {
    "pop": "Bắt bong bóng: nghe rồi chạm vào quả bóng đúng",
    "fish": "Câu cá: câu con cá mang đáp án đúng",
    "picture": "Nghe rồi chọn hình đúng",
    "meaning": "Chọn nghĩa đúng của từ",
    "gate": "Chọn cửa: chữ nào viết đúng?",
    "train": "Ghép toa tàu: âm đầu + vần + dấu",
    "sort": "Hái quả: thả mỗi quả vào giỏ đúng vần",
    "match": "Lật thẻ: tìm các cặp đi với nhau",
    "order": "Xếp câu: nghe rồi xếp các từ đúng thứ tự",
    "type": "Đuổi hình bắt chữ: nhìn hình, nghe rồi viết",
}


def sign(**data) -> str:
    return signing.dumps(data, salt=SALT, compress=True)


def unsign(token: str, max_age: int = 6 * 3600) -> dict:
    return signing.loads(token, salt=SALT, max_age=max_age)


def starts_with(tiles: list[str]) -> str:
    return f"Bắt đầu bằng “{tiles[0]}”"


def _assemble(order: list[str], start: int, count: int, make) -> tuple[list[dict], list[list]]:
    """Games in rotation from `start`, skipping one that has too little material; when fewer kinds than `count`
    have material, a kind comes back with new items. (games, item keys)"""
    games, keys, empty = [], [], set()
    for i in range(len(order) * 2):
        if len(games) == count or len(empty) == len(order):
            break
        kind = order[(start + i) % len(order)]
        if kind in empty:
            continue
        built = make(kind)
        if built and built[0]["items"]:
            games.append(built[0])
            keys.append(built[1])
        else:
            empty.add(kind)
    return games, keys


# ====================================================================== words track

class WordGames:
    def __init__(self, user, target, request, word_ids: list[int], level: int, rng: random.Random):
        self.target, self.rng, self.request = target, rng, request
        self.locale = tts_locale(target.code)
        batch = {w.id: w for w in words_for_target(Word.objects.filter(id__in=word_ids), user, target)}
        self.words = [e for e in (self._entry(batch[i]) for i in word_ids if i in batch) if e]
        pool_ids = list(level_words(user, target, level).exclude(id__in=word_ids).order_by("?").values_list("id", flat=True)[:60])
        pool = words_for_target(Word.objects.filter(id__in=pool_ids), user, target)
        self.pool = [e for e in (self._entry(w) for w in pool) if e]

    def _entry(self, w: Word) -> dict | None:
        by_lang = {t.language_id: t for t in getattr(w, "visible_translations", [])}
        tr = by_lang.get(self.target.code)
        if tr is None:
            return None
        image = w.image.url if w.image else w.image_url
        if image and image.startswith("/") and self.request is not None:
            image = self.request.build_absolute_uri(image)
        vi = by_lang.get("vi")
        return {"id": w.id, "text": tr.text, "sub": tr.pinyin if self.target.learn == "zh" else "",
                "numbered": tr.pinyin_numbered, "meaning": vi.text if vi and self.target.learn != "vi" else "",
                "image": image or None, "emoji": w.emoji,
                "examples": [e for e in getattr(w, "visible_examples", []) if e.tokens]}

    def _audio(self, text: str) -> dict:
        return {"text": text, "locale": self.locale}

    @staticmethod
    def _hint(e: dict) -> str:
        word = f"{e['text']} ({e['sub']})" if e["sub"] else e["text"]
        return f"{word} nghĩa là “{e['meaning']}”" if e["meaning"] else f"Từ này là “{word}”"

    def _sample(self, items: list, k: int) -> list:
        return self.rng.sample(items, min(k, len(items)))

    def _distractors(self, answer_entry: dict, key: str, k: int, need=None) -> list[dict]:
        seen = {answer_entry[key]}
        out = []
        for e in self.rng.sample(self.words + self.pool, len(self.words + self.pool)):
            if e[key] and e[key] not in seen and (need is None or need(e)):
                seen.add(e[key])
                out.append(e)
            if len(out) == k:
                break
        return out

    def _choose(self, game, entries, prompt, option, value, need=None):
        items, keys = [], []
        for e in entries:
            others = self._distractors(e, value, 3, need)
            if len(others) < 2:
                continue
            opts = [option(x) for x in others + [e]]
            self.rng.shuffle(opts)
            items.append({"prompt": prompt(e), "options": opts, "answer": option(e)["t"], "hint": self._hint(e)})
            keys.append(e["id"])
        return {"game": game, "title": TITLES.get(game, ""), "items": items}, keys

    def make(self, game: str):
        words, text_opt = self.words, (lambda e: {"t": e["text"], "s": e["sub"]})
        pictured = lambda e: bool(e["image"] or e["emoji"])  # noqa: E731
        if game == "pop":
            return self._choose("pop", self._sample(words, ITEMS), lambda e: {"audio": self._audio(e["text"])},
                                text_opt, "text")
        if game == "meaning":
            with_meaning = [e for e in words if e["meaning"]]
            return self._choose("meaning", self._sample(with_meaning, ITEMS),
                                lambda e: {"text": e["text"], "sub": e["sub"], "audio": self._audio(e["text"])},
                                lambda e: {"t": e["meaning"]}, "meaning", need=lambda e: bool(e["meaning"]))
        if game == "picture":
            return self._choose("picture", self._sample([e for e in words if pictured(e)], ITEMS),
                                lambda e: {"audio": self._audio(e["text"])},
                                lambda e: {"t": str(e["id"]), "image": e["image"], "emoji": e["emoji"]}, "id", need=pictured)
        if game == "tone":
            return self._tone()
        if game == "match":
            return self._match()
        if game == "spell":
            return self._spell()
        if game == "order":
            return self._order()
        return None

    def _tone(self):
        items, keys = [], []
        for e in self._sample([e for e in self.words if e["numbered"]], ITEMS * 2):
            syls = py.syllables(e["numbered"])
            if not syls or any(not s[-1].isdigit() for s in syls):
                continue
            i = self.rng.randrange(len(syls))
            base, right = syls[i][:-1], syls[i][-1]
            variants = []
            for tone in "1234":
                v = syls[:i] + [base + tone] + syls[i + 1:]
                variants.append(py.numbered_to_marked(" ".join(v)))
            answer = py.numbered_to_marked(" ".join(syls))
            if right == "5" or answer not in variants:
                continue
            opts = [{"t": v} for v in variants]
            items.append({"prompt": {"text": e["text"], "audio": self._audio(e["text"])}, "options": opts, "answer": answer,
                          "hint": f"{self._hint(e)}, đọc là {answer}"})
            keys.append(e["id"])
            if len(items) == ITEMS:
                break
        return {"game": "tone", "title": "Nghe rồi chọn pinyin có thanh điệu đúng", "items": items}, keys

    def _match(self):
        if self.target.learn == "vi":
            usable = [e for e in self.words if e["image"] or e["emoji"]]
            pair = lambda e: {"a": {"t": e["text"]}, "b": {"t": "", "image": e["image"], "emoji": e["emoji"]}}  # noqa: E731
        else:
            usable = [e for e in self.words if e["meaning"]]
            pair = lambda e: {"a": {"t": e["text"], "s": e["sub"]}, "b": {"t": e["meaning"]}}  # noqa: E731
        chosen, seen = [], set()
        for e in self.rng.sample(usable, len(usable)):
            b = pair(e)["b"]
            label = b["t"] or b["image"] or b["emoji"]
            if label not in seen and e["text"] not in seen:
                seen.update({label, e["text"]})
                chosen.append(e)
            if len(chosen) == 5:
                break
        if len(chosen) < 3:
            return None
        return {"game": "match", "title": TITLES["match"], "items": [pair(e) for e in chosen]}, [e["id"] for e in chosen]

    def _spell(self):
        learn, items, keys = self.target.learn, [], []
        for e in self.rng.sample(self.words, len(self.words)):
            text = e["text"]
            if learn == "en":
                if not (3 <= len(text) <= 10 and text.isalpha()):
                    continue
                tiles, joiner = list(text.lower()), ""
                extra = self.rng.sample("abcdefghijklmnopqrstuvwxyz", 2)
                title = "Ghép chữ cái thành từ vừa nghe"
            elif learn == "zh":
                if not 2 <= len(text) <= 4:
                    continue
                tiles, joiner = list(text), ""
                others = [c for x in self.pool + self.words for c in x["text"] if c not in text]
                extra = self.rng.sample(others, min(2, len(others)))
                title = "Ghép chữ Hán thành từ vừa nghe"
            else:
                tiles, joiner = ph.syllables_of(text), " "
                if len(tiles) < 2:
                    continue
                others = [s for x in self.pool for s in ph.syllables_of(x["text"]) if s not in tiles]
                extra = self.rng.sample(others, min(1, len(others)))
                title = "Ghép các tiếng thành từ vừa nghe"
            shuffled = tiles + extra
            self.rng.shuffle(shuffled)
            items.append({"prompt": {"audio": self._audio(text), "sub": e["meaning"], "image": e["image"], "emoji": e["emoji"]},
                          "tiles": shuffled, "joiner": joiner, "answer": joiner.join(tiles),
                          "hint": f"{self._hint(e)} · bắt đầu bằng “{tiles[0]}”"})
            keys.append(e["id"])
            if len(items) == ITEMS:
                break
        return {"game": "spell", "title": title if items else "", "items": items}, keys

    def _order(self):
        joiner = "" if self.target.learn == "zh" else " "
        items, keys = [], []
        for e in self.rng.sample(self.words, len(self.words)):
            for ex in e["examples"]:
                tiles = [t["t"] for t in ex.tokens if not t.get("x")]
                if not 3 <= len(tiles) <= 8 or len(set(tiles)) != len(tiles):
                    continue
                shuffled = tiles[:]
                while shuffled == tiles:
                    self.rng.shuffle(shuffled)
                hint = ex.translation_vi if self.target.learn != "vi" else ""
                items.append({"prompt": {"audio": self._audio(ex.text), "sub": hint}, "tiles": shuffled,
                              "joiner": joiner, "answer": joiner.join(tiles), "hint": starts_with(tiles)})
                keys.append(e["id"])
                break
            if len(items) == 3:
                break
        return {"game": "order", "title": TITLES["order"], "items": items}, keys


def word_round(user, target, request, stop: Stop, word_ids: list[int], seed: int) -> tuple[list[dict], list[list]]:
    rng = random.Random(seed)
    gen = WordGames(user, target, request, word_ids if stop.kind != "boss" else rng.sample(word_ids, min(30, len(word_ids))),
                    stop.level, rng)
    order = WORD_GAMES[target.learn]
    count = BOSS_GAMES if stop.kind == "boss" else ROUND_GAMES
    return _assemble(order, stop.index + rng.randrange(len(order)), count, gen.make)


# ====================================================================== reading track (Vietnamese, kid mode)

VI = "vi-VN"
RULES = {("c", "k"): 6, ("g", "gh"): 9, ("ng", "ngh"): 10}  # lesson that teaches each spelling rule


class ReadingGames:
    def __init__(self, units: list[tuple[cur.Unit, int]], n: int, level: int, rng: random.Random, request=None):
        """units: (unit, lesson that teaches it); n: the last lesson whose sounds the child knows."""
        self.units, self.n, self.level, self.rng, self.request = units, n, level, rng, request
        self.taught = cur.taught_until(n)
        self.known = {s.text for s, c in cur.readable_syllables(n)}
        self.examples = []  # (syllable, lesson)
        for unit, lesson in units:
            for s in lit._weighted_pick(lit._examples(unit, n), 4, rng):
                self.examples.append((s, lesson))
        self.default_lesson = units[0][1] if units else n

    def _audio(self, text):
        return {"text": text, "locale": VI}

    @staticmethod
    def _hint(text: str) -> str:
        return "Đánh vần: " + " – ".join(ph.spell(text))

    def make(self, game: str):
        return getattr(self, "_" + game)()

    def _word_hint(self, text: str) -> str:
        syllables = ph.syllables_of(text)
        return self._hint(syllables[0]) if len(syllables) == 1 else starts_with(syllables)

    def _pop(self):
        items, keys = [], []
        for s, lesson in self.rng.sample(self.examples, len(self.examples)):
            pool = lit._similar(s, self.n)
            if len(pool) < 2:
                continue
            opts = [{"t": x} for x in lit._options(s.text, pool, 4, self.rng)]
            items.append({"prompt": {"audio": self._audio(s.text)}, "options": opts, "answer": s.text, "hint": self._hint(s.text)})
            keys.append(lesson)
            if len(items) == ITEMS:
                break
        return {"game": "pop", "title": TITLES["pop"], "items": items}, keys

    def _fish(self):
        items, keys, t = [], [], self.taught
        for unit, lesson in self.units:
            for s in lit._weighted_pick(lit._examples(unit, self.n), 2, self.rng):
                if unit.kind == "thanh":
                    pool, answer, ask = [ph.TONE_LABEL[x] for x in ["ngang", *sorted(t.tones)]], ph.TONE_LABEL[s.tone], "dấu thanh"
                elif unit.kind == "van" or unit.is_vowel:
                    pool, answer, ask = sorted(t.rhymes | t.vowels), s.rhyme, "vần"
                else:
                    pool, answer, ask = sorted(t.onsets), s.onset, "âm đầu"
                if len(set(pool)) < 2:
                    continue
                opts = [{"t": x} for x in lit._options(answer, pool, 4, self.rng)]
                items.append({"prompt": {"text": s.text, "sub": f"Tiếng “{s.text}” có {ask} nào?", "audio": self._audio(s.text)},
                              "options": opts, "answer": answer, "hint": self._hint(s.text)})
                keys.append(lesson)
        picked = list(range(len(items)))
        self.rng.shuffle(picked)
        picked = sorted(picked[:ITEMS])
        return {"game": "fish", "title": TITLES["fish"], "items": [items[i] for i in picked]}, [keys[i] for i in picked]

    def _tone(self):
        if len(self.taught.tones) < 1:
            return None
        items, keys = [], []
        for s, lesson in self.rng.sample(self.examples, len(self.examples)):
            variants = [ph.compose(s.onset, s.rhyme, t) for t in ["ngang", *ph.TONES[1:]] if t == "ngang" or t in self.taught.tones]
            variants = [v for v in dict.fromkeys(variants) if v in self.known or v == s.text]
            if len(variants) < 2 or s.text not in variants:
                continue
            others = [v for v in variants if v != s.text]
            opts = [{"t": v} for v in self.rng.sample(others, min(3, len(others))) + [s.text]]
            self.rng.shuffle(opts)
            items.append({"prompt": {"text": ph.compose(s.onset, s.rhyme, "ngang"), "audio": self._audio(s.text)},
                          "options": opts, "answer": s.text, "hint": self._hint(s.text)})
            keys.append(lesson)
            if len(items) == ITEMS:
                break
        return {"game": "tone", "title": "Thả dấu: chọn dấu để thành tiếng vừa nghe", "items": items}, keys

    def _train(self):
        items, keys, t = [], [], self.taught
        tones = ["ngang", *[x for x in ph.TONES if x in t.tones]]
        for s, lesson in self.rng.sample(self.examples, len(self.examples)):
            onsets = lit._options(s.onset or "∅", [o or "∅" for o in sorted(t.onsets)] + ["∅"], 3, self.rng)
            rhymes = lit._options(s.rhyme, sorted(t.rhymes | t.vowels), 3, self.rng)
            if len(rhymes) < 2:
                continue
            items.append({"audio": self._audio(s.text), "text": s.text, "onsets": onsets, "rhymes": rhymes,
                          "tones": [{"code": x, "label": ph.TONE_LABEL[x], "symbol": ph.TONE_SYMBOL[x]} for x in tones],
                          "answer": {"onset": s.onset or "∅", "rhyme": s.rhyme, "tone": s.tone}, "hint": self._hint(s.text)})
            keys.append(lesson)
            if len(items) == 4:
                break
        return {"game": "train", "title": TITLES["train"], "items": items}, keys

    def _gate(self):
        pairs = [p for p, lesson in RULES.items() if lesson <= self.n]
        if not pairs:
            return None
        items, keys = [], []
        candidates = [s for s, c in cur.readable_syllables(self.n)[:600] if c > 0 and any(s.onset in p for p in pairs)]
        for s in self.rng.sample(candidates, min(ITEMS, len(candidates))):
            pair = next(p for p in pairs if s.onset in p)
            items.append({"prompt": {"text": "_" + ph.compose("", s.rhyme, s.tone), "audio": self._audio(s.text)},
                          "options": [{"t": x} for x in pair], "answer": s.onset, "hint": self._hint(s.text)})
            keys.append(RULES[pair])
        return {"game": "gate", "title": TITLES["gate"], "items": items}, keys

    def _sort(self):
        rhymes = [(u.code, lesson) for u, lesson in self.units if u.kind == "van" or u.is_vowel]
        if len(rhymes) < 2:
            known = sorted(self.taught.rhymes - {r for r, _ in rhymes})
            if not rhymes or not known:
                return None
            rhymes.append((self.rng.choice(known), rhymes[0][1]))
        a, b = self.rng.sample(rhymes, 2)
        items, keys = [], []
        for code, lesson in (a, b):
            matching = [s for s, c in cur.readable_syllables(self.n) if c > 0 and s.rhyme == code][:12]
            for s in self.rng.sample(matching, min(3, len(matching))):
                items.append({"t": s.text, "audio": self._audio(s.text), "answer": code, "hint": self._hint(s.text)})
                keys.append(lesson)
        if len({i["answer"] for i in items}) < 2:
            return None
        order = list(range(len(items)))
        self.rng.shuffle(order)
        return ({"game": "sort", "title": TITLES["sort"], "baskets": [a[0], b[0]], "items": [items[i] for i in order]},
                [keys[i] for i in order])

    def _pictured_words(self):
        words = [dict(w) for w in lit._words(self.n) if len(w["text"]) <= 14]
        for w in words:  # the app needs the full address of a picture
            if w["image"] and w["image"].startswith("/") and self.request is not None:
                w["image"] = self.request.build_absolute_uri(w["image"])
        return words

    def _match(self):
        words = self._pictured_words()
        chosen, seen = [], set()
        for w in self.rng.sample(words, len(words)):
            label = w["image"] or w["emoji"]
            if label not in seen:
                seen.add(label)
                chosen.append(w)
            if len(chosen) == 5:
                break
        if len(chosen) < 3:
            return None
        return ({"game": "match", "title": TITLES["match"],
                 "items": [{"a": {"t": w["text"]}, "b": {"t": "", "image": w["image"], "emoji": w["emoji"]}} for w in chosen]},
                [self.default_lesson] * len(chosen))

    def _type(self):
        words = self._pictured_words()
        chosen = self.rng.sample(words, min(3, len(words)))
        return ({"game": "type", "title": TITLES["type"],
                 "items": [{"prompt": {"audio": self._audio(w["text"]), "image": w["image"], "emoji": w["emoji"]},
                            "answer": w["text"], "accepted": [w["text"]], "hint": self._word_hint(w["text"])} for w in chosen]},
                [self.default_lesson] * len(chosen))

    def _order(self):
        if self.n < 17:
            return None
        longest = 6 if self.n < 40 else 8
        sentences = [x for x in cur.corpus()["sentences"]
                     if 3 <= x["syllables"] <= longest and cur.readable_text(x["text"], self.n)]
        items = []
        for x in self.rng.sample(sentences, min(3, len(sentences))):
            tiles = ph.syllables_of(x["text"])
            if len(set(tiles)) != len(tiles):
                continue
            shuffled = tiles[:]
            while shuffled == tiles:
                self.rng.shuffle(shuffled)
            items.append({"prompt": {"audio": self._audio(x["text"])}, "tiles": shuffled, "joiner": " ",
                          "answer": " ".join(tiles), "hint": starts_with(tiles)})
        return {"game": "order", "title": TITLES["order"], "items": items}, [self.default_lesson] * len(items)


def reading_round(stop: Stop, seed: int, request=None) -> tuple[list[dict], list[list]]:
    rng = random.Random(seed)
    by_code = {f"{u.kind}:{u.code}": (u, n) for n in range(1, len(cur.LESSONS) + 1) for u in cur.lesson(n)["units"]}
    if stop.kind == "boss":
        rounds = [s for s in stops("reading", stop.level) if s.kind == "round"]
        units = [by_code[c] for r in rounds for c in r.units]
        n = max(READING_LEVELS[stop.level - 1][1])  # everything taught in the level, nothing from the next one
        rng.shuffle(units)
    else:
        units = [by_code[c] for c in stop.units]
        n = stop.lesson
    gen = ReadingGames(units, n, stop.level, rng, request)
    order = READING_GAMES[stop.level]
    count = BOSS_GAMES if stop.kind == "boss" else ROUND_GAMES
    return _assemble(order, stop.index + rng.randrange(len(order)), count, gen.make)
