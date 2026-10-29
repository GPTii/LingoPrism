"""Game map: learning opens the rounds, rounds use only learned material, a failed round sends back to learning."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.learning.models import PersonalWord, StudySession
from apps.literacy import curriculum as cur
from apps.literacy.models import LiteracyProgress
from apps.vocab.models import Language, ReviewStatus, Word, WordTranslation

from . import content
from .path import ROUNDS, find_stop, stops

ANIMALS = [("mèo", "cat"), ("chó", "dog"), ("gà", "chicken"), ("vịt", "duck"), ("cá", "fish"), ("bò", "cow"),
           ("ngựa", "horse"), ("chim", "bird"), ("lợn", "pig"), ("dê", "goat")]


@pytest.fixture
def words(db):
    for code in ("vi", "en", "zh-Hans", "zh-Hant"):
        Language.objects.create(code=code, name=code, native_name=code, tts_locale=code)
    out = []
    for i in range(3):  # 30 words of level 1: 2 per round
        for vi, en in ANIMALS:
            w = Word.objects.create(slug=f"{en}-{i}", levels={"en": 1}, emoji="🐾")
            WordTranslation.objects.create(word=w, language_id="vi", text=f"{vi} {i}", status=ReviewStatus.VERIFIED)
            WordTranslation.objects.create(word=w, language_id="en", text=f"{en}{'x' * i}", status=ReviewStatus.VERIFIED)
            out.append(w)
    return out


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


def learn(user, ws):
    for w in ws:
        PersonalWord.objects.create(user=user, word=w, language="en", status="learning")


def play(client, node, ok=True):
    r = client.get(f"/api/v1/games/rounds/{node}/")
    assert r.status_code == 200, r.data
    results = [[ok] * len(g["items"]) for g in r.data["games"]]
    return r.data, client.post(f"/api/v1/games/rounds/{node}/finish/", {"token": r.data["token"], "results": results},
                               format="json")


def node(data, node_id):
    return next(x for level in data["levels"] for x in level["nodes"] if x["id"] == node_id)


def test_the_map_has_4_levels_of_rounds_chests_and_a_boss(words):
    user = User.objects.create_user("p@example.com", "Strong!Pass123", active_language="en")
    data = client_for(user).get("/api/v1/games/map/").data
    assert data["track"] == "words" and [lv["name"] for lv in data["levels"]] == ["Nhập môn", "Sơ cấp", "Trung cấp", "Nâng cao"]
    kinds = [x["kind"] for x in data["levels"][0]["nodes"]]
    assert kinds.count("round") == ROUNDS and kinds.count("chest") == 3 and kinds[-1] == "boss"
    assert kinds[4] == "chest"  # after the 4th round


def test_learning_opens_rounds_and_rounds_use_only_learned_words(words):
    user = User.objects.create_user("p@example.com", "Strong!Pass123", active_language="en")
    c = client_for(user)
    assert node(c.get("/api/v1/games/map/").data, "L1-r1")["lock"] == {"reason": "learn", "level": 1, "need": 2}
    assert c.get("/api/v1/games/rounds/L1-r1/").status_code == 403

    learn(user, words[:2])
    data = c.get("/api/v1/games/map/").data
    assert node(data, "L1-r1")["status"] == "open" and data["current"] == "L1-r1"
    assert node(data, "L1-r2")["lock"]["reason"] == "previous"

    r = c.get("/api/v1/games/rounds/L1-r1/")
    keys = content.unsign(r.data["token"])["keys"]
    assert {k for game in keys for k in game} <= {words[0].id, words[1].id}  # what the learner learned, nothing else
    for game in r.data["games"]:
        for item in game["items"]:
            if "answer" in item and "options" in item:
                assert item["answer"] in [o["t"] for o in item["options"]]


def test_passing_rewards_once_and_failing_sends_back_to_the_words(words):
    user = User.objects.create_user("p@example.com", "Strong!Pass123", active_language="en")
    c = client_for(user)
    learn(user, words[:10])
    _, res = play(c, "L1-r1")
    assert res.data["passed"] and res.data["stars"] == 3 and res.data["xp"] == 10 and res.data["next"]["id"] == "L1-r2"
    _, again = play(c, "L1-r1")
    assert again.data["passed"] and again.data["xp"] == 0  # the reward is for the first pass only

    round2, failed = play(c, "L1-r2", ok=False)
    assert not failed.data["passed"] and failed.data["stars"] == 0
    review = failed.data["review"]
    assert review["kind"] == "words" and set(review["word_ids"]) <= {words[2].id, words[3].id}
    # "Ôn lại những từ này": a practice session of exactly those words
    # the app sends empty fields as null
    s = c.post("/api/v1/sessions/", {"kind": "review", "topic": None, "size": None, "word_ids": review["word_ids"]},
               format="json")
    assert s.status_code == 201 and s.data["kind"] == StudySession.Kind.PRACTICE
    assert {i["card"]["id"] for i in s.data["items"]} == set(review["word_ids"])
    assert node(c.get("/api/v1/games/map/").data, "L1-r3")["status"] == "locked"


def test_chest_opens_once_after_the_round_before_it(words):
    user = User.objects.create_user("p@example.com", "Strong!Pass123", active_language="en")
    c = client_for(user)
    learn(user, words[:10])  # 4 rounds of 2 words, and round 5 after the chest
    assert c.post("/api/v1/games/chests/L1-c1/open/").status_code == 403
    for n in range(1, 5):
        assert play(c, f"L1-r{n}")[1].data["passed"]
    before = User.objects.get(pk=user.pk).gems_balance
    res = c.post("/api/v1/games/chests/L1-c1/open/")
    assert res.status_code == 200 and res.data["gems"] > 0
    assert User.objects.get(pk=user.pk).gems_balance == before + res.data["gems"]
    assert c.post("/api/v1/games/chests/L1-c1/open/").status_code == 400
    assert node(c.get("/api/v1/games/map/").data, "L1-r5")["status"] == "open"


def test_results_must_come_from_this_learner_and_round(words):
    user = User.objects.create_user("p@example.com", "Strong!Pass123", active_language="en")
    other = User.objects.create_user("o@example.com", "Strong!Pass123", active_language="en")
    learn(user, words[:2])
    learn(other, words[:2])
    r = client_for(user).get("/api/v1/games/rounds/L1-r1/")
    results = [[True] * len(g["items"]) for g in r.data["games"]]
    body = {"token": r.data["token"], "results": results}
    assert client_for(other).post("/api/v1/games/rounds/L1-r1/finish/", body, format="json").status_code == 400
    assert client_for(user).post("/api/v1/games/rounds/L1-r2/finish/", body, format="json").status_code == 400
    short = {"token": r.data["token"], "results": results[:-1]}
    assert client_for(user).post("/api/v1/games/rounds/L1-r1/finish/", short, format="json").status_code == 400
    bad = {"token": r.data["token"] + "x", "results": results}
    assert client_for(user).post("/api/v1/games/rounds/L1-r1/finish/", bad, format="json").status_code == 400


# ---------------------------------------------------------------- reading track (Vietnamese, kid mode)

@pytest.mark.django_db
def test_a_child_learning_vietnamese_plays_the_reading_course():
    kid = User.objects.create_user("k@example.com", "Strong!Pass123", active_language="vi", learner_type="kid")
    c = client_for(kid)
    data = c.get("/api/v1/games/map/").data
    assert data["track"] == "reading"
    assert node(data, "L1-r1")["lock"] == {"reason": "lesson", "lesson": 1, "title": cur.lesson(1)["title"]}
    LiteracyProgress.objects.create(user=kid, lesson=1, best_percent=80, stars=2)
    _, failed = play(c, "L1-r1", ok=False)
    assert failed.data["review"] == {"kind": "lesson", "lesson": 1}
    _, passed = play(c, "L1-r1")
    assert passed.data["passed"]
    assert node(c.get("/api/v1/games/map/").data, "L1-r2")["lock"]["reason"] == "lesson"


@pytest.mark.django_db
@pytest.mark.parametrize("level", [1, 2, 3, 4])
def test_reading_rounds_use_only_real_syllables_the_child_can_read(level):
    for stop in [s for s in stops("reading", level) if s.kind != "chest"]:
        n = stop.lesson or max(r.lesson for r in stops("reading", level) if r.kind == "round")
        known = {s.text for s, _ in cur.readable_syllables(n)}
        games, keys = content.reading_round(stop, seed=7)
        assert len(games) == (5 if stop.kind == "boss" else 3), stop.id
        for game in games:
            for item in game["items"]:
                if game["game"] in ("pop", "tone"):
                    assert {o["t"] for o in item["options"]} <= known, (stop.id, item)
                if game["game"] == "sort":
                    assert item["t"] in known
                if game["game"] == "order":
                    assert cur.readable_text(item["answer"], n)


def test_boss_needs_every_round_of_its_level(words):
    stop = find_stop("words", "L1-boss")
    assert stop.kind == "boss" and stop.level == 1
    user = User.objects.create_user("p@example.com", "Strong!Pass123", active_language="en")
    learn(user, words)
    assert client_for(user).get("/api/v1/games/rounds/L1-boss/").status_code == 403


# ---------------------------------------------------------------- rewards and helpers

def test_winning_rounds_counts_for_the_daily_quest_and_the_game_badges(words):
    from apps.gamification.models import Badge, DailyQuest, UserBadge, UserStats
    from apps.gamification.sync import sync_catalog
    from apps.gamification.models import Item
    sync_catalog(Item, Badge)
    user = User.objects.create_user("p@example.com", "Strong!Pass123", active_language="en")
    c = client_for(user)
    learn(user, words[:10])
    play(c, "L1-r1")
    quest = DailyQuest.objects.get(user=user, kind=DailyQuest.Kind.WIN_GAMES)
    assert quest.progress == 1 and not quest.completed
    stats = UserStats.objects.get(user=user)
    assert (stats.games_won, stats.bosses_won, stats.games_perfect) == (1, 0, 1)
    assert UserBadge.objects.filter(user=user, badge__code="games-1").exists()
    play(c, "L1-r1")  # a replay: the quest counts it, the badges do not
    stats.refresh_from_db()
    quest.refresh_from_db()
    assert quest.completed and stats.games_won == 1 and stats.games_perfect == 1
    play(c, "L1-r2", ok=False)
    stats.refresh_from_db()
    assert stats.games_won == 1


def test_helpers_cost_scales_and_are_limited_per_round(words):
    user = User.objects.create_user("p@example.com", "Strong!Pass123", active_language="en")
    c = client_for(user)
    learn(user, words[:2])
    r = c.get("/api/v1/games/rounds/L1-r1/").data
    assert r["helpers"]["cost"] == {"hint": 5, "retry": 10} and r["helpers"]["scales"] == 0
    assert all(item.get("hint") for g in r["games"] if g["game"] != "match" for item in g["items"])
    body = {"token": r["token"], "kind": "hint"}
    assert c.post("/api/v1/games/rounds/L1-r1/help/", body, format="json").status_code == 400  # no vảy
    User.objects.filter(pk=user.pk).update(scales_balance=100)
    res = c.post("/api/v1/games/rounds/L1-r1/help/", body, format="json")
    assert res.status_code == 200 and res.data["scales"] == 95 and res.data["left"] == 2
    assert c.post("/api/v1/games/rounds/L1-r1/help/", {**body, "kind": "retry"}, format="json").data["scales"] == 85
    c.post("/api/v1/games/rounds/L1-r1/help/", body, format="json")
    c.post("/api/v1/games/rounds/L1-r1/help/", body, format="json")
    assert c.post("/api/v1/games/rounds/L1-r1/help/", body, format="json").status_code == 400  # 3 per round
    assert User.objects.get(pk=user.pk).scales_balance == 75
    other = User.objects.create_user("o@example.com", "Strong!Pass123", active_language="en")
    assert client_for(other).post("/api/v1/games/rounds/L1-r1/help/", body, format="json").status_code == 400


@pytest.mark.django_db
def test_reading_hints_spell_the_syllable_out():
    stop = next(s for s in stops("reading", 1) if s.kind == "round")
    games, _ = content.reading_round(stop, seed=3)
    hints = [item["hint"] for g in games if g["game"] != "match" for item in g["items"]]
    assert hints and all(h.startswith(("Đánh vần: ", "Bắt đầu bằng")) for h in hints)
