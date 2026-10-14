"""Gamification rules (ported from SnapLingua): XP with boosts and a daily cap, streaks with
streak-freeze, daily / monthly quests, weekly leagues, shop and badges."""
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import notify, push_event

from .models import (
    ActiveBoost, Badge, DailyProgress, DailyQuest, Item, LeagueCycle, LeagueMember, LeagueTier, MonthlyQuest,
    UserBadge, UserInventory, UserStats, XpTransaction,
)

DAILY_XP_CAP = 500
XP_MILESTONES = [100, 500, 1000, 2500, 5000, 10000, 25000, 50000]
LEAGUE_GROUP_SIZE = 30


def today() -> date:
    return timezone.localdate()


def stats_for(user) -> UserStats:
    return UserStats.objects.get_or_create(user=user)[0]


def progress_for(user, day: date | None = None) -> DailyProgress:
    day = day or today()
    goal = getattr(user, "goal", None)
    return DailyProgress.objects.get_or_create(
        user=user, date=day,
        defaults={
            "new_target": goal.daily_new_target if goal else 10,
            "review_target": goal.daily_review_target if goal else 20,
        },
    )[0]


# ------------------------------------------------------------------ streak

@transaction.atomic
def mark_activity(user, day: date | None = None) -> UserStats:
    """Record that the user studied today and update the streak (consuming a streak freeze if needed)."""
    day = day or today()
    stats = UserStats.objects.select_for_update().get_or_create(user=user)[0]
    progress = progress_for(user, day)
    if not progress.active:
        progress.active = True
        progress.save(update_fields=["active"])
    last = stats.last_active_date
    if last == day:
        return stats
    if last == day - timedelta(days=1):
        stats.current_streak += 1
    elif last == day - timedelta(days=2) and _consume_item(user, Item.Effect.STREAK_FREEZE):
        missed = progress_for(user, day - timedelta(days=1))
        missed.freeze_used = True
        missed.save(update_fields=["freeze_used"])
        stats.freezes_used += 1
        stats.current_streak += 2
        notify(user, Notification.Kind.SYSTEM, "Đá băng đã giữ chuỗi streak của bạn! 🧊",
               f"Chuỗi hiện tại: {stats.current_streak} ngày.", image="assets/images/streak/streakbang.png")
    else:
        stats.current_streak = 1
    stats.longest_streak = max(stats.longest_streak, stats.current_streak)
    stats.last_active_date = day
    stats.save()
    check_badges(user, stats)
    return stats


def current_streak(user) -> int:
    """Streak shown to the user: broken if they missed yesterday (and have no freeze)."""
    stats = stats_for(user)
    if stats.last_active_date is None:
        return 0
    gap = (today() - stats.last_active_date).days
    if gap <= 1:
        return stats.current_streak
    if gap == 2 and has_item(user, Item.Effect.STREAK_FREEZE):
        return stats.current_streak
    return 0


# ------------------------------------------------------------------ XP

def active_multiplier(user) -> float:
    boosts = ActiveBoost.objects.filter(user=user, expires_at__gt=timezone.now()).values_list("multiplier", flat=True)
    return max(boosts, default=1.0)


@transaction.atomic
def award_xp(user, source: str, base: int, source_id: str = "", note: str = "") -> int:
    if base <= 0:
        return 0
    multiplier = active_multiplier(user)
    progress = DailyProgress.objects.select_for_update().get(pk=progress_for(user).pk)
    amount = min(round(base * multiplier), max(DAILY_XP_CAP - progress.xp, 0))
    XpTransaction.objects.create(user=user, source=source, source_id=str(source_id), base_amount=base,
                                 multiplier=multiplier, amount=amount, note=note)
    if amount <= 0:
        return 0
    progress.xp += amount
    progress.save(update_fields=["xp"])
    stats = UserStats.objects.select_for_update().get_or_create(user=user)[0]
    before = stats.lifetime_xp
    stats.lifetime_xp += amount
    stats.save(update_fields=["lifetime_xp"])
    member = join_current_league(user)
    LeagueMember.objects.filter(pk=member.pk).update(weekly_xp=F("weekly_xp") + amount)
    for m in XP_MILESTONES:
        if before < m <= stats.lifetime_xp:
            notify(user, Notification.Kind.XP_MILESTONE, f"Bạn đã đạt {m} XP!",
                   f"Tổng kinh nghiệm hiện tại: {stats.lifetime_xp} XP.", image="assets/images/XP.png",
                   data={"route": "/profile"})
    check_badges(user, stats)
    push_event(user.id, "xp", {"amount": amount, "lifetime_xp": stats.lifetime_xp, "today_xp": progress.xp})
    return amount


# ------------------------------------------------------------------ badges

