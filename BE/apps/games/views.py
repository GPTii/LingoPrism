"""Trò chơi: the game map of the active language, its rounds, and the chests.

GET  /games/map/                      the 4 levels with every stop and whether it is open, and the stop
                                      each friend has reached (their avatar is shown there)
GET  /games/rounds/<node>/            the mini games of an open round or boss round
POST /games/rounds/<node>/finish/     {token, results: [[true, false, …] per game]} -> score, stars, rewards;
                                      a failed round says what to learn again (words or a reading lesson)
POST /games/chests/<node>/open/       an open chest -> gems and scales, once
POST /games/rounds/<node>/help/       {token, kind: hint | retry} -> pay vảy for a helper during the round

Rewards join the rest of the app: XP (daily goal, league, XP badges), the streak, the daily quest "win 2 rounds",
and the game badges (rounds won, bosses won, rounds with 3 stars – each round counted once).
"""
import hashlib
import random
from collections import Counter

from django.core import signing
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.gamification.models import DailyQuest, XpTransaction
from apps.gamification.services import award_xp, bump_stat, mark_activity, progress_quest
from apps.vocab.services import resolve_target
from apps.vocab.views import LANG_PARAMS

from . import content
from .models import GameNode
from .path import PASS_PERCENT, friends_on_map, game_map, round_words, stop_state

ROUND_XP = 10
BOSS_XP = 30
BOSS_GEMS = 10
CHEST_GEMS = {1: 3, 2: 4, 3: 5, 4: 6}
CHEST_SCALES = 20
# helpers bought with vảy during a round (vảy pay for help, ngọc for looks): the hint shows the item's "hint"
# (meaning of the word / how to spell the syllable out), retry takes back a wrong answer. A few per round.
HELPERS = {"hint": 5, "retry": 10}
HELPERS_PER_ROUND = 3


def stars_for(percent: int) -> int:
    return 3 if percent == 100 else 2 if percent >= 85 else 1 if percent >= PASS_PERCENT else 0


def _locked(lock: dict | None):
    reason = (lock or {}).get("reason")
    detail = {"previous": "Hãy qua màn trước đã.",
              "learn": f"Hãy học thêm {(lock or {}).get('need', 0)} từ ở mục Học để mở màn này.",
              "lesson": f"Hãy học xong bài “{(lock or {}).get('title', '')}” ở mục Học để mở màn này."}.get(reason, "Màn này chưa mở.")
    return Response({"detail": detail, "lock": lock, "errors": {}}, status=403)


@extend_schema(tags=["games"], parameters=LANG_PARAMS, responses={200: dict})
class GameMapView(APIView):
    def get(self, request):
        target = resolve_target(request)
        return Response({**game_map(request.user, target), "friends": friends_on_map(request.user, target, request)})


@extend_schema(tags=["games"], parameters=LANG_PARAMS, responses={200: dict})
class GameRoundView(APIView):
    def get(self, request, node: str):
        target = resolve_target(request)
        stop, status, lock, track = stop_state(request.user, target, node)
        if stop is None or stop.kind == "chest":
            return Response({"detail": "Không có màn chơi này", "errors": {}}, status=404)
        if status == "locked":
            return _locked(lock)
        seed = random.randrange(1 << 30)
        if track == GameNode.Track.READING:
            games, keys = content.reading_round(stop, seed, request)
        else:
            games, keys = content.word_round(request.user, target, request, stop, round_words(request.user, target, stop), seed)
        if not games:
            return Response({"detail": "Màn này chưa đủ từ để chơi. Hãy học thêm ở mục Học.", "errors": {}}, status=400)
        token = content.sign(u=request.user.id, l=target.learn, k=track, n=node, keys=keys)
        request.user.refresh_from_db(fields=["scales_balance"])
        return Response({"node": node, "kind": stop.kind, "level": stop.level, "title": stop.title, "track": track,
                         "pass_percent": PASS_PERCENT, "games": games, "token": token,
                         "helpers": {"cost": HELPERS, "per_round": HELPERS_PER_ROUND,
                                     "scales": request.user.scales_balance}})


class FinishSerializer(serializers.Serializer):
    token = serializers.CharField()
    results = serializers.ListField(child=serializers.ListField(child=serializers.BooleanField(), max_length=20),
                                    max_length=10)


def _review(track: str, keys: list[list], results: list[list[bool]]) -> dict | None:
    wrong = [k for game_keys, game_results in zip(keys, results) for k, ok in zip(game_keys, game_results) if not ok]
    if not wrong:
        return None
    if track == GameNode.Track.READING:
        return {"kind": "lesson", "lesson": Counter(wrong).most_common(1)[0][0]}
    return {"kind": "words", "word_ids": list(dict.fromkeys(wrong))[:20]}


