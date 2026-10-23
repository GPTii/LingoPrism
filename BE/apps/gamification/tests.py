from datetime import timedelta

import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User, UserGoal
from apps.gamification import mascot, services
from apps.gamification.models import DailyQuest, Item, LeagueCycle, Outfit, UserInventory
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
    assert services.claim_quest(user, q) == (15, 0)
    assert services.claim_quest(user, q) == (0, 0)
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


def test_friends_leaderboard_is_this_weeks_xp_of_people_you_follow(user):
    from apps.community.models import UserFollow
    from apps.gamification.models import XpTransaction

    friend = User.objects.create_user("f@example.com", "Strong!Pass123", display_name="Bạn")
    stranger = User.objects.create_user("s@example.com", "Strong!Pass123")
    UserFollow.objects.create(follower=user, following=friend)
    services.award_xp(user, "learn", 20)
    services.award_xp(friend, "learn", 50)
    services.award_xp(stranger, "learn", 90)
    old = services.award_xp(friend, "learn", 5) and XpTransaction.objects.filter(user=friend).latest("id")
    old.created_at -= timedelta(days=8)  # last week's XP does not count
    old.save(update_fields=["created_at"])

    c = APIClient()
    c.force_authenticate(user)
    rows = c.get("/api/v1/leaderboard/", {"scope": "friends"}).data["members"]
    assert [(r["display_name"], r["xp"], r["is_me"]) for r in rows] == [("Bạn", 50, False), (user.display_name, 20, True)]


def test_badge_gives_gems_once(user):
    services.award_xp(user, "learn", 120)  # "Tia sáng đầu": 100 XP → 1 gem
    user.refresh_from_db()
    assert user.gems_balance == 1
    assert Notification.objects.filter(user=user, kind="achievement", title__contains="Tia sáng đầu").count() == 1
    services.check_badges(user)
    user.refresh_from_db()
    assert user.gems_balance == 1


def test_last_quest_of_the_day_gives_a_gem(user):
    for q in services.ensure_quests(user):
        services.progress_quest(user, q.kind, absolute=q.target)
    quests = list(DailyQuest.objects.filter(user=user))
    gems = [services.claim_quest(user, q)[1] for q in quests]
    assert gems == [0] * (len(quests) - 1) + [1]
    assert services.stats_for(user).quests_done == len(quests)


def test_sticker_pack_unlocks_its_stickers(user):
    client = APIClient()
    client.force_authenticate(user)
    assert client.get("/api/v1/shop/items/stickers/").data == []
    pack = Item.objects.get(code="pack_feelings")
    shop = {i["code"]: i for i in client.get("/api/v1/shop/items/").data}
    assert [s["code"] for s in shop["pack_feelings"]["stickers"]][:2] == ["sticker_love", "sticker_sad"]
    assert "sticker_ok" not in shop  # the single stickers sold before are no longer on sale
    User.objects.filter(pk=user.pk).update(gems_balance=2)
    assert client.post(f"/api/v1/shop/items/{pack.id}/buy/").status_code == 200
    mine = [s["code"] for s in client.get("/api/v1/shop/items/stickers/").data]
    assert len(mine) == 6 and services.owns_sticker(user, "haha") and not services.owns_sticker(user, "hello")
    User.objects.filter(pk=user.pk).update(gems_balance=5)
    assert client.post(f"/api/v1/shop/items/{pack.id}/buy/").data["detail"] == "Bạn đã có gói sticker này"


def test_legacy_sticker_owner_gets_the_pack(user):
    from apps.gamification.models import Badge
    from apps.gamification.sync import sync_catalog

    legacy = Item.objects.create(code="sticker_ok", name="Sticker OK", description="", image="", effect="sticker", cost_gems=2)
    UserInventory.objects.create(user=user, item=legacy, quantity=1)
    sync_catalog(Item, Badge, UserInventory)
    assert services.owns_sticker(user, "great") and not Item.objects.get(code="sticker_ok").active


def test_gem_exchange_and_streak_repair(user):
    client = APIClient()
    client.force_authenticate(user)
    exchange = Item.objects.get(code="gem_exchange")
    User.objects.filter(pk=user.pk).update(scales_balance=600)
    res = client.post(f"/api/v1/shop/items/{exchange.id}/buy/")
    assert res.status_code == 200 and res.data["gems"] == 1 and res.data["scales"] == 100

    repair = Item.objects.get(code="streak_repair")
    User.objects.filter(pk=user.pk).update(gems_balance=10, scales_balance=1000)
    assert client.post(f"/api/v1/shop/items/{repair.id}/buy/").data["detail"] == "Chuỗi của bạn vẫn còn, không cần hồi"
    day = services.today()
    for i in range(10, 4, -1):  # a 6-day streak that ended 5 days ago…
        services.mark_activity(user, day - timedelta(days=i))
    services.mark_activity(user, day - timedelta(days=1))  # …and a new one started yesterday
    stats = services.stats_for(user)
    assert stats.current_streak == 1 and stats.lost_streak == 6
    assert client.get("/api/v1/gamification/summary/").data["repairable_streak"] == 6
    res = client.post(f"/api/v1/shop/items/{repair.id}/buy/")
    # paid in vảy; gems: 10 + 1 ("Khởi động", 3 days), then the 7-day streak earns "Một tuần kiên trì" (+2)
    assert res.status_code == 200 and res.data["scales"] == 200 and res.data["gems"] == 13
    assert services.stats_for(user).current_streak == 7
    assert client.get("/api/v1/gamification/summary/").data["repairable_streak"] == 0