def check_badges(user, stats: UserStats | None = None):
    stats = stats or stats_for(user)
    values = {
        Badge.Condition.XP: stats.lifetime_xp,
        Badge.Condition.STREAK: stats.current_streak,
        Badge.Condition.WORDS_LEARNED: stats.words_learned,
        Badge.Condition.WORDS_MASTERED: stats.words_mastered,
        Badge.Condition.DETECTIONS: stats.detections,
        Badge.Condition.POSTS: stats.posts,
    }
    owned = set(UserBadge.objects.filter(user=user).values_list("badge_id", flat=True))
    for badge in Badge.objects.exclude(id__in=owned):
        if values.get(badge.condition, 0) >= badge.threshold:
            UserBadge.objects.get_or_create(user=user, badge=badge)
            notify(user, Notification.Kind.ACHIEVEMENT, "Bạn vừa nhận được thành tựu mới",
                   f"{badge.name}: {badge.description}", image=badge.icon, data={"route": "/profile", "badge": badge.code})


def bump_stat(user, field: str, by: int = 1):
    UserStats.objects.get_or_create(user=user)
    UserStats.objects.filter(user=user).update(**{field: F(field) + by})
    check_badges(user)


# ------------------------------------------------------------------ quests

def ensure_quests(user, day: date | None = None) -> list[DailyQuest]:
    day = day or today()
    goal = getattr(user, "goal", None)
    targets = {
        DailyQuest.Kind.SAVE_WORDS: 5,
        DailyQuest.Kind.REACH_LEARN_GOAL: goal.daily_new_target if goal else 10,
        DailyQuest.Kind.REACH_REVIEW_GOAL: goal.daily_review_target if goal else 20,
        DailyQuest.Kind.POST_COMMUNITY_IMAGE: 1,
        DailyQuest.Kind.ENGAGE_COMMUNITY: 5,
    }
    if user.learner_type == "kid":  # no social quests for children
        targets.pop(DailyQuest.Kind.POST_COMMUNITY_IMAGE)
        targets.pop(DailyQuest.Kind.ENGAGE_COMMUNITY)
    for kind, target in targets.items():
        DailyQuest.objects.get_or_create(user=user, date=day, kind=kind, defaults={"target": target})
    return list(DailyQuest.objects.filter(user=user, date=day))


def monthly_for(user, day: date | None = None) -> MonthlyQuest:
    day = day or today()
    return MonthlyQuest.objects.get_or_create(user=user, month=day.strftime("%Y-%m"))[0]


@transaction.atomic
def progress_quest(user, kind: str, amount: int = 1, absolute: int | None = None):
    ensure_quests(user)
    quest = DailyQuest.objects.select_for_update().filter(user=user, date=today(), kind=kind).first()
    if quest is None or quest.completed:
        return
    quest.progress = min(quest.target, absolute if absolute is not None else quest.progress + amount)
    if quest.completed:
        quest.completed_at = timezone.now()
        monthly = monthly_for(user)
        MonthlyQuest.objects.filter(pk=monthly.pk).update(completed_count=F("completed_count") + 1)
        push_event(user.id, "quest_completed", {"kind": kind})
    quest.save()


@transaction.atomic
def claim_quest(user, quest: DailyQuest) -> int:
    quest = DailyQuest.objects.select_for_update().get(pk=quest.pk)
    if not quest.completed or quest.reward_claimed:
        return 0
    quest.reward_claimed = True
    quest.save(update_fields=["reward_claimed"])
    type(user).objects.filter(pk=user.pk).update(scales_balance=F("scales_balance") + DailyQuest.REWARD_SCALES)
    return DailyQuest.REWARD_SCALES


@transaction.atomic
def claim_monthly(user) -> int:
    monthly = MonthlyQuest.objects.select_for_update().get(pk=monthly_for(user).pk)
    if monthly.reward_claimed or monthly.completed_count < MonthlyQuest.TARGET:
        return 0
    monthly.reward_claimed = True
    monthly.reward_claimed_at = timezone.now()
    monthly.save(update_fields=["reward_claimed", "reward_claimed_at"])
    type(user).objects.filter(pk=user.pk).update(gems_balance=F("gems_balance") + MonthlyQuest.REWARD_GEMS)
    return MonthlyQuest.REWARD_GEMS


# ------------------------------------------------------------------ leagues

def week_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = timezone.localtime(now or timezone.now())
    monday = (now - timedelta(days=now.weekday())).date()
    start = timezone.make_aware(datetime.combine(monday, time.min))
    return start, start + timedelta(days=7)


