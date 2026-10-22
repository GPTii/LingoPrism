from datetime import timedelta

import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User, UserGoal
from apps.gamification import services
from apps.gamification.models import DailyQuest, Item, LeagueCycle, UserInventory
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    call_command("seed_gamification")
    u = User.objects.create_user("g@example.com", "Strong!Pass123")
    UserGoal.objects.create(user=u)
    return u


def test_award_xp_daily_cap_and_milestone(user):
    assert services.award_xp(user, "learn", 80) == 80
    assert Notification.objects.filter(user=user, kind="xp_milestone").count() == 0
    services.award_xp(user, "learn", 30)  # crosses 100 XP
    assert Notification.objects.filter(user=user, kind="xp_milestone").count() == 1
    assert services.award_xp(user, "learn", 1000) == services.DAILY_XP_CAP - 110
    assert services.award_xp(user, "learn", 10) == 0
    assert services.stats_for(user).lifetime_xp == services.DAILY_XP_CAP


def test_xp_boost(user):
    item = Item.objects.get(code="xp_boost")
    UserInventory.objects.create(user=user, item=item, quantity=1)
    services.use_item(user, item)
    assert services.award_xp(user, "learn", 10) == 20


def test_streak_and_freeze(user):
    d0 = services.today()
    services.mark_activity(user, d0 - timedelta(days=4))
    services.mark_activity(user, d0 - timedelta(days=3))
    assert services.stats_for(user).current_streak == 2
    # skipped a day without a freeze → reset
    services.mark_activity(user, d0 - timedelta(days=1))
    assert services.stats_for(user).current_streak == 1
    # skipped a day with a freeze → kept
    UserInventory.objects.create(user=user, item=Item.objects.get(code="streak_freeze"), quantity=1)
    services.mark_activity(user, d0 + timedelta(days=1))
    stats = services.stats_for(user)
    assert stats.current_streak == 3 and stats.freezes_used == 1
    assert UserInventory.objects.get(user=user, item__code="streak_freeze").quantity == 0


def test_quests_claim_and_monthly(user):
    quests = services.ensure_quests(user)
    assert len(quests) == 5
    services.progress_quest(user, DailyQuest.Kind.SAVE_WORDS, 5)
    q = DailyQuest.objects.get(user=user, kind=DailyQuest.Kind.SAVE_WORDS)
    assert q.completed
    assert services.claim_quest(user, q) == 15
    assert services.claim_quest(user, q) == 0
    user.refresh_from_db()
    assert user.scales_balance == 15
    assert services.monthly_for(user).completed_count == 1


def test_kids_have_no_social_quests(user):
    user.learner_type = "kid"
    user.save()
    kinds = {q.kind for q in services.ensure_quests(user)}
    assert "post_community_image" not in kinds


def test_shop_purchase(user):
    client = APIClient()
    client.force_authenticate(user)
    freeze = Item.objects.get(code="streak_freeze")
    res = client.post(f"/api/v1/shop/items/{freeze.id}/buy/")
    assert res.status_code == 400 and res.data["detail"] == "Không đủ Vảy"
    User.objects.filter(pk=user.pk).update(scales_balance=250)
    res = client.post(f"/api/v1/shop/items/{freeze.id}/buy/")
    assert res.status_code == 200 and res.data["scales"] == 50
    items = {i["code"]: i for i in client.get("/api/v1/shop/items/").data}
    assert items["streak_freeze"]["owned"] == 1


def test_league_join_and_close(user):
    other = User.objects.create_user("o@example.com", "Strong!Pass123")
    services.award_xp(user, "learn", 50)
    services.award_xp(other, "learn", 20)
    client = APIClient()
    client.force_authenticate(user)
    board = client.get("/api/v1/leaderboard/").data
    assert board["tier"]["name"] == "Tia Sáng"
    assert [m["xp"] for m in board["members"]] == [50, 20] and board["members"][0]["is_me"]
    cycle = LeagueCycle.objects.get()
    services.close_cycle(cycle)
    assert cycle.members.get(user=user).result == "promoted"


def test_summary_endpoint(user):
    client = APIClient()
    client.force_authenticate(user)
    data = client.get("/api/v1/gamification/summary/").data
    assert data["streak"] == 0 and data["daily_xp_cap"] == 500 and data["level"] == 1


@pytest.mark.django_db(transaction=True)
def test_websocket_receives_notifications(user):
    from config.asgi import application

    async def run():
        token = str(AccessToken.for_user(user))
        comm = WebsocketCommunicator(application, f"/ws/events/?token={token}")
        connected, _ = await comm.connect()
        assert connected
        assert (await comm.receive_json_from())["event"] == "connected"
        from channels.db import database_sync_to_async

        await database_sync_to_async(services.award_xp)(user, "learn", 10)
        msg = await comm.receive_json_from(timeout=3)
        assert msg["event"] == "xp" and msg["payload"]["amount"] == 10
        await comm.disconnect()

    async_to_sync(run)()


@pytest.mark.django_db(transaction=True)
def test_websocket_rejects_anonymous():
    from config.asgi import application

    async def run():
        comm = WebsocketCommunicator(application, "/ws/events/")
        connected, code = await comm.connect()
        assert not connected

    async_to_sync(run)()
