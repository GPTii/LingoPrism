from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsStaffRole

from . import services
from .models import (
    ActiveBoost, Badge, DailyProgress, DailyQuest, Item, LeagueCycle, LeagueMember, LeagueTier, UserBadge,
    UserInventory, XpTransaction,
)


def _avatar(request, user):
    return user.avatar_url(request)


class SummaryView(APIView):
    @extend_schema(tags=["gamification"], responses={200: dict})
    def get(self, request):
        user = request.user
        user.refresh_from_db(fields=["scales_balance", "gems_balance"])
        stats = services.stats_for(user)
        progress = services.progress_for(user)
        boosts = ActiveBoost.objects.filter(user=user, expires_at__gt=timezone.now()).select_related("item")
        member = LeagueMember.objects.filter(user=user, cycle__start_at=services.week_bounds()[0]).select_related("cycle__tier").first()
        return Response({
            "lifetime_xp": stats.lifetime_xp, "level": stats.level, "today_xp": progress.xp,
            "daily_xp_cap": services.DAILY_XP_CAP,
            "streak": services.current_streak(user), "longest_streak": stats.longest_streak,
            "studied_today": progress.active,
            "scales": user.scales_balance, "gems": user.gems_balance,
            "streak_freezes": UserInventory.objects.filter(user=user, item__effect=Item.Effect.STREAK_FREEZE).aggregate(n=Sum("quantity"))["n"] or 0,
            "freezes_used": stats.freezes_used,
            "words_learned": stats.words_learned, "words_mastered": stats.words_mastered,
            "today": {"new_learned": progress.new_learned, "new_target": progress.new_target,
                      "reviews_done": progress.reviews_done, "review_target": progress.review_target},
            "active_boosts": [{"item": b.item.code, "name": b.item.name, "multiplier": b.multiplier, "expires_at": b.expires_at} for b in boosts],
            "league": {"tier": member.cycle.tier.name, "tier_code": member.cycle.tier.code, "weekly_xp": member.weekly_xp} if member else None,
        })


class ProgressView(APIView):
    @extend_schema(tags=["gamification"], parameters=[
        OpenApiParameter("start", str, description="YYYY-MM-DD"), OpenApiParameter("end", str, description="YYYY-MM-DD")],
        responses={200: dict})
    def get(self, request):
        end = date.fromisoformat(request.query_params.get("end")) if request.query_params.get("end") else services.today()
        start = date.fromisoformat(request.query_params.get("start")) if request.query_params.get("start") else end - timedelta(days=89)
        rows = DailyProgress.objects.filter(user=request.user, date__range=(start, end)).order_by("date")
        return Response([
            {"date": r.date, "xp": r.xp, "new_learned": r.new_learned, "reviews_done": r.reviews_done,
             "active": r.active, "freeze_used": r.freeze_used}
            for r in rows
        ])


class QuestSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="get_kind_display")
    completed = serializers.BooleanField()
    reward_scales = serializers.SerializerMethodField()

    class Meta:
        model = DailyQuest
        fields = ["id", "kind", "title", "target", "progress", "completed", "completed_at", "reward_claimed", "reward_scales"]

    def get_reward_scales(self, obj):
        return DailyQuest.REWARD_SCALES


@extend_schema(tags=["gamification"])
class QuestViewSet(viewsets.GenericViewSet):
    serializer_class = QuestSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return DailyQuest.objects.none()
        return DailyQuest.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def today(self, request):
        quests = services.ensure_quests(request.user)
        monthly = services.monthly_for(request.user)
        return Response({
            "quests": QuestSerializer(quests, many=True).data,
            "monthly": {"month": monthly.month, "completed_count": monthly.completed_count,
                        "target": monthly.TARGET, "reward_gems": monthly.REWARD_GEMS, "reward_claimed": monthly.reward_claimed},
        })

    @action(detail=True, methods=["post"])
    def claim(self, request, pk=None):
        quest = get_object_or_404(self.get_queryset(), pk=pk)
        gained = services.claim_quest(request.user, quest)
        if not gained:
            return Response({"detail": "Nhiệm vụ chưa hoàn thành hoặc đã nhận thưởng", "errors": {}}, status=400)
        return Response({"scales": gained})

    @action(detail=False, methods=["post"], url_path="monthly/claim")
    def claim_monthly(self, request):
        gained = services.claim_monthly(request.user)
        if not gained:
            return Response({"detail": "Chưa đủ nhiệm vụ trong tháng hoặc đã nhận thưởng", "errors": {}}, status=400)
        return Response({"gems": gained})


