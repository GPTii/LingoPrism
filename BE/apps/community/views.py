from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Exists, F, OuterRef, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.permissions import IsStaffRole, require_verified_email
from apps.gamification import services as game
from apps.gamification.mascot import look
from apps.gamification.models import DailyQuest
from apps.learning.models import PersonalWord
from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.vocab.models import Word
from apps.vocab.services import card, personal_map, resolve_target, words_for_target
from apps.chat.services import can_message
from apps.core.throttles import ActionThrottleMixin

from .models import (
    FriendRequest, Group, GroupMember, Post, PostBookmark, PostComment, PostLike, PostReport, PostWord, UserBlock,
    UserFollow, UserReport, blocked_between, friend_ids, friendship, hidden_user_ids,
)

User = get_user_model()


class NotKid(permissions.BasePermission):
    message = "Tài khoản trẻ em không dùng được tính năng này"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(request.user, "learner_type", "adult") != "kid" or request.user.is_staff_role


def author(request, user):
    return {"id": user.id, "public_id": user.public_id, "display_name": user.display_name, "avatar": user.avatar_url(request),
            "mascot": look(user)}


def no_kids(request):
    """Social lists are for adults: NotKid lets reads through, so the read endpoints that show strangers check here."""
    if getattr(request.user, "learner_type", "adult") == "kid" and not request.user.is_staff_role:
        raise PermissionDenied(NotKid.message)


def friend_status(me, other):
    """none | friends | outgoing (I asked) | incoming (they asked), and the request behind it."""
    fr = friendship(me.id, other.id)
    if not fr:
        return "none", None
    if fr.status == FriendRequest.Status.ACCEPTED:
        return "friends", fr
    return ("outgoing" if fr.from_user_id == me.id else "incoming"), fr


def person(request, user):
    """A learner in a list (search, friends, requests): who they are and where I stand with them."""
    me = request.user
    state, fr = friend_status(me, user)
    return {**author(request, user), "bio": user.bio, "active_language": user.active_language,
            "friend_status": state, "friend_request_id": fr.id if fr else None,
            "is_following": UserFollow.objects.filter(follower=me, following=user).exists()}


def accept_friend(request, fr):
    fr.status, fr.responded_at = FriendRequest.Status.ACCEPTED, timezone.now()
    fr.save(update_fields=["status", "responded_at"])
    me = request.user
    count_friends(fr.from_user, fr.to_user)
    notify(fr.from_user, Notification.Kind.FRIEND_ACCEPT, f"{me.display_name} đã đồng ý kết bạn với bạn",
           "Giờ hai bạn có thể nhắn tin cho nhau.", data={"route": f"/community/users/{me.id}", "user_id": me.id})
    return {"friend_status": "friends", "friend_request_id": fr.id}


def count_friends(*users):
    """Keep the friend counter (for the friends badges) in step after a friendship starts or ends."""
    from apps.gamification.models import UserStats

    for u in users:
        UserStats.objects.update_or_create(user=u, defaults={"friends": len(friend_ids(u.id))})
        game.check_badges(u)


# ------------------------------------------------------------------ posts

class PostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(read_only=True, default=0)
    comment_count = serializers.IntegerField(read_only=True, default=0)
    liked = serializers.BooleanField(read_only=True, default=False)
    saved = serializers.BooleanField(read_only=True, default=False)
    words = serializers.SerializerMethodField()
    word_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)

    class Meta:
        model = Post
        fields = ["id", "author", "image", "caption", "topic_label", "visibility", "status", "save_count",
                  "like_count", "comment_count", "liked", "saved", "words", "word_ids", "detection", "created_at"]
        read_only_fields = ["id", "author", "status", "save_count", "created_at"]

    def get_author(self, obj):
        return author(self.context["request"], obj.user)

    def get_words(self, obj):
        request = self.context["request"]
        target = resolve_target(request)
        words = words_for_target(Word.objects.filter(postword__post=obj), request.user, target)
        personal = personal_map(request.user, [w.id for w in words], target)
        return [card(w, target, personal.get(w.id), request) for w in words]

    def validate_detection(self, detection):
        # a post can only point at the author's own photo
        if detection and detection.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Ảnh nhận diện không thuộc về bạn.")
        return detection

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
        fields = ["id", "author", "kind", "content", "sticker", "can_delete", "created_at"]
        read_only_fields = ["id", "author", "created_at"]

    can_delete = serializers.SerializerMethodField()

    def get_can_delete(self, obj):
        me = self.context["request"].user
        return me.id in (obj.user_id, obj.post.user_id) or me.is_staff_role

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
class PostViewSet(ActionThrottleMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                  mixins.DestroyModelMixin, viewsets.GenericViewSet):
    throttle_scopes = {"create": "upload", "report": "report"}
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
        ).select_related("user__mascot").annotate(
            like_count=Count("likes", distinct=True),
            comment_count=Count("comments", filter=Q(comments__hidden=False), distinct=True),
            liked=Exists(PostLike.objects.filter(post=OuterRef("pk"), user=user)),
            saved=Exists(PostBookmark.objects.filter(post=OuterRef("pk"), user=user)),
        ).exclude(user_id__in=hidden_user_ids(user.id))
        params = self.request.query_params
        if params.get("user"):
            qs = qs.filter(user_id=params["user"])
        if params.get("following") == "1":
            qs = qs.filter(user_id__in=following)
        if params.get("saved") == "1":  # "Bài đã lưu", newest saved first
            return qs.filter(bookmarks__user=user).order_by("-bookmarks__created_at")
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        require_verified_email(self.request.user)
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
            game.bump_stat(request.user, "cheers")
            if post.user_id != request.user.id:
                notify(post.user, Notification.Kind.LIKE, f"{request.user.display_name} đã thả tim bài viết của bạn",
                       data={"route": f"/community/posts/{post.id}"})
        return Response({"liked": True})

    @action(detail=True, methods=["get", "post"], serializer_class=CommentSerializer)
    def comments(self, request, pk=None):
        post = self.get_object()
        if request.method == "GET":
            qs = post.comments.filter(hidden=False).select_related("user__mascot")
            return Response(CommentSerializer(qs, many=True, context={"request": request}).data)
        require_verified_email(request.user)
        ser = CommentSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        comment = ser.save(post=post, user=request.user)
        game.progress_quest(request.user, DailyQuest.Kind.ENGAGE_COMMUNITY)
        game.bump_stat(request.user, "cheers")
        if post.user_id != request.user.id:
            notify(post.user, Notification.Kind.COMMENT, f"{request.user.display_name} đã bình luận bài viết của bạn",
                   comment.content[:120], data={"route": f"/community/posts/{post.id}"})
        return Response(CommentSerializer(comment, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post", "delete"])
    def bookmark(self, request, pk=None):
        """Keep the post in "Bài đã lưu" (POST) or take it out (DELETE)."""
        post = self.get_object()
        if request.method == "DELETE":
            PostBookmark.objects.filter(post=post, user=request.user).delete()
            return Response({"saved": False})
        PostBookmark.objects.get_or_create(post=post, user=request.user)
        return Response({"saved": True})

    @action(detail=True, methods=["delete"], url_path=r"comments/(?P<comment_id>\d+)")
    def delete_comment(self, request, pk=None, comment_id=None):
        """The comment's writer, the post's author or staff can remove a comment."""
        post = self.get_object()
        comment = get_object_or_404(PostComment, pk=comment_id, post=post)
        if request.user.id not in (comment.user_id, post.user_id) and not request.user.is_staff_role:
            raise PermissionDenied("Bạn chỉ xoá được bình luận của mình hoặc trên bài của mình.")
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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

class UserReportSerializer(serializers.ModelSerializer):
    block = serializers.BooleanField(default=False, write_only=True)
    thread = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = UserReport
        fields = ["id", "reason", "details", "block", "thread", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate(self, attrs):
        if attrs["reason"] == "other" and len(attrs.get("details", "").strip()) < 10:
            raise serializers.ValidationError('Hãy mô tả chi tiết khi chọn lý do "Khác".')
        return attrs


def block_user(me, target):
    UserBlock.objects.get_or_create(blocker=me, blocked=target)
    UserFollow.objects.filter(Q(follower=me, following=target) | Q(follower=target, following=me)).delete()


@extend_schema(tags=["community"])
class CommunityUserViewSet(ActionThrottleMixin, viewsets.GenericViewSet):
    throttle_scopes = {"report": "report"}
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.Serializer
    permission_classes = [permissions.IsAuthenticated, NotKid]

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        no_kids(request)
        user = self.get_object()
        stats = game.stats_for(user)
        state, fr = friend_status(request.user, user)
        recent = Post.objects.filter(user=user, status=Post.Status.ACTIVE).order_by("-created_at")[:12]
        return Response({
            **author(request, user), "bio": user.bio,
            "friend_status": state, "friend_request_id": fr.id if fr else None,
            "friend_message": fr.message if fr and state == "incoming" else "",
            "friends": len(friend_ids(user.id)),
            "followers": UserFollow.objects.filter(following=user).count(),
            "following": UserFollow.objects.filter(follower=user).count(),
            "posts": Post.objects.filter(user=user, status=Post.Status.ACTIVE).count(),
            "is_following": UserFollow.objects.filter(follower=request.user, following=user).exists(),
            "can_message": can_message(request.user, user),
            "blocked": UserBlock.objects.filter(blocker=request.user, blocked=user).exists(),
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
        if blocked_between(request.user.id, target.id):
            return Response({"detail": "Bạn không thể theo dõi người này.", "errors": {}}, status=400)
        _, created = UserFollow.objects.get_or_create(follower=request.user, following=target)
        if created:
            notify(target, Notification.Kind.FOLLOW, f"{request.user.display_name} đã theo dõi bạn",
                   data={"route": f"/community/users/{request.user.id}"})
        return Response({"following": True})


    # ---- finding people, friends

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Find a learner by their 8-digit ID (exact) or by name (2+ letters). Adults only, never blocked people."""
        no_kids(request)
        q = request.query_params.get("q", "").strip().lstrip("#")
        if len(q) < 2:
            return Response([])
        qs = (User.objects.filter(is_active=True, status=User.Status.ACTIVE, role=User.Role.LEARNER)
              .exclude(learner_type="kid").exclude(id__in={request.user.id, *hidden_user_ids(request.user.id)}))
        qs = qs.filter(public_id=q) if q.isdigit() and len(q) == 8 else qs.filter(display_name__icontains=q)
        return Response([person(request, u) for u in qs.order_by("display_name")[:20]])

    @action(detail=True, methods=["post", "delete"])
    def friend(self, request, pk=None):
        """POST: send a friend request with an optional hello (`message`); if they had already asked me, we become
        friends at once. DELETE: cancel my request, decline theirs, or end the friendship."""
        me, target = request.user, self.get_object()
        state, fr = friend_status(me, target)
        if request.method == "DELETE":
            if fr:
                fr.delete()
                count_friends(me, target)
            return Response({"friend_status": "none"})
        require_verified_email(me)
        if target.id == me.id or target.learner_type == "kid" or target.role != User.Role.LEARNER:
            return Response({"detail": "Bạn không thể kết bạn với tài khoản này.", "errors": {}}, status=400)
        if blocked_between(me.id, target.id):
            return Response({"detail": "Bạn không thể kết bạn với người này.", "errors": {}}, status=400)
        with transaction.atomic():
            # lock both people, lower id first: a double tap, or both pressing "add friend" at the same moment, would
            # otherwise create the request twice (a 500 on the unique pair, or two crossed pending requests)
            list(User.objects.select_for_update().filter(pk__in=[me.id, target.id]).order_by("pk"))
            state, fr = friend_status(me, target)
            if state == "incoming":
                return Response(accept_friend(request, fr))
            if state == "none":
                fr = FriendRequest.objects.create(from_user=me, to_user=target, message=str(request.data.get("message", ""))[:200])
                notify(target, Notification.Kind.FRIEND_REQUEST, f"{me.display_name} muốn kết bạn với bạn", fr.message,
                       data={"route": "/friends?tab=incoming", "action": "friend_request", "request_id": fr.id, "user_id": me.id})
                state = "outgoing"
        return Response({"friend_status": state, "friend_request_id": fr.id})

    @action(detail=False, methods=["get"])
    def friends(self, request):
        """My friends, newest first."""
        no_kids(request)
        me = request.user
        rows = (FriendRequest.objects.filter(Q(from_user=me) | Q(to_user=me), status=FriendRequest.Status.ACCEPTED)
                .select_related("from_user", "to_user").order_by("-responded_at"))
        hidden = hidden_user_ids(me.id)
        out = []
        for fr in rows:
            other = fr.to_user if fr.from_user_id == me.id else fr.from_user
            if other.is_active and other.id not in hidden:
                out.append({**person(request, other), "since": fr.responded_at})
        return Response(out)

    @action(detail=False, methods=["get"], url_path="friend-requests")
    def friend_requests(self, request):
        """`?box=incoming` (default): requests waiting for my answer; `?box=outgoing`: the ones I sent."""
        no_kids(request)
        me = request.user
        incoming = request.query_params.get("box", "incoming") != "outgoing"
        qs = (FriendRequest.objects.filter(status=FriendRequest.Status.PENDING, **({"to_user": me} if incoming else {"from_user": me}))
              .select_related("from_user", "to_user"))
        return Response([{"id": fr.id, "message": fr.message, "created_at": fr.created_at,
                          "user": person(request, fr.from_user if incoming else fr.to_user)} for fr in qs])

    @action(detail=False, methods=["post"], url_path=r"friend-requests/(?P<req_id>\d+)/(?P<decision>accept|decline)")
    def answer_friend_request(self, request, req_id=None, decision=None):
        fr = get_object_or_404(FriendRequest, pk=req_id, to_user=request.user)
        if fr.status != FriendRequest.Status.PENDING:
            return Response({"friend_status": "friends", "friend_request_id": fr.id})
        if decision == "decline":  # the sender is not told; they can ask again later
            fr.delete()
            return Response({"friend_status": "none"})
        return Response(accept_friend(request, fr))

    @action(detail=False, methods=["get"])
    def suggestions(self, request):
        """Learners to follow: adults learning the same language first, then the most active lately; never someone
        already followed, blocked either way, a child or staff."""
        me = request.user
        if me.learner_type == "kid":  # children are never shown strangers to follow
            return Response([])
        skip = {me.id, *UserFollow.objects.filter(follower=me).values_list("following_id", flat=True), *hidden_user_ids(me.id)}
        qs = (User.objects.filter(is_active=True, role=User.Role.LEARNER).exclude(learner_type="kid").exclude(id__in=skip)
              .select_related("stats")
              .annotate(follows_me=Exists(UserFollow.objects.filter(follower=OuterRef("pk"), following=me)))
              .order_by("-follows_me", F("stats__last_active_date").desc(nulls_last=True), "-stats__lifetime_xp"))
        same = list(qs.filter(active_language=me.active_language)[:8])
        people = same + list(qs.exclude(active_language=me.active_language)[:8 - len(same)]) if len(same) < 8 else same
        return Response([{**author(request, u), "active_language": u.active_language, "follows_me": u.follows_me,
                          "lifetime_xp": getattr(getattr(u, "stats", None), "lifetime_xp", 0)} for u in people])

    @action(detail=True, methods=["post", "delete"])
    def block(self, request, pk=None):
        """Block (POST) or unblock (DELETE) a learner. Blocking also ends following in both directions."""
        target = self.get_object()
        if target.id == request.user.id:
            return Response({"detail": "Bạn không thể chặn chính mình.", "errors": {}}, status=400)
        if request.method == "DELETE":
            UserBlock.objects.filter(blocker=request.user, blocked=target).delete()
            return Response({"blocked": False})
        block_user(request.user, target)
        return Response({"blocked": True})

    @action(detail=True, methods=["post"], serializer_class=UserReportSerializer)
    def report(self, request, pk=None):
        """Report a learner to the moderators. With `thread`, the last 30 messages of that conversation are kept as
        evidence (only a conversation between these two people). `block` also blocks them right away."""
        from apps.chat.models import DirectThread

        target = self.get_object()
        if target.id == request.user.id:
            return Response({"detail": "Bạn không thể báo cáo chính mình.", "errors": {}}, status=400)
        ser = UserReportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if UserReport.objects.filter(reporter=request.user, reported=target, status=UserReport.Status.PENDING).exists():
            return Response({"detail": "Bạn đã báo cáo người này, đội ngũ kiểm duyệt đang xem xét.", "errors": {}}, status=400)
        thread, evidence = None, []
        if data.get("thread"):
            a, b = sorted([request.user.id, target.id])
            thread = get_object_or_404(DirectThread, pk=data["thread"], user_a_id=a, user_b_id=b)
            last = list(thread.messages.select_related("sender").order_by("-created_at", "-id")[:30])
            evidence = [{"sender": m.sender.display_name, "sender_id": m.sender_id, "content": m.content,
                         "created_at": m.created_at.isoformat()} for m in reversed(last)]
        UserReport.objects.create(reporter=request.user, reported=target, reason=data["reason"],
                                  details=data.get("details", ""), thread=thread, evidence=evidence)
        if data.get("block"):
            block_user(request.user, target)
        return Response({"detail": "Đã gửi báo cáo. Đội ngũ kiểm duyệt sẽ xem xét sớm nhất.",
                         "blocked": bool(data.get("block"))}, status=201)


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
class GroupViewSet(ActionThrottleMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                   mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    throttle_scopes = {"create": "upload"}
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
        require_verified_email(self.request.user)
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
        if created:
            for leader in group.members.filter(role="leader").select_related("user"):
                if status_value == "pending":
                    notify(leader.user, Notification.Kind.GROUP_REQUEST, f"{request.user.display_name} xin vào nhóm {group.name}",
                           m.request_message, data={"route": f"/community/groups/{group.id}", "action": "group_request",
                                                    "group_id": group.id, "member_id": m.id, "user_id": request.user.id})
                else:
                    notify(leader.user, Notification.Kind.GROUP, f"{request.user.display_name} đã tham gia nhóm {group.name}",
                           data={"route": f"/community/groups/{group.id}", "user_id": request.user.id})
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
        qs = group.members.select_related("user__mascot").order_by("role", "joined_at")
        if not GroupMember.objects.filter(group=group, user=request.user, role="leader").exists():
            qs = qs.filter(status="active")
        return Response(MemberSerializer(qs, many=True, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path=r"members/(?P<member_id>\d+)/(?P<decision>approve|reject|remove)")
    def moderate(self, request, pk=None, member_id=None, decision=None):
        group = self.get_object()
        self._leader(group)
        m = get_object_or_404(GroupMember, pk=member_id, group=group)
        if decision == "approve":
            if m.status != "active":
                m.status = "active"
                m.save(update_fields=["status"])
                notify(m.user, Notification.Kind.GROUP, f"Bạn đã được duyệt vào nhóm {group.name}",
                       data={"route": f"/community/groups/{group.id}"})
        else:
            if m.role == "leader":
                return Response({"detail": "Không thể xoá trưởng nhóm.", "errors": {}}, status=400)
            if decision == "reject" and m.status == "pending":
                notify(m.user, Notification.Kind.GROUP, f"Yêu cầu vào nhóm {group.name} chưa được duyệt",
                       "Bạn có thể tìm nhóm khác hoặc xin lại sau.", data={"route": "/community?tab=groups"})
            m.delete()
        return Response({"ok": True, "status": "active" if decision == "approve" else "removed"})


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


class AdminUserReportSerializer(serializers.ModelSerializer):
    reporter_name = serializers.CharField(source="reporter.display_name", read_only=True)
    reporter_email = serializers.CharField(source="reporter.email", read_only=True)
    reported_name = serializers.CharField(source="reported.display_name", read_only=True)
    reported_email = serializers.CharField(source="reported.email", read_only=True)
    reported_status = serializers.CharField(source="reported.status", read_only=True)
    reports_against = serializers.SerializerMethodField()

    class Meta:
        model = UserReport
        fields = ["id", "reporter", "reporter_name", "reporter_email", "reported", "reported_name", "reported_email",
                  "reported_status", "reports_against", "reason", "details", "evidence", "status", "created_at"]
        read_only_fields = fields

    def get_reports_against(self, obj):
        """How many different people reported this learner: one report can be a quarrel, several is a pattern."""
        return UserReport.objects.filter(reported_id=obj.reported_id).values("reporter").distinct().count()


@extend_schema(tags=["admin-community"])
class AdminUserReportViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AdminUserReportSerializer
    permission_classes = [IsStaffRole]
    filterset_fields = ["status", "reason"]
    queryset = UserReport.objects.select_related("reporter", "reported")

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """`lock: true` locks the reported account (it can no longer sign in) and closes every pending report about
        them; otherwise only this report is dismissed. The reporter is told it was handled, never how."""
        report = self.get_object()
        if request.data.get("lock"):
            target = report.reported
            if target.role != User.Role.LEARNER:
                return Response({"detail": "Chỉ khoá được tài khoản học viên từ đây.", "errors": {}}, status=400)
            target.status = User.Status.LOCKED
            target.save(update_fields=["status"])
            handled = list(UserReport.objects.filter(reported=target, status="pending").select_related("reporter"))
            UserReport.objects.filter(id__in=[r.id for r in handled]).update(status="resolved", handled_by=request.user)
        else:
            report.status, report.handled_by = UserReport.Status.DISMISSED, request.user
            report.save(update_fields=["status", "handled_by"])
            handled = [report]
        for r in {r.reporter_id: r for r in handled}.values():
            notify(r.reporter, Notification.Kind.SYSTEM, "Báo cáo của bạn đã được xem xét",
                   "Cảm ơn bạn đã giúp cộng đồng LingoPrism an toàn hơn.")
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