def _user_tier(user) -> LeagueTier:
    last = LeagueMember.objects.filter(user=user, cycle__status=LeagueCycle.Status.CLOSED).select_related("cycle__tier").order_by("-cycle__start_at").first()
    tiers = list(LeagueTier.objects.order_by("order"))
    if not tiers:
        tiers = [LeagueTier.objects.create(code="tan-binh", name="Tân binh Igloo", order=0)]
    if last is None:
        return tiers[0]
    idx = next(i for i, t in enumerate(tiers) if t.id == last.cycle.tier_id)
    if last.result == "promoted":
        idx = min(idx + 1, len(tiers) - 1)
    elif last.result == "demoted":
        idx = max(idx - 1, 0)
    return tiers[idx]


def join_current_league(user) -> LeagueMember:
    start, end = week_bounds()
    existing = LeagueMember.objects.filter(user=user, cycle__start_at=start).first()
    if existing:
        return existing
    tier = _user_tier(user)
    cycle = None
    for c in LeagueCycle.objects.filter(tier=tier, start_at=start, status=LeagueCycle.Status.ACTIVE).order_by("group_index"):
        if c.members.count() < LEAGUE_GROUP_SIZE:
            cycle = c
            break
    if cycle is None:
        index = LeagueCycle.objects.filter(tier=tier, start_at=start).count()
        cycle = LeagueCycle.objects.create(tier=tier, group_index=index, start_at=start, end_at=end)
    return LeagueMember.objects.get_or_create(cycle=cycle, user=user)[0]


@transaction.atomic
def close_cycle(cycle: LeagueCycle):
    tiers = list(LeagueTier.objects.order_by("order"))
    is_top = cycle.tier_id == tiers[-1].id
    is_bottom = cycle.tier_id == tiers[0].id
    members = list(cycle.members.select_related("user").order_by("-weekly_xp", "id"))
    n = len(members)
    for rank, m in enumerate(members, start=1):
        m.rank = rank
        if rank <= cycle.tier.promote_top and m.weekly_xp > 0 and not is_top:
            m.result = "promoted"
        elif rank > n - cycle.tier.demote_bottom and n > cycle.tier.promote_top + cycle.tier.demote_bottom and not is_bottom:
            m.result = "demoted"
        else:
            m.result = "stayed"
        m.save(update_fields=["rank", "result"])
        if m.result == "promoted":
            notify(m.user, Notification.Kind.LEAGUE, "Bạn vừa thăng hạng mới!", f"Hạng {rank} tuần qua tại {cycle.tier.name}.",
                   data={"route": "/community/leaderboard"})
    cycle.status = LeagueCycle.Status.CLOSED
    cycle.save(update_fields=["status"])


# ------------------------------------------------------------------ shop

class ShopError(Exception):
    pass


def has_item(user, effect: str) -> bool:
    return UserInventory.objects.filter(user=user, item__effect=effect, quantity__gt=0).exists()


def _consume_item(user, effect: str) -> bool:
    inv = UserInventory.objects.select_for_update().filter(user=user, item__effect=effect, quantity__gt=0).first()
    if inv is None:
        return False
    inv.quantity -= 1
    inv.last_used_at = timezone.now()
    inv.save(update_fields=["quantity", "last_used_at", "updated_at"])
    return True


@transaction.atomic
def purchase(user, item: Item) -> UserInventory:
    from apps.accounts.models import User

    u = User.objects.select_for_update().get(pk=user.pk)
    if item.cost_scales:
        if u.scales_balance < item.cost_scales:
            raise ShopError("Không đủ Vảy")
        u.scales_balance -= item.cost_scales
    elif item.cost_gems:
        if u.gems_balance < item.cost_gems:
            raise ShopError("Không đủ Ngọc")
        u.gems_balance -= item.cost_gems
    else:
        raise ShopError("Vật phẩm không bán")
    if item.effect == Item.Effect.STICKER and UserInventory.objects.filter(user=u, item=item, quantity__gt=0).exists():
        raise ShopError("Bạn đã có sticker này")
    u.save(update_fields=["scales_balance", "gems_balance"])
    inv, _ = UserInventory.objects.get_or_create(user=u, item=item)
    inv.quantity += 1
    inv.save(update_fields=["quantity", "updated_at"])
    return inv


BOOSTS = {
    Item.Effect.XP_DOUBLE_15M: (2.0, timedelta(minutes=15)),
    Item.Effect.XP_PLUS25_24H: (1.25, timedelta(hours=24)),
}


@transaction.atomic
def use_item(user, item: Item) -> ActiveBoost:
    if item.effect not in BOOSTS:
        raise ShopError("Vật phẩm này được dùng tự động")
    if not _consume_item(user, item.effect):
        raise ShopError("Bạn không có vật phẩm này")
    multiplier, duration = BOOSTS[item.effect]
    now = timezone.now()
    return ActiveBoost.objects.create(user=user, item=item, multiplier=multiplier, started_at=now, expires_at=now + duration)


def owns_sticker(user, code: str) -> bool:
    return UserInventory.objects.filter(user=user, item__code=code, item__effect=Item.Effect.STICKER, quantity__gt=0).exists()