class BadgeSerializer(serializers.ModelSerializer):
    owned = serializers.SerializerMethodField()
    awarded_at = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = ["id", "code", "name", "description", "icon", "sticker", "condition", "threshold", "owned", "awarded_at"]

    def _owned(self):
        if not hasattr(self, "_cache"):
            uid = self.context.get("user_id") or self.context["request"].user.id
            self._cache = dict(UserBadge.objects.filter(user_id=uid).values_list("badge_id", "awarded_at"))
        return self._cache

    def get_owned(self, obj):
        return obj.id in self._owned()

    def get_awarded_at(self, obj):
        return self._owned().get(obj.id)


@extend_schema(tags=["gamification"])
class BadgeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = BadgeSerializer
    queryset = Badge.objects.all()
    pagination_class = None

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request.query_params.get("user"):
            ctx["user_id"] = int(self.request.query_params["user"])
        return ctx


class LeaderboardView(APIView):
    @extend_schema(tags=["gamification"], parameters=[OpenApiParameter("scope", str, description="league | global | friends")],
                   responses={200: dict})
    def get(self, request):
        scope = request.query_params.get("scope", "league")
        User = get_user_model()
        tiers = [{"code": t.code, "name": t.name, "order": t.order, "icon": t.icon} for t in LeagueTier.objects.all()]
        if scope == "friends":
            # you and the people you follow, by XP earned this week (Monday 00:00, local time)
            from apps.community.models import UserFollow

            ids = [request.user.id, *UserFollow.objects.filter(follower=request.user).values_list("following_id", flat=True)]
            today = timezone.localdate()
            week_start = timezone.make_aware(datetime.combine(today - timedelta(days=today.weekday()), time.min))
            xp = dict(XpTransaction.objects.filter(user_id__in=ids, created_at__gte=week_start)
                      .values("user_id").annotate(s=Sum("amount")).values_list("user_id", "s"))
            people = sorted(User.objects.filter(id__in=ids, is_active=True), key=lambda u: (-(xp.get(u.id) or 0), u.id))
            return Response({"scope": "friends", "tiers": tiers, "members": [
                {"rank": i + 1, "user_id": u.id, "display_name": u.display_name, "avatar": _avatar(request, u),
                 "xp": xp.get(u.id) or 0, "is_me": u.id == request.user.id}
                for i, u in enumerate(people)
            ]})
        if scope == "global":
            top = User.objects.filter(is_active=True, stats__lifetime_xp__gt=0).select_related("stats").order_by("-stats__lifetime_xp")[:50]
            return Response({"scope": "global", "tiers": tiers, "members": [
                {"rank": i + 1, "user_id": u.id, "display_name": u.display_name, "avatar": _avatar(request, u),
                 "xp": u.stats.lifetime_xp, "is_me": u.id == request.user.id}
                for i, u in enumerate(top)
            ]})
        me = services.join_current_league(request.user)
        cycle = me.cycle
        members = list(cycle.members.select_related("user").order_by("-weekly_xp", "id"))
        n = len(members)
        out = []
        for i, m in enumerate(members, start=1):
            zone = "promotion" if i <= cycle.tier.promote_top else (
                "demotion" if i > n - cycle.tier.demote_bottom and n > cycle.tier.promote_top + cycle.tier.demote_bottom else "safe")
            out.append({"rank": i, "user_id": m.user_id, "display_name": m.user.display_name, "avatar": _avatar(request, m.user),
                        "xp": m.weekly_xp, "zone": zone, "is_me": m.user_id == request.user.id})
        return Response({"scope": "league", "tiers": tiers, "tier": {"code": cycle.tier.code, "name": cycle.tier.name},
                         "ends_at": cycle.end_at, "members": out})