@extend_schema(tags=["games"], parameters=LANG_PARAMS, request=FinishSerializer, responses={200: dict})
class GameFinishView(APIView):
    def post(self, request, node: str):
        ser = FinishSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            data = content.unsign(ser.validated_data["token"])
        except signing.BadSignature:
            return Response({"detail": "Màn chơi đã hết hạn, hãy chơi lại", "errors": {}}, status=400)
        target = resolve_target(request)
        if data["u"] != request.user.id or data["n"] != node or data["l"] != target.learn:
            return Response({"detail": "Kết quả không thuộc màn chơi này", "errors": {}}, status=400)
        keys, results = data["keys"], ser.validated_data["results"]
        if len(results) != len(keys) or any(len(r) != len(k) for r, k in zip(results, keys)):
            return Response({"detail": "Kết quả không khớp với màn chơi", "errors": {}}, status=400)
        total = sum(len(k) for k in keys)
        correct = sum(sum(r) for r in results)
        percent = round(100 * correct / total) if total else 0
        stars, passed = stars_for(percent), percent >= PASS_PERCENT
        boss = node.endswith("-boss")
        xp = gems = 0
        with transaction.atomic():
            g, _ = GameNode.objects.select_for_update().get_or_create(
                user=request.user, language=target.learn, track=data["k"], node=node)
            first_pass = passed and not g.passed_at
            first_perfect = stars == 3 and g.stars < 3
            g.plays += 1
            g.best_percent = max(g.best_percent, percent)
            g.stars = max(g.stars, stars)
            if first_pass:
                g.passed_at = timezone.now()
            g.save()
            if first_pass and boss:
                gems = BOSS_GEMS
                type(request.user).objects.filter(pk=request.user.pk).update(gems_balance=F("gems_balance") + gems)
        if first_pass:
            xp = award_xp(request.user, XpTransaction.Source.GAME, BOSS_XP if boss else ROUND_XP, source_id=node,
                          note=f"Trò chơi {target.learn} {node}")
        mark_activity(request.user)
        if passed:
            progress_quest(request.user, DailyQuest.Kind.WIN_GAMES)
        if first_pass or first_perfect:
            bump_stat(request.user, "games_won", int(first_pass), bosses_won=int(first_pass and boss),
                      games_perfect=int(first_perfect))
        nxt = None
        if passed:
            nodes = [x for level in game_map(request.user, target)["levels"] for x in level["nodes"]]
            ids = [x["id"] for x in nodes]
            after = nodes[ids.index(node) + 1:] if node in ids else []
            nxt = next((x for x in after if x["status"] != "done"), None)
        return Response({"correct": correct, "total": total, "percent": percent, "stars": stars, "passed": passed,
                         "best_stars": g.stars, "xp": xp, "gems": gems,
                         "review": None if passed else _review(data["k"], keys, results),
                         "next": nxt})


@extend_schema(tags=["games"], parameters=LANG_PARAMS, request=None, responses={200: dict})
class ChestOpenView(APIView):
    def post(self, request, node: str):
        target = resolve_target(request)
        stop, status, lock, track = stop_state(request.user, target, node)
        if stop is None or stop.kind != "chest":
            return Response({"detail": "Không có rương này", "errors": {}}, status=404)
        if status == "locked":
            return _locked(lock)
        with transaction.atomic():
            g, _ = GameNode.objects.select_for_update().get_or_create(
                user=request.user, language=target.learn, track=track, node=node)
            if g.passed_at:
                return Response({"detail": "Rương này đã được mở", "errors": {}}, status=400)
            g.passed_at = timezone.now()
            g.plays = 1
            g.save()
            gems = CHEST_GEMS.get(stop.level, 3)
            type(request.user).objects.filter(pk=request.user.pk).update(
                gems_balance=F("gems_balance") + gems, scales_balance=F("scales_balance") + CHEST_SCALES)
        return Response({"gems": gems, "scales": CHEST_SCALES})


class HelpSerializer(serializers.Serializer):
    token = serializers.CharField()
    kind = serializers.ChoiceField(choices=list(HELPERS))


@extend_schema(tags=["games"], parameters=LANG_PARAMS, request=HelpSerializer, responses={200: dict})
class GameHelpView(APIView):
    """Pay vảy for a helper: the round's answers and hints are already on the device, so this only charges (and
    limits) them. 400 when the learner has too few vảy or used the helper HELPERS_PER_ROUND times this round."""

    def post(self, request, node: str):
        ser = HelpSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token, kind = ser.validated_data["token"], ser.validated_data["kind"]
        try:
            data = content.unsign(token)
        except signing.BadSignature:
            return Response({"detail": "Màn chơi đã hết hạn, hãy chơi lại", "errors": {}}, status=400)
        if data["u"] != request.user.id or data["n"] != node:
            return Response({"detail": "Không thuộc màn chơi này", "errors": {}}, status=400)
        key = f"games:help:{kind}:{hashlib.sha256(token.encode()).hexdigest()[:32]}"
        cache.add(key, 0, timeout=6 * 3600)
        if cache.get(key, 0) >= HELPERS_PER_ROUND:
            return Response({"detail": f"Mỗi màn chỉ dùng được {HELPERS_PER_ROUND} lần", "errors": {}}, status=400)
        cost = HELPERS[kind]
        User = type(request.user)
        if not User.objects.filter(pk=request.user.pk, scales_balance__gte=cost).update(
                scales_balance=F("scales_balance") - cost):
            return Response({"detail": f"Cần {cost} vảy – qua màn và mở rương để có thêm vảy", "errors": {}}, status=400)
        used = cache.incr(key)
        scales = User.objects.values_list("scales_balance", flat=True).get(pk=request.user.pk)
        return Response({"kind": kind, "cost": cost, "scales": scales, "left": HELPERS_PER_ROUND - used})
