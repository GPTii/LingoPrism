"""The game map: 4 levels (same names as the learning path), each a row of rounds with a chest after every 4th
round and a boss round at the end, like Duolingo's path.

Learning comes first: a round opens only once its content was learned in the Học section, and the map is played in
order (a round needs the previous stop passed). Two tracks:
  words   – English, Chinese, and Vietnamese for adults. A level has ROUNDS rounds; round k plays the k-th batch of
            the words of that level the learner has started (in the order they were added), so round k opens when
            k batches have been learned.
  reading – Vietnamese in kid mode: the reading course (apps.literacy). Each round is one lesson (long rhyme lessons
            are split into rounds of at most 3 rhymes) and opens once that lesson was passed.
"""
import math
from dataclasses import dataclass, field

from apps.learning.levels import LEVELS, STARTED, level_words
from apps.learning.models import PersonalWord
from apps.literacy import curriculum as cur
from apps.literacy.models import LiteracyProgress
from apps.literacy.views import PASS_PERCENT as LESSON_PASS

from .models import GameNode

ROUNDS = 15  # words track: rounds per level
CHEST_EVERY = 4
PASS_PERCENT = 70

READING_LEVELS = (  # lessons of the reading course in each level
    (1, range(1, 17), "Chữ cái, âm ghép và 5 dấu thanh"),
    (2, range(17, 30), "Vần không có âm cuối, vần có âm cuối n, m"),
    (3, range(30, 42), "Vần có âm cuối ng, nh, c, ch, t, p"),
    (4, range(42, 47), "Vần khó (iê, uô, ươ, oa, uy) và đọc cả câu"),
)
MAX_RHYMES = 3  # a reading round teaches at most this many rhymes


@dataclass
class Stop:
    id: str  # L2-r5 | L2-c1 | L2-boss
    level: int
    kind: str  # round | chest | boss
    index: int = 0
    title: str = ""
    lesson: int = 0  # reading: the lesson this round plays
    units: list = field(default_factory=list)  # reading: unit codes of the round ("am:b", "van:an")


def track_of(user, learn: str) -> str:
    return GameNode.Track.READING if learn == "vi" and getattr(user, "learner_type", "") == "kid" else GameNode.Track.WORDS


def _reading_rounds(lessons) -> list[tuple[int, list, str]]:
    out = []
    for n in lessons:
        lesson = cur.lesson(n)
        units = lesson["units"]
        if len(units) <= MAX_RHYMES:
            out.append((n, units, lesson["title"]))
            continue
        parts = math.ceil(len(units) / MAX_RHYMES)
        size = math.ceil(len(units) / parts)
        for i in range(0, len(units), size):
            chunk = units[i:i + size]
            out.append((n, chunk, "Vần " + ", ".join(u.code for u in chunk)))
    return out


def _with_chests(level: int, rounds: list[Stop]) -> list[Stop]:
    stops, chest = [], 0
    for r in rounds:
        stops.append(r)
        if r.index % CHEST_EVERY == 0:
            chest += 1
            stops.append(Stop(f"L{level}-c{chest}", level, "chest", chest, "Rương thưởng"))
    stops.append(Stop(f"L{level}-boss", level, "boss", 0, "Màn trùm"))
    return stops


def stops(track: str, level: int) -> list[Stop]:
    if track == GameNode.Track.READING:
        lessons = READING_LEVELS[level - 1][1]
        rounds = [Stop(f"L{level}-r{i}", level, "round", i, title, n, [f"{u.kind}:{u.code}" for u in units])
                  for i, (n, units, title) in enumerate(_reading_rounds(lessons), start=1)]
    else:
        rounds = [Stop(f"L{level}-r{i}", level, "round", i, f"Vòng {i}") for i in range(1, ROUNDS + 1)]
    return _with_chests(level, rounds)


def find_stop(track: str, node: str) -> Stop | None:
    try:
        level = int(node.split("-")[0][1:])
    except (ValueError, IndexError):
        return None
    if not 1 <= level <= len(LEVELS):
        return None
    return next((s for s in stops(track, level) if s.id == node), None)


# ------------------------------------------------------------------ what the learner has learned

def learned_words(user, target, level: int) -> tuple[list[int], int]:
    """Words of this level the learner has started in the Học section, in the order they were added."""
    ids = set(level_words(user, target, level).values_list("id", flat=True))
    started = (PersonalWord.objects.filter(user=user, language=target.learn, status__in=STARTED, word_id__in=ids)
               .order_by("created_at", "id").values_list("word_id", flat=True))
    return list(started), len(ids)


def batch_size(total: int) -> int:
    return max(1, math.ceil(total / ROUNDS))


def round_words(user, target, stop: Stop) -> list[int]:
    learned, total = learned_words(user, target, stop.level)
    if stop.kind == "boss":
        return learned
    size = batch_size(total)
    return learned[(stop.index - 1) * size: stop.index * size]


def passed_lessons(user) -> set[int]:
    return set(LiteracyProgress.objects.filter(user=user, best_percent__gte=LESSON_PASS).values_list("lesson", flat=True))


# ------------------------------------------------------------------ the map with its state

def game_map(user, target) -> dict:
    track = track_of(user, target.learn)
    results = {g.node: g for g in GameNode.objects.filter(user=user, language=target.learn, track=track)}
    lessons = passed_lessons(user) if track == GameNode.Track.READING else set()
    staff = getattr(user, "is_staff_role", False)
    levels, previous_done, current = [], True, None
    for n, name, desc in LEVELS:
        if track == GameNode.Track.READING:
            desc = READING_LEVELS[n - 1][2]
            learned, size = [], 0
        else:
            learned, total = learned_words(user, target, n)
            size = batch_size(total)
        nodes = []
        for stop in stops(track, n):
            result = results.get(stop.id)
            done = bool(result and result.passed_at)
            lock = None
            if not previous_done and not staff:
                lock = {"reason": "previous"}
            elif stop.kind == "round" and not staff:
                if track == GameNode.Track.READING and stop.lesson not in lessons:
                    lock = {"reason": "lesson", "lesson": stop.lesson, "title": cur.lesson(stop.lesson)["title"]}
                elif track == GameNode.Track.WORDS and len(learned) < stop.index * size:
                    lock = {"reason": "learn", "level": n, "need": stop.index * size - len(learned)}
            status = "done" if done else "locked" if lock else "open"
            if status == "open" and current is None:
                current = stop.id
            nodes.append({"id": stop.id, "kind": stop.kind, "index": stop.index, "title": stop.title,
                          "lesson": stop.lesson or None, "status": status, "stars": result.stars if result else 0,
                          "lock": lock})
            previous_done = done or staff
        first_lock = nodes[0]["lock"]
        levels.append({"level": n, "name": name, "description": desc, "nodes": nodes,
                       "unlocked": not (first_lock and first_lock["reason"] == "previous"),
                       "done": sum(1 for x in nodes if x["status"] == "done"), "total": len(nodes)})
    return {"language": target.learn, "track": track, "current": current, "pass_percent": PASS_PERCENT,
            "levels": levels}


def stop_state(user, target, node: str):
    """(stop, status, lock) for one stop, from the same rules as the map."""
    data = game_map(user, target)
    for level in data["levels"]:
        for x in level["nodes"]:
            if x["id"] == node:
                return find_stop(data["track"], node), x["status"], x["lock"], data["track"]
    return None, None, None, data["track"]
