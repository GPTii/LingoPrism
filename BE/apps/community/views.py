from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import IsStaffRole
from apps.gamification import services as game
from apps.gamification.models import DailyQuest
from apps.learning.models import PersonalWord
from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.vocab.models import Word
from apps.vocab.services import card, personal_map, resolve_target, words_for_target

from .models import Group, GroupMember, Post, PostComment, PostLike, PostReport, PostWord, UserFollow

User = get_user_model()


class NotKid(permissions.BasePermission):
    message = "Tài khoản trẻ em không dùng được tính năng này"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, "learner_type", "adult") != "kid" or request.user.is_staff_role


def author(request, user):
    return {"id": user.id, "display_name": user.display_name, "avatar": user.avatar_url(request)}


# ------------------------------------------------------------------ posts

class PostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(read_only=True, default=0)
    comment_count = serializers.IntegerField(read_only=True, default=0)
    liked = serializers.BooleanField(read_only=True, default=False)
    words = serializers.SerializerMethodField()
    word_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Post
        fields = ["id", "author", "image", "caption", "topic_label", "visibility", "status", "save_count",
                  "like_count", "comment_count", "liked", "words", "word_ids", "detection", "created_at"]
        read_only_fields = ["id", "author", "status", "save_count", "created_at"]

    def get_author(self, obj):
        return author(self.context["request"], obj.user)

    def get_words(self, obj):
        request = self.context["request"]
        target = resolve_target(request)
        words = words_for_target(Word.objects.filter(postword__post=obj), request.user, target)
        personal = personal_map(request.user, [w.id for w in words], target)
        return [card(w, target, personal.get(w.id), request) for w in words]

    def create(self, validated):
        word_ids = validated.pop("word_ids", [])
        post = Post.objects.create(**validated)
        for i, wid in enumerate(dict.fromkeys(word_ids)):
            if Word.objects.filter(id=wid).exists():
                PostWord.objects.create(post=post, word_id=wid, order=i)
        return post


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ["id", "author", "kind", "content", "sticker", "created_at"]
        read_only_fields = ["id", "author", "created_at"]

    def get_author(self, obj):
        return author(self.context["request"], obj.user)

    def validate(self, attrs):
        if attrs.get("kind", "text") == "text" and not attrs.get("content", "").strip():
            raise serializers.ValidationError("Bình luận không được để trống.")
        if attrs.get("kind") == "sticker" and not game.owns_sticker(self.context["request"].user, attrs.get("sticker", "")):
            raise serializers.ValidationError("Bạn chưa sở hữu sticker này")
        return attrs


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReport
        fields = ["id", "reason", "details", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, attrs):
        if attrs["reason"] == "other" and len(attrs.get("details", "").strip()) < 10:
            raise serializers.ValidationError('Hãy mô tả chi tiết khi chọn lý do "Khác".')
        return attrs


@extend_schema(tags=["community"])
class PostViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                  mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, NotKid]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Post.objects.none()
        user = self.request.user
        following = UserFollow.objects.filter(follower=user).values("following_id")
        qs = Post.objects.filter(status=Post.Status.ACTIVE).filter(
            Q(visibility=Post.Visibility.PUBLIC) | Q(user=user) | Q(user_id__in=following)
        ).select_related("user").annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", filter=Q(comments__hidden=False), distinct=True),
            liked=Exists(PostLike.objects.filter(post=OuterRef("pk"), user=user)),
        )
        params = self.request.query_params
        if params.get("user"):
            qs = qs.filter(user_id=params["user"])
        if params.get("following") == "1":
            qs = qs.filter(user_id__in=following)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        game.bump_stat(self.request.user, "posts")
        game.progress_quest(self.request.user, DailyQuest.Kind.POST_COMMUNITY_IMAGE)

    def perform_destroy(self, instance):
        if instance.user_id != self.request.user.id and not self.request.user.is_staff_role:
            raise PermissionDenied("Bạn chỉ có thể xoá bài viết của mình.")
        instance.delete()

    @action(detail=True, methods=["post", "delete"])
    def like(self, request, pk=None):
        post = self.get_object()
        if request.method == "DELETE":
            PostLike.objects.filter(post=post, user=request.user).delete()
            return Response({"liked": False})
        _, created = PostLike.objects.get_or_create(post=post, user=request.user)
        if created:
            game.progress_quest(request.user, DailyQuest.Kind.ENGAGE_COMMUNITY)
            if post.user_id != request.user.id:
                notify(post.user, Notification.Kind.LIKE, f"{request.user.display_name} đã thả tim bài viết của bạn",
                       data={"route": f"/community/posts/{post.id}"})
        return Response({"liked": True})

    @action(detail=True, methods=["get", "post"], serializer_class=CommentSerializer)
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == "GET":
            qs = post.comments.filter(hidden=False).select_related("user")
            return Response(CommentSerializer(qs, many=True, context={"request": request}).data)
        ser = CommentSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        comment = ser.save(post=post, user=request.user)
        game.progress_quest(request.user, DailyQuest.Kind.ENGAGE_COMMUNITY)
        if post.user_id != request.user.id:
            notify(post.user, Notification.Kind.COMMENT, f"{request.user.display_name} đã bình luận bài viết của bạn",
                   comment.content[:120], data={"route": f"/community/posts/{post.id}"})
        return Response(CommentSerializer(comment, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], serializer_class=ReportSerializer)
    def report(self, request, pk=None):
        post = self.get_object()
        ser = ReportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if PostReport.objects.filter(post=post, reporter=request.user).exists():
            return Response({"detail": "Bạn đã gửi báo cáo cho bài đăng này.", "errors": {}}, status=400)
        ser.save(post=post, reporter=request.user)
        return Response({"detail": "Đội ngũ kiểm duyệt sẽ xem xét sớm nhất."}, status=201)

    @action(detail=True, methods=["post"], url_path="save-words")
    def save_words(self, request, pk=None):
        post = self.get_object()
        target = resolve_target(request)
        words = words_for_target(Word.objects.filter(postword__post=post), request.user, target)
        added = 0
        with transaction.atomic():
            for w in words:
                _, created = PersonalWord.objects.get_or_create(
                    user=request.user, word=w, language=target.learn,
                    defaults={"source": PersonalWord.Source.COMMUNITY, "source_ref": str(post.id)})
                added += created
            if added:
                Post.objects.filter(pk=post.pk).update(save_count=post.save_count + 1)
        return Response({"added": added})


