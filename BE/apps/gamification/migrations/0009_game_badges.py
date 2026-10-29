"""The game badges (catalog.py), and the new counters filled from the rounds learners already played, so the badges
they have earned are awarded (with their gems) the next time they play or study."""
from collections import Counter

from django.db import migrations

from apps.gamification.sync import sync_catalog


def forwards(apps, schema_editor):
    get = apps.get_model
    sync_catalog(get("gamification", "Item"), get("gamification", "Badge"), get("gamification", "UserInventory"),
                 get("gamification", "Outfit"))
    won, bosses, perfect = Counter(), Counter(), Counter()
    for uid, node, stars in (get("games", "GameNode").objects.filter(passed_at__isnull=False)
                             .exclude(node__contains="-c").values_list("user_id", "node", "stars")):
        won[uid] += 1
        bosses[uid] += node.endswith("-boss")
        perfect[uid] += stars == 3
    UserStats = get("gamification", "UserStats")
    for uid in won:
        stats, _ = UserStats.objects.get_or_create(user_id=uid)
        stats.games_won, stats.bosses_won, stats.games_perfect = won[uid], bosses[uid], perfect[uid]
        stats.save(update_fields=["games_won", "bosses_won", "games_perfect"])


class Migration(migrations.Migration):
    dependencies = [("gamification", "0008_game_stats"), ("games", "0001_initial")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