class ItemSerializer(serializers.ModelSerializer):
    owned = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = ["id", "code", "name", "description", "image", "effect", "cost_scales", "cost_gems", "owned"]

    def get_owned(self, obj):
        inv = {i.item_id: i.quantity for i in self.context.get("inventory", [])}
        return inv.get(obj.id, 0)


@extend_schema(tags=["gamification"])
class ShopViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ItemSerializer
    queryset = Item.objects.filter(active=True)
    pagination_class = None

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if not getattr(self, "swagger_fake_view", False):
            ctx["inventory"] = list(UserInventory.objects.filter(user=self.request.user))
        return ctx

    @action(detail=True, methods=["post"])
    def buy(self, request, pk=None):
        item = self.get_object()
        try:
            inv = services.purchase(request.user, item)
        except services.ShopError as e:
            return Response({"detail": str(e), "errors": {}}, status=400)
        request.user.refresh_from_db(fields=["scales_balance", "gems_balance"])
        return Response({"item": item.code, "quantity": inv.quantity,
                         "scales": request.user.scales_balance, "gems": request.user.gems_balance})

    @action(detail=True, methods=["post"])
    def use(self, request, pk=None):
        item = self.get_object()
        try:
            boost = services.use_item(request.user, item)
        except services.ShopError as e:
            return Response({"detail": str(e), "errors": {}}, status=400)
        return Response({"item": item.code, "multiplier": boost.multiplier, "expires_at": boost.expires_at})


class XpHistoryView(APIView):
    @extend_schema(tags=["gamification"], responses={200: dict})
    def get(self, request):
        rows = XpTransaction.objects.filter(user=request.user)[:100]
        return Response([{"source": r.source, "amount": r.amount, "multiplier": r.multiplier, "note": r.note,
                          "created_at": r.created_at} for r in rows])


class PublicProfileStatsView(APIView):
    @extend_schema(tags=["gamification"], responses={200: dict})
    def get(self, request, user_id):
        user = get_object_or_404(get_user_model(), pk=user_id, is_active=True)
        stats = services.stats_for(user)
        member = LeagueMember.objects.filter(user=user).select_related("cycle__tier").order_by("-cycle__start_at").first()
        return Response({
            "user_id": user.id, "display_name": user.display_name, "avatar": _avatar(request, user),
            "lifetime_xp": stats.lifetime_xp, "level": stats.level, "streak": services.current_streak(user),
            "words_learned": stats.words_learned, "tier": member.cycle.tier.name if member else None,
            "badges": BadgeSerializer(Badge.objects.filter(userbadge__user=user), many=True, context={"user_id": user.id}).data,
        })


# ------------------------------------------------------------------ admin

class AdminBadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = "__all__"


class AdminItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class AdminTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeagueTier
        fields = "__all__"


@extend_schema(tags=["admin-gamification"])
class AdminBadgeViewSet(viewsets.ModelViewSet):
    serializer_class = AdminBadgeSerializer
    permission_classes = [IsStaffRole]
    queryset = Badge.objects.all()


@extend_schema(tags=["admin-gamification"])
class AdminItemViewSet(viewsets.ModelViewSet):
    serializer_class = AdminItemSerializer
    permission_classes = [IsStaffRole]
    queryset = Item.objects.all()


@extend_schema(tags=["admin-gamification"])
class AdminTierViewSet(viewsets.ModelViewSet):
    serializer_class = AdminTierSerializer
    permission_classes = [IsStaffRole]
    queryset = LeagueTier.objects.all()

    @action(detail=False, methods=["post"], url_path="close-week")
    def close_week(self, request):
        start, _ = services.week_bounds()
        closed = 0
        for cycle in LeagueCycle.objects.filter(status=LeagueCycle.Status.ACTIVE, end_at__lte=timezone.now()):
            services.close_cycle(cycle)
            closed += 1
        return Response({"closed": closed, "current_week_start": start})