# ------------------------------------------------------------------ users / follows

@extend_schema(tags=["community"])
class CommunityUserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.Serializer
    permission_classes = [permissions.IsAuthenticated, NotKid]

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        user = self.get_object()
        stats = game.stats_for(user)
        recent = Post.objects.filter(user=user, status=Post.Status.ACTIVE).order_by("-created_at")[:12]
        return Response({
            **author(request, user), "bio": user.bio,
            "followers": UserFollow.objects.filter(following=user).count(),
            "following": UserFollow.objects.filter(follower=user).count(),
            "posts": Post.objects.filter(user=user, status=Post.Status.ACTIVE).count(),
            "is_following": UserFollow.objects.filter(follower=request.user, following=user).exists(),
            "lifetime_xp": stats.lifetime_xp, "streak": game.current_streak(user),
            "recent_posts": [{"id": p.id, "image": request.build_absolute_uri(p.image.url)} for p in recent],
            "groups": [{"id": m.group_id, "name": m.group.name} for m in
                       GroupMember.objects.filter(user=user, status="active").select_related("group")[:10]],
        })

    @action(detail=True, methods=["post", "delete"])
    def follow(self, request, pk=None):
        target = self.get_object()
        if target.id == request.user.id or target.learner_type == "kid":
            return Response({"detail": "Bạn không thể theo dõi tác giả này.", "errors": {}}, status=400)
        if request.method == "DELETE":
            UserFollow.objects.filter(follower=request.user, following=target).delete()
            return Response({"following": False})
        _, created = UserFollow.objects.get_or_create(follower=request.user, following=target)
        if created:
            notify(target, Notification.Kind.FOLLOW, f"{request.user.display_name} đã theo dõi bạn",
                   data={"route": f"/community/users/{request.user.id}"})
        return Response({"following": True})


# ------------------------------------------------------------------ groups

class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True, default=0)
    my_status = serializers.SerializerMethodField()
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ["id", "name", "description", "icon", "require_approval", "member_count", "my_status", "my_role",
                  "created_by", "created_at"]
        read_only_fields = ["id", "created_by", "created_at"]

    def _membership(self, obj):
        user = self.context["request"].user
        return next((m for m in obj.members.all() if m.user_id == user.id), None)

    def get_my_status(self, obj):
        m = self._membership(obj)
        return m.status if m else None

    def get_my_role(self, obj):
        m = self._membership(obj)
        return m.role if m else None


class MemberSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    weekly_xp = serializers.SerializerMethodField()
    lifetime_xp = serializers.SerializerMethodField()

    class Meta:
        model = GroupMember
        fields = ["id", "user", "role", "status", "request_message", "joined_at", "weekly_xp", "lifetime_xp"]

    def get_user(self, obj):
        return author(self.context["request"], obj.user)

    def get_weekly_xp(self, obj):
        from apps.gamification.models import LeagueMember
        from apps.gamification.services import week_bounds

        m = LeagueMember.objects.filter(user=obj.user, cycle__start_at=week_bounds()[0]).first()
        return m.weekly_xp if m else 0

    def get_lifetime_xp(self, obj):
        stats = getattr(obj.user, "stats", None)
        return stats.lifetime_xp if stats else 0