def test_streak_repair_before_learning_again(user):
    day = services.today()
    for i in range(6, 2, -1):  # 4 days, then 2 days missed
        services.mark_activity(user, day - timedelta(days=i))
    assert services.repairable_streak(user) == 4
    User.objects.filter(pk=user.pk).update(scales_balance=800)
    services.purchase(user, Item.objects.get(code="streak_repair"))
    services.mark_activity(user, day)
    assert services.stats_for(user).current_streak == 5


def test_promotion_gives_gems_and_league_badge(user):
    other = User.objects.create_user("o2@example.com", "Strong!Pass123")
    services.award_xp(user, "learn", 50)
    services.award_xp(other, "learn", 20)
    services.close_cycle(LeagueCycle.objects.get())
    user.refresh_from_db()
    stats = services.stats_for(user)
    assert stats.best_league == 2
    # 5 gems for 1st place + 1 for "Lên hạng Ánh Đồng" + 3 for "Quán quân tuần" (the 50 XP give no badge yet)
    assert user.gems_balance == 9
    assert stats.league_wins == 1 and mascot.owned_codes(user) == {"hat_crown"}


def test_kids_do_not_see_community_badges(user):
    client = APIClient()
    client.force_authenticate(user)
    adult = {b["condition"] for b in client.get("/api/v1/badges/").data}
    user.learner_type = "kid"
    user.save()
    kid = {b["condition"] for b in client.get("/api/v1/badges/").data}
    assert "friends" in adult and "friends" not in kid and "streak" in kid


def test_prices_scales_for_help_gems_for_looks(user):
    for item in Item.objects.filter(active=True):
        if item.effect == "sticker":
            assert item.cost_gems and not item.cost_scales, item.code
        else:
            assert item.cost_scales and not item.cost_gems, item.code
    assert all(o.cost_gems or o.badge_code for o in Outfit.objects.all())


def test_wardrobe_buy_and_dress(user):
    client = APIClient()
    client.force_authenticate(user)
    data = client.get("/api/v1/mascot/").data
    assert data["name"] == "Prismo" and data["wearing"]["hat"] == "" and len(data["outfits"]) >= 40
    assert client.post("/api/v1/mascot/buy/", {"code": "hat_cap"}).data["detail"] == "Không đủ Ngọc"
    User.objects.filter(pk=user.pk).update(gems_balance=5)
    res = client.post("/api/v1/mascot/buy/", {"code": "hat_cap"})
    assert res.status_code == 200 and res.data["gems"] == 3 and res.data["wearing"]["hat"] == "hat_cap"  # worn at once
    assert client.post("/api/v1/mascot/buy/", {"code": "hat_cap"}).data["detail"] == "Prismo đã có món này rồi"
    assert client.post("/api/v1/mascot/buy/", {"code": "hat_crown"}).status_code == 400  # earned, never sold
    assert client.patch("/api/v1/mascot/", {"wearing": {"glasses": "glasses_sun"}}, format="json").status_code == 400
    assert client.patch("/api/v1/mascot/", {"wearing": {"glasses": "hat_cap"}}, format="json").status_code == 400
    res = client.patch("/api/v1/mascot/", {"name": "Bé Lam", "as_avatar": True, "wearing": {"hat": ""}}, format="json")
    assert res.data["name"] == "Bé Lam" and res.data["wearing"]["hat"] == "" and res.data["as_avatar"]
    client.force_authenticate(User.objects.get(pk=user.pk))  # a fresh user, as each real request has
    assert client.get("/api/v1/me/").data["mascot"]["name"] == "Bé Lam"
    lb = client.get("/api/v1/leaderboard/?scope=league").data["members"]
    assert lb[0]["mascot"]["as_avatar"] is True


def test_badge_unlocks_its_outfit(user):
    services.bump_stat(user, "night_owl")
    assert "hat_nightcap" in mascot.owned_codes(user)
    note = Notification.objects.filter(user=user, kind="achievement").latest("id")
    assert "Mũ ngủ" in note.body


def test_festival_pieces_only_in_their_window():
    from datetime import date

    witch = Outfit.objects.get(code="hat_witch")
    assert mascot.for_sale(witch, date(2026, 10, 31))
    assert not mascot.for_sale(witch, date(2026, 11, 10))
    assert mascot.how_to_get(witch, date(2026, 11, 10)) == "Chỉ bán dịp Halloween, từ 20/10"
    assert mascot.how_to_get(witch, date(2026, 10, 25)) == "Chỉ bán dịp Halloween, đến hết 03/11"
    tet = Outfit.objects.get(code="hand_lixi")
    assert mascot.for_sale(tet, date(2027, 2, 6)) and not mascot.for_sale(tet, date(2027, 3, 1))
