"""Sticker packs, the new shop items and badges (catalog.py), and the new counters filled from what learners already
did, so the badges they have earned are awarded (with their gems) the next time they study."""
from collections import Counter

from django.db import migrations
from django.db.models import F

from apps.gamification.sync import sync_catalog


def forwards(apps, schema_editor):
    get = apps.get_model
    sync_catalog(get("gamification", "Item"), get("gamification", "Badge"), get("gamification", "UserInventory"))

    counts = {name: Counter() for name in ("quests_done", "sessions", "perfect_sessions", "friends", "cheers", "best_league")}
    for uid in get("gamification", "DailyQuest").objects.filter(progress__gte=F("target")).values_list("user_id", flat=True):
        counts["quests_done"][uid] += 1
    for uid, done, correct in (get("learning", "StudySession").objects.filter(ended_at__isnull=False, completed_count__gt=0)
                               .values_list("user_id", "completed_count", "correct_first_try")):
        counts["sessions"][uid] += 1
        if done >= 3 and correct == done:
            counts["perfect_sessions"][uid] += 1
    for a, b in get("community", "FriendRequest").objects.filter(status="accepted").values_list("from_user_id", "to_user_id"):
        counts["friends"][a] += 1
        counts["friends"][b] += 1
    for uid in get("community", "PostLike").objects.values_list("user_id", flat=True):
        counts["cheers"][uid] += 1
    for uid in get("community", "PostComment").objects.values_list("user_id", flat=True):
        counts["cheers"][uid] += 1
    place = {t: i + 1 for i, t in enumerate(get("gamification", "LeagueTier").objects.order_by("order").values_list("id", flat=True))}
    for uid, tier, result in get("gamification", "LeagueMember").objects.values_list("user_id", "cycle__tier_id", "result"):
        reached = min(place.get(tier, 1) + (result == "promoted"), max(place.values(), default=1))
        counts["best_league"][uid] = max(counts["best_league"][uid], reached)

    UserStats = get("gamification", "UserStats")
    users = set().union(*(c.keys() for c in counts.values()))
    for uid in users:
        stats, _ = UserStats.objects.get_or_create(user_id=uid)
        for name, c in counts.items():
            setattr(stats, name, max(c[uid], 1) if name == "best_league" else c[uid])
        stats.save()


class Migration(migrations.Migration):
    dependencies = [
        ("gamification", "0003_reward_stats"),
        ("community", "0005_friendrequest_postbookmark"),
        ("learning", "0004_personalword_fsrs_difficulty_and_more"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