@extend_schema(tags=["groups"])
class GroupViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                   mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, NotKid]
    search_fields = ["name", "description"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Group.objects.none()
        qs = Group.objects.filter(status=Group.Status.ACTIVE).annotate(
            member_count=Count("members", filter=Q(members__status="active"), distinct=True)
        ).prefetch_related("members")
        if self.request.query_params.get("mine") == "1":
            qs = qs.filter(members__user=self.request.user, members__status="active")
        return qs.order_by("-created_at")

    def _leader(self, group):
        if not GroupMember.objects.filter(group=group, user=self.request.user, role="leader").exists() and not self.request.user.is_staff_role:
            raise PermissionDenied("Chỉ trưởng nhóm mới có quyền này.")

    def perform_create(self, serializer):
        group = serializer.save(created_by=self.request.user)
        GroupMember.objects.create(group=group, user=self.request.user, role="leader", status="active")

    def perform_update(self, serializer):
        self._leader(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._leader(instance)
        instance.delete()

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        group = self.get_object()
        status_value = "pending" if group.require_approval else "active"
        m, created = GroupMember.objects.get_or_create(
            group=group, user=request.user,
            defaults={"status": status_value, "request_message": request.data.get("message", "")[:200]})
        if created and status_value == "pending":
            for leader in group.members.filter(role="leader").select_related("user"):
                notify(leader.user, Notification.Kind.SYSTEM, f"{request.user.display_name} xin vào nhóm {group.name}",
                       data={"route": f"/community/groups/{group.id}"})
        return Response({"status": m.status})

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        group = self.get_object()
        m = GroupMember.objects.filter(group=group, user=request.user).first()
        if m and m.role == "leader" and group.members.filter(role="leader").count() == 1 and group.members.count() > 1:
            return Response({"detail": "Hãy chuyển quyền trưởng nhóm trước khi rời nhóm", "errors": {}}, status=400)
        if m:
            m.delete()
        return Response({"detail": "Bạn đã rời khỏi nhóm."})

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        group = self.get_object()
        qs = group.members.select_related("user").order_by("role", "joined_at")
        if not GroupMember.objects.filter(group=group, user=request.user, role="leader").exists():
            qs = qs.filter(status="active")
        return Response(MemberSerializer(qs, many=True, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path=r"members/(?P<member_id>\d+)/(?P<decision>approve|reject|remove)")
    def moderate(self, request, pk=None, member_id=None, decision=None):
        group = self.get_object()
        self._leader(group)
        m = get_object_or_404(GroupMember, pk=member_id, group=group)
        if decision == "approve":
            m.status = "active"
            m.save(update_fields=["status"])
            notify(m.user, Notification.Kind.SYSTEM, f"Bạn đã được duyệt vào nhóm {group.name}",
                   data={"route": f"/community/groups/{group.id}"})
        else:
            m.delete()
        return Response({"ok": True})


# ------------------------------------------------------------------ moderation (staff)

class AdminReportSerializer(serializers.ModelSerializer):
    reporter_email = serializers.CharField(source="reporter.email", read_only=True)
    post_caption = serializers.CharField(source="post.caption", read_only=True)
    post_image = serializers.ImageField(source="post.image", read_only=True)
    post_author = serializers.CharField(source="post.user.email", read_only=True)
    post_status = serializers.CharField(source="post.status", read_only=True)

    class Meta:
        model = PostReport
        fields = ["id", "post", "post_caption", "post_image", "post_author", "post_status", "reporter_email",
                  "reason", "details", "status", "created_at"]
        read_only_fields = fields


@extend_schema(tags=["admin-community"])
class AdminPostReportViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AdminReportSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["status", "reason"]
    queryset = PostReport.objects.select_related("post__user", "reporter")

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        report = self.get_object()
        hide = request.data.get("hide_post", True)
        if hide:
            Post.objects.filter(pk=report.post_id).update(status=Post.Status.HIDDEN)
            PostReport.objects.filter(post_id=report.post_id, status="pending").update(status="resolved", handled_by=request.user)
        else:
            report.status, report.handled_by = PostReport.Status.DISMISSED, request.user
            report.save(update_fields=["status", "handled_by"])
        return Response({"ok": True})


@extend_schema(tags=["admin-community"])
class AdminPostViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["status"]

    def get_queryset(self):
        return Post.objects.select_related("user").annotate(
            like_count=Count("likes", distinct=True), comment_count=Count("comments", distinct=True)
        ).order_by("-created_at")

    @action(detail=True, methods=["post"])
    def visibility(self, request, pk=None):
        post = self.get_object()
        post.status = Post.Status.HIDDEN if request.data.get("hidden", True) else Post.Status.ACTIVE
        post.save(update_fields=["status"])
        return Response({"status": post.status})
