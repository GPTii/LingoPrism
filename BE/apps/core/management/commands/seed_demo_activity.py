"""Realistic demo activity for every feature: learners with 5 weeks of study history and everything that follows
from it (spaced repetition, XP, streaks, quests, badges, weekly leagues, shop), photos recognised by the real YOLO
model, community posts, study groups, teacher support chats, exams, sentence practice and the children's reading course.

    python manage.py seed_demo_activity            # rebuilds the demo activity (keeps vocabulary, exams, POIs)

Rules followed so the demo never shows "test 1" style or invented language content:
* learner accounts are fictional people with ordinary Vietnamese names, on the demo domain @lingoprism.local;
* every word, sentence and translation shown comes from the verified database (Tatoeba sentences for essays);
* photos are the reviewed Wikimedia Commons word photos (credited), objects are found by the real detector;
* study history is replayed through the app's own scheduler and XP/quest rules, so all totals agree.
Only the activity of the demo accounts listed here is deleted and rebuilt.
"""
import random
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from PIL import Image

from apps.core import brand
from apps.accounts.models import User, UserGoal
from apps.chat.models import GroupMessage, SupportConversation, SupportMessage
from apps.community.models import Group, GroupMember, Post, PostComment, PostLike, PostReport, PostWord, UserFollow
from apps.detection.models import Detection, DetectionItem, Photo
from apps.gamification import services as game
from apps.gamification.models import (
    Badge, DailyProgress, DailyQuest, Item, LeagueCycle, LeagueMember, LeagueTier, MonthlyQuest, UserBadge,
    UserInventory, UserStats, XpTransaction,
)
from apps.gis.models import GeofenceEvent, Poi
from apps.learning.models import LearnerLevel, PersonalWord, ReviewLog, SentenceAttempt, SessionItem, StudySession
from apps.learning.scheduling import CardState, get_scheduler
from apps.algorithms.simulate import TrueMemory, word_difficulty
from apps.literacy import curriculum as cur
from apps.literacy.models import LiteracyAttempt, LiteracyProgress
from apps.notifications.models import Notification, NotificationSetting
from apps.quizzes.models import Answer, Exam, Question, Submission
from apps.vocab.models import ErrorReport, ExampleSentence, ReviewStatus, Word, WordTranslation

PASSWORD = "LingoPrism@2026"
DAYS = 35
AVATARS = brand.AVATARS  # Prismo in six colours

# learn: vi | en | zh ; script for zh ; p = chance to study on a given day ; new = words per learning session ;
# acc = first-try accuracy ; since = days ago they joined ; social = posts/comments in the community
LEARNERS = [
    # the three original demo accounts (login shown in README) get a history too
    dict(email="adult@lingoprism.local", name="Minh Anh", learn="zh", script="hans", p=.9, new=10, acc=.82, since=35, social=True,
         bio="Nhân viên văn phòng, học tiếng Trung để đi công tác Thượng Hải.", born=1997, gender="female", purpose="work"),
    dict(email="taiwan@lingoprism.local", name="Bảo Ngọc", learn="zh", script="hant", p=.8, new=8, acc=.78, since=30, social=True,
         bio="Chuẩn bị sang Đài Bắc du học thạc sĩ.", born=1999, gender="female", purpose="study"),
    dict(email="kid@lingoprism.local", name="Bé Na", learn="vi", p=.75, new=6, acc=.7, since=28, kid=True,
         born=2019, gender="female", purpose="study"),
    dict(email="thuha.nguyen@lingoprism.local", name="Nguyễn Thu Hà", learn="en", p=.92, new=12, acc=.86, since=35, social=True,
         bio="Giáo viên mầm non, ôn tiếng Anh mỗi tối 20 phút.", born=1994, gender="female", purpose="work"),
    dict(email="ducminh.tran@lingoprism.local", name="Trần Đức Minh", learn="en", p=.6, new=10, acc=.74, since=33, social=True,
         bio="Sinh viên CNTT năm 3 – mục tiêu IELTS 6.5.", born=2004, gender="male", purpose="study"),
    dict(email="hoangnam.le@lingoprism.local", name="Lê Hoàng Nam", learn="zh", script="hans", p=.7, new=10, acc=.8, since=35, social=True,
         bio="Làm logistics, hay làm việc với đối tác Quảng Châu.", born=1991, gender="male", purpose="work"),
    dict(email="ngocanh.pham@lingoprism.local", name="Phạm Ngọc Ánh", learn="en", p=.85, new=8, acc=.88, since=29, social=True,
         bio="Thích chụp ảnh đồ vật quanh nhà rồi học từ mới.", born=2001, gender="female", purpose="communication"),
    dict(email="thanhtung.vo@lingoprism.local", name="Võ Thanh Tùng", learn="en", p=.45, new=10, acc=.7, since=34,
         bio="Hướng dẫn viên du lịch Hội An.", born=1989, gender="male", purpose="work"),
    dict(email="mailinh.dang@lingoprism.local", name="Đặng Mai Linh", learn="zh", script="hant", p=.75, new=8, acc=.84, since=32, social=True,
         bio="Mê phim Đài Loan, học phồn thể kèm chú âm.", born=2000, gender="female", purpose="friends"),
    dict(email="quochuy.bui@lingoprism.local", name="Bùi Quốc Huy", learn="en", p=.95, new=15, acc=.9, since=35, social=True,
         bio="Kỹ sư phần mềm, luyện từ vựng trước giờ làm.", born=1995, gender="male", purpose="work"),
    dict(email="thaovy.do@lingoprism.local", name="Đỗ Thảo Vy", learn="zh", script="hans", p=.55, new=6, acc=.72, since=26, social=True,
         bio="Học sinh lớp 11, chọn tiếng Trung làm ngoại ngữ 2.", born=2009, gender="female", purpose="study"),
    dict(email="khanhlinh.ngo@lingoprism.local", name="Ngô Khánh Linh", learn="en", p=.7, new=10, acc=.83, since=31,
         bio="Nhân viên lễ tân khách sạn.", born=1998, gender="female", purpose="work"),
    dict(email="vanloc.duong@lingoprism.local", name="Dương Văn Lộc", learn="zh", script="hans", p=.65, new=8, acc=.76, since=35,
         bio="Chủ shop quần áo, nhập hàng từ Quảng Châu.", born=1987, gender="male", purpose="work"),
    dict(email="minhchau.ly@lingoprism.local", name="Lý Minh Châu", learn="en", p=.8, new=10, acc=.85, since=24, social=True,
         bio="Mẹ của hai bé, học cùng con mỗi tối.", born=1990, gender="female", purpose="communication"),
    dict(email="tanphat.huynh@lingoprism.local", name="Huỳnh Tấn Phát", learn="en", p=.35, new=8, acc=.66, since=30,
         bio="Thợ sửa điện lạnh, muốn đọc hiểu tài liệu máy.", born=1993, gender="male", purpose="work"),
    dict(email="thuydung.phan@lingoprism.local", name="Phan Thùy Dung", learn="zh", script="hant", p=.85, new=10, acc=.87, since=35, social=True,
         bio="Phiên dịch viên tự do, ôn từ vựng mỗi sáng.", born=1992, gender="female", purpose="work"),
    dict(email="haiyen.trinh@lingoprism.local", name="Trịnh Hải Yến", learn="en", p=.6, new=6, acc=.79, since=20,
         bio="Mới bắt đầu học lại tiếng Anh sau nhiều năm.", born=1985, gender="female", purpose="communication"),
    dict(email="anhkhoa.mai@lingoprism.local", name="Mai Anh Khoa", learn="zh", script="hans", p=.9, new=12, acc=.89, since=35, social=True,
         bio="Ôn thi HSK 3 cuối năm nay.", born=2003, gender="male", purpose="study"),
    # children learning to read and write Vietnamese (no community features for kids)
    dict(email="be.bin@lingoprism.local", name="Bé Bin", learn="vi", p=.8, new=5, acc=.68, since=30, kid=True, born=2019, gender="male"),
    dict(email="be.mit@lingoprism.local", name="Bé Mít", learn="vi", p=.6, new=5, acc=.62, since=21, kid=True, born=2020, gender="male"),
    dict(email="be.suri@lingoprism.local", name="Bé Su", learn="vi", p=.9, new=6, acc=.78, since=35, kid=True, born=2018, gender="female"),
    dict(email="be.tom@lingoprism.local", name="Bé Tôm", learn="en", p=.7, new=5, acc=.72, since=25, kid=True, born=2017, gender="male"),
]
STAFF = dict(email="thay.quanghuy@lingoprism.local", name="Thầy Quang Huy",
             bio="Giáo viên tiếng Trung, phụ trách hỗ trợ học viên HSK và TOCFL.")

# Captions never claim the (Wikimedia Commons) photo as the learner's own – the credit is added under each post.
CAPTIONS = [
    "Thử tính năng nhận diện với ảnh {w}, app nhận ra ngay 👍",
    "Từ mới hôm nay: {w}. Có ảnh minh họa dễ nhớ hơn hẳn!",
    "Ai đoán được đây là gì không? Đáp án: {w} 😆",
    "Ôn bài tối nay với {w}. Chúc mọi người học vui!",
    "Chia sẻ ảnh {w} mình dùng để ôn từ vựng tuần này.",
    "Học chủ đề này vui ghê, nhất là từ {w}.",
]
COMMENTS = [
    "Ảnh đẹp quá bạn ơi!", "Mình cũng vừa học từ này hôm qua 😄", "Hay quá, để mình thử chụp ở nhà.",
    "Cảm ơn bạn, nhờ ảnh mà nhớ từ nhanh hơn.", "Cố lên nha, giữ chuỗi học nhé!", "Góc này xinh ghê.",
    "Đọc phiên âm xong mới biết mình phát âm sai bấy lâu 😅", "Lưu lại để tối ôn.", "Tuần này mình đang đua hạng với bạn đó nha 😆",
    "Từ này dễ nhớ ghê.", "Bạn học mỗi ngày bao nhiêu từ vậy?", "Chuẩn luôn!",
]
REPLIES = ["Mình học 10 từ mỗi ngày, tối ôn lại 15 phút thôi.", "Cảm ơn bạn nhiều nha 🥰", "Cùng cố gắng nào!"]
STICKERS = ["sticker_ok", "sticker_love"]

GROUPS = [
    dict(name="Luyện HSK 1–3 mỗi ngày", learn="zh", icon=brand.group_icon(1),
         description="Mỗi ngày 10 từ HSK, tối 9h điểm danh và chia sẻ mẹo nhớ chữ Hán.",
         chat=["Chào cả nhóm, mình mới vào. Mọi người học HSK mấy rồi ạ?",
               "Mình đang ôn HSK 3, mỗi ngày 10–12 từ là vừa sức.",
               "Mẹo của mình: học theo bộ thủ, nhớ chữ nhanh hơn hẳn.",
               "Điểm danh tối nay: xong 10 từ chủ đề giao thông rồi nha ✅",
               "Mình hay nhầm thanh 3 với thanh 2, có ai bị giống không 😅",
               "Bật pinyin trên thẻ từ rồi nghe audio 2 lần là đỡ hẳn đó.",
               "Tuần này cả nhóm cố lên hạng Ánh Bạc nha!"]),
    dict(name="Tiếng Anh cho người đi làm", learn="en", icon=brand.group_icon(2),
         description="Học từ vựng văn phòng, khách sạn, du lịch – chia sẻ tình huống thực tế.",
         chat=["Hôm nay khách hỏi đường tới bảo tàng, may mà vừa học từ museum 😄",
               "Có ai luyện nghe bằng phần Luyện câu chưa? Mình thấy dạng nghe – sắp xếp hay lắm.",
               "Mình làm bài kiểm tra chủ đề Giao thông được 82%, còn sai mấy câu điền từ.",
               "Tối nay ai đua XP không, mình đang thua bạn Huy 40 XP 😂",
               "Chụp ảnh đồ trong văn phòng rồi học là nhớ lâu nhất.",
               "Cuối tuần mình tổng kết từ hay của nhóm nhé."]),
    dict(name="Học phồn thể & chú âm", learn="zh", icon=brand.group_icon(3), require_approval=True,
         description="Nhóm cho người học tiếng Trung Đài Loan: chữ phồn thể, chú âm, từ vựng riêng của Đài Loan.",
         chat=["Mọi người ơi, ở Đài Loan gọi xe đạp là 腳踏車 chứ không phải 自行車 đâu nha.",
               "Mình bật chú âm trong cài đặt rồi, nhìn quen dần.",
               "Phim Đài Loan tối qua có đúng mấy từ vừa học, vui ghê.",
               "Ai có mẹo nhớ ㄓㄔㄕㄖ không ạ?",
               "Đọc to theo audio nhiều lần là quen thôi bạn."]),
]
SUPPORT = [
    ("hoangnam.le@lingoprism.local", "Hỏi về cấp độ HSK",
     [("l", "Thầy ơi, em học xong gần hết cấp 1 rồi, có nên làm bài kiểm tra vượt cấp luôn không ạ?"),
      ("s", "Chào em, nếu em đã thuộc trên 80% từ cấp 1 thì làm bài kiểm tra vượt cấp nhé. Đúng từ 8/10 câu là mở cấp 2."),
      ("l", "Dạ em làm rồi, được 9/10 ạ. Cảm ơn thầy!")], "closed"),
    ("mailinh.dang@lingoprism.local", "Chú âm và pinyin",
     [("l", "Thầy ơi em học phồn thể, có nên học cả pinyin không hay chỉ chú âm thôi ạ?"),
      ("s", "Ở Đài Loan trường học dùng chú âm, nhưng biết pinyin giúp em tra từ điển và gõ máy dễ hơn. App hiện cả hai, em cứ bật chú âm trong phần cài đặt.")],
     "open"),
    ("ducminh.tran@lingoprism.local", "Không nghe được audio",
     [("l", "Cô ơi máy em bấm loa không có tiếng đọc tiếng Anh ạ."),
      ("s", "Em kiểm tra giúp cô: trình duyệt Chrome trên Windows cần có giọng đọc tiếng Anh. Em thử Edge hoặc vào Cài đặt > Thời gian & ngôn ngữ > Giọng nói để thêm giọng nhé."),
      ("l", "Em dùng Edge thì nghe được rồi ạ, cảm ơn cô.")], "closed"),
    ("thaovy.do@lingoprism.local", "Xin tài liệu ôn thi",
     [("l", "Cô ơi có bài kiểm tra nào cho chủ đề động vật bằng tiếng Trung không ạ?"),
      ("s", "Có em nhé, vào mục Bài kiểm tra chọn \"Động vật – tiếng Trung (giản thể)\". Làm xong phần tự luận cô sẽ chấm và nhận xét.")],
     "open"),
]
REPORTS = [  # (reporter, word slug, reason, details, status)
    ("thuha.nguyen@lingoprism.local", "kettle", "wrong_image", "Ảnh ấm đun nước hơi nhỏ, nhìn trên điện thoại hơi khó thấy.", "open"),
    ("anhkhoa.mai@lingoprism.local", "watch", "other", "Gợi ý thêm lượng từ 块 khi học từ đồng hồ đeo tay ạ.", "resolved"),
]


def at(day: date, hour: int, minute: int = 0) -> datetime:
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))


class Command(BaseCommand):
    help = "Tạo dữ liệu hoạt động mẫu chân thực cho mọi chức năng (người học, lịch sử học, cộng đồng, giải đấu…)"

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=2026)
        parser.add_argument("--no-detect", action="store_true", help="Không chạy YOLO (bỏ phần ảnh nhận diện)")

    def handle(self, *args, seed=2026, no_detect=False, **opts):
        self.rng = random.Random(seed)
        self.today = timezone.localdate()
        self.scheduler = get_scheduler("leitner")  # the history is replayed with SnapLingua's original scheduler
        self.memory = {}
        from apps.algorithms.vision import latest as visual_profile

        self.visual = visual_profile()
        call_command("seed_demo_users", verbosity=0)
        with transaction.atomic():
            users = self._accounts()
            self._reset(users)
            self.staff = User.objects.get(email="staff@lingoprism.local")
            self.teacher = self._staff()
            self.vi_text = dict(WordTranslation.objects.filter(language_id="vi", status=ReviewStatus.VERIFIED)
                                .values_list("word_id", "text"))
            for user, prof in users:
                self._history(user, prof)
            self._exams(users)
            self._leagues(users)
            self._shop(users)
        # photos run the real detector – outside the big transaction (slow)
        self._photos_and_posts(users, detect=not no_detect)
        with transaction.atomic():
            self._community(users)
            self._groups(users)
            self._support()
            self._reports()
            self._geofence(users)
            for user, prof in users:
                self._totals(user, prof)
        self.stdout.write(self.style.SUCCESS(
            f"Đã tạo hoạt động cho {len(users)} người học · {ReviewLog.objects.filter(user__in=[u for u, _ in users]).count()} lượt ôn · "
            f"{Post.objects.count()} bài đăng · mật khẩu chung {PASSWORD}"))

    # ------------------------------------------------------------------ accounts

    def _accounts(self):
        out = []
        for i, prof in enumerate(LEARNERS):
            user = User.objects.filter(email=prof["email"]).first() or User(email=prof["email"])
            user.display_name = prof["name"]
            user.role = User.Role.LEARNER
            user.learner_type = "kid" if prof.get("kid") else "adult"
            user.active_language = prof["learn"]
            user.learning_languages = [prof["learn"]] + (["en"] if prof["learn"] == "vi" else [])
            user.zh_script = prof.get("script", "hans")
            user.show_zhuyin = prof.get("script") == "hant"
            user.bio = prof.get("bio", "")
            user.avatar_preset = AVATARS[i % len(AVATARS)]
            user.birth_date = date(prof["born"], 1 + i % 12, 1 + (i * 7) % 28)
            user.gender = prof.get("gender", "")
            user.purpose = prof.get("purpose", "")
            user.onboarding_completed = True
            user.scales_balance = user.gems_balance = 0
            if not user.pk:
                user.set_password(PASSWORD)
            user.save()
            User.objects.filter(pk=user.pk).update(created_at=at(self.today - timedelta(days=prof["since"]), 8 + i % 10))
            goal, _ = UserGoal.objects.get_or_create(user=user)
            goal.daily_new_target = prof["new"]
            goal.daily_review_target = prof["new"] * 2
            goal.save()
            NotificationSetting.objects.update_or_create(user=user, defaults={
                "morning_time": time(7, 30), "evening_time": time(20, 30), "social_enabled": not prof.get("kid")})
            out.append((user, prof))
        return out

    def _staff(self):
        t = User.objects.filter(email=STAFF["email"]).first() or User(email=STAFF["email"])
        t.display_name, t.role, t.bio, t.onboarding_completed = STAFF["name"], User.Role.STAFF, STAFF["bio"], True
        t.avatar_preset = brand.mascot("graduate")
        if not t.pk:
            t.set_password(PASSWORD)
        t.save()
        return t

    def _reset(self, users):
        # staff/admin accounts are not learners: drop anything left on them by manual testing
        ids = [u.id for u, _ in users] + list(User.objects.filter(role__in=[User.Role.ADMIN, User.Role.STAFF])
                                              .values_list("id", flat=True))
        for model in (Photo, Post):
            for obj in model.objects.filter(user_id__in=ids):
                if obj.image:
                    obj.image.delete(save=False)
        Group.objects.filter(Q(created_by_id__in=ids) | Q(name__in=[g["name"] for g in GROUPS])).delete()
        for model, field in [
            (Post, "user"), (Photo, "user"), (Detection, "user"), (PersonalWord, "user"), (StudySession, "user"),
            (ReviewLog, "user"), (SentenceAttempt, "user"), (XpTransaction, "user"), (DailyProgress, "user"),
            (DailyQuest, "user"), (MonthlyQuest, "user"), (UserBadge, "user"), (UserInventory, "user"),
            (UserStats, "user"), (LeagueMember, "user"), (Notification, "user"), (Submission, "user"),
            (SupportConversation, "learner"), (GeofenceEvent, "user"), (LiteracyProgress, "user"),
            (LiteracyAttempt, "user"), (LearnerLevel, "user"), (ErrorReport, "user"), (UserFollow, "follower"),
            (UserFollow, "following"), (GroupMember, "user"), (PostLike, "user"), (PostComment, "user"),
            (PostReport, "reporter"),
        ]:
            model.objects.filter(**{f"{field}_id__in": ids}).delete()
        LeagueCycle.objects.filter(members__isnull=True).delete()

    # ------------------------------------------------------------------ study history

    def _target(self, prof):
        return "zh-Hant" if prof["learn"] == "zh" and prof.get("script") == "hant" else (
            "zh-Hans" if prof["learn"] == "zh" else prof["learn"])

    def _path(self, prof):
        """Words of the learner's language in path order (level, then topic order), kid-safe for children."""
        code = self._target(prof)
        qs = Word.objects.filter(translations__language_id=code, translations__status=ReviewStatus.VERIFIED)
        if prof.get("kid"):
            qs = qs.filter(audience__in=["all", "kid"])
        words = list(qs.distinct())
        self.rng.shuffle(words)
        return sorted(words, key=lambda w: (w.levels or {}).get(prof["learn"], 4))

    def _history(self, user, prof):
        learn, code = prof["learn"], self._target(prof)
        script = prof.get("script", "") if learn == "zh" else ""
        path = self._path(prof)
        cards: dict[int, PersonalWord] = {}
        days = sorted(self.today - timedelta(days=d) for d in range(prof["since"] + 1))
        streak_bias = 0
        self.active_days = getattr(self, "active_days", {})
        active = []
        examples = defaultdict(list)
        for ex in ExampleSentence.objects.filter(language_id=code, status=ReviewStatus.VERIFIED).exclude(tokens=[]):
            examples[ex.word_id].append(ex)
        for day in days:
            # habits: people who study keep going (streaks), the last day is "today" for active users
            chance = min(.97, prof["p"] + (.1 if streak_bias > 2 else 0))
            if day == self.today:
                chance = .85 if prof["p"] >= .6 else .3
            if self.rng.random() > chance:
                streak_bias = 0
                continue
            streak_bias += 1
            active.append(day)
            hour = self.rng.choice([6, 7, 12, 19, 20, 21, 22])
            minute = self.rng.randrange(60)
            progress = DailyProgress(user=user, date=day, new_target=prof["new"], review_target=prof["new"] * 2, active=True)
            xp_day = 0
            # 1) review what is due
            due = [c for c in cards.values() if c.due_at and c.due_at.date() <= day]
            self.rng.shuffle(due)
            if due:
                sess, xp = self._session(user, prof, "review", due[: prof["new"] * 2], at(day, hour, minute), code, script)
                progress.reviews_done += sess.completed_count
                xp_day += xp
            # 2) learn new words
            fresh = [w for w in path if w.id not in cards][: prof["new"] if self.rng.random() > .15 else prof["new"] // 2]
            if fresh:
                start = at(day, hour, minute) + timedelta(minutes=12)
                new_cards = []
                for w in fresh:
                    pw = PersonalWord.objects.create(user=user, word=w, language=learn, source=PersonalWord.Source.TOPIC)
                    PersonalWord.objects.filter(pk=pw.pk).update(created_at=start)
                    cards[w.id] = pw
                    new_cards.append(pw)
                sess, xp = self._session(user, prof, "learn", new_cards, start, code, script)
                progress.new_learned += sess.completed_count
                xp_day += xp
            # 3) sentence practice now and then (needs words already started)
            if learn != "vi" and self.rng.random() < .35:
                pool = [ex for wid in cards for ex in examples.get(wid, [])]
                for ex in self.rng.sample(pool, min(len(pool), 5)):
                    ok = self.rng.random() < prof["acc"]
                    SentenceAttempt.objects.create(
                        user=user, sentence=ex, language=learn, script=script, correct=ok,
                        exercise=self.rng.choice(["arrange", "listen", "fill", "meaning"] if ex.translation_vi else ["listen", "fill"]),
                        answer=ex.text[:300] if ok else "", response_ms=self.rng.randint(4000, 20000),
                        created_at=at(day, hour, minute) + timedelta(minutes=25))
                    if ok:
                        xp_day += self._xp(user, "practice", 2, at(day, hour, minute) + timedelta(minutes=26), f"sentence:{ex.id}")
            progress.xp = min(xp_day, game.DAILY_XP_CAP)
            progress.save()
            self._quests(user, prof, day, progress)
        if prof["learn"] == "vi" and prof.get("kid"):
            self._literacy(user, prof, active)
        self.active_days[user.id] = active
        LearnerLevel.objects.get_or_create(user=user, language=learn)

    def _session(self, user, prof, kind, pws, start, code, script):
        sess = StudySession.objects.create(user=user, language=prof["learn"], script=script, kind=kind,
                                           planned_count=len(pws), started_at=start)
        t = start
        first_ok = 0
        for order, pw in enumerate(pws):
            SessionItem.objects.create(session=sess, personal_word=pw, order=order, answered=True)
            t += timedelta(seconds=self.rng.randint(15, 70))
            # the learner's (hidden) memory decides the answer: recall decays with time since the last review
            mem = self.memory.get(pw.id)
            if mem is None:
                lvl = (pw.word.levels or {}).get(prof["learn"], 2)
                vis = self.visual.get(pw.word.yolo_label) if pw.word.yolo_label else None
                mem = self.memory[pw.id] = TrueMemory(0.6 + 0.6 * prof["acc"], word_difficulty(lvl, vis["score"] if vis else 0))
                mem.first()
                correct = self.rng.random() < prof["acc"]
            else:
                correct = mem.review((t - pw.last_reviewed_at).total_seconds() / 86400, self.rng)
            before = CardState(pw.stage, pw.ease, pw.interval_days, pw.repetitions, pw.lapses, pw.wrong_streak)
            elapsed = (t.date() - pw.last_reviewed_at.date()).days if pw.last_reviewed_at else 0
            state, due = self.scheduler.review(before, correct, 4 if correct else 1, t)
            ReviewLog.objects.create(
                user=user, personal_word=pw, session=sess, language=prof["learn"], script=script,
                question_type=self.rng.choice(["choose_target", "choose_meaning", "type_target", "listen_type"]),
                correct=correct, first_try=True, rating=4 if correct else 1, response_ms=self.rng.randint(1800, 9000),
                scheduler=self.scheduler.name, state_before=before.as_dict(), state_after=state.as_dict(),
                elapsed_days=elapsed, created_at=t)
            first_ok += correct
            pw.stage, pw.ease, pw.interval_days = state.stage, state.ease, state.interval_days
            pw.repetitions, pw.lapses, pw.wrong_streak = state.repetitions, state.lapses, state.wrong_streak
            pw.due_at, pw.last_reviewed_at = due, t
            pw.first_learned_at = pw.first_learned_at or t
            pw.status = PersonalWord.Status.MASTERED if state.interval_days >= 21 else PersonalWord.Status.LEARNING
            PersonalWord.objects.filter(pk=pw.pk).update(
                stage=pw.stage, ease=pw.ease, interval_days=pw.interval_days, repetitions=pw.repetitions,
                lapses=pw.lapses, wrong_streak=pw.wrong_streak, due_at=due, last_reviewed_at=t,
                first_learned_at=pw.first_learned_at, status=pw.status, updated_at=t)
        sess.completed_count, sess.correct_first_try = len(pws), first_ok
        sess.xp_earned = 5 * len(pws) + 5 * first_ok
        sess.ended_at = t + timedelta(seconds=20)
        sess.save()
        StudySession.objects.filter(pk=sess.pk).update(created_at=start, updated_at=sess.ended_at)
        user.scales_balance += first_ok  # +1 Vảy per word right at the first try
        xp = self._xp(user, kind, sess.xp_earned, sess.ended_at, str(sess.id),
                      f"Phiên {sess.get_kind_display().lower()}")
        return sess, xp

    def _xp(self, user, source, amount, when, source_id="", note=""):
        tx = XpTransaction.objects.create(user=user, source=source, source_id=source_id, base_amount=amount,
                                          multiplier=1.0, amount=amount, note=note)
        XpTransaction.objects.filter(pk=tx.pk).update(created_at=when)
        return amount

    def _quests(self, user, prof, day, progress):
        kid = prof.get("kid")
        values = {
            DailyQuest.Kind.REACH_LEARN_GOAL: (progress.new_target, progress.new_learned),
            DailyQuest.Kind.REACH_REVIEW_GOAL: (progress.review_target, progress.reviews_done),
            DailyQuest.Kind.SAVE_WORDS: (5, 0),
        }
        if not kid:
            values[DailyQuest.Kind.POST_COMMUNITY_IMAGE] = (1, 0)
            values[DailyQuest.Kind.ENGAGE_COMMUNITY] = (5, self.rng.choice([0, 2, 5, 5]) if prof.get("social") else 0)
        for kind, (target, done) in values.items():
            done = min(target, done)
            q = DailyQuest.objects.create(user=user, date=day, kind=kind, target=target, progress=done)
            if done >= target:
                q.completed_at = at(day, 21, self.rng.randrange(60))
                q.reward_claimed = day != self.today or self.rng.random() < .5
                q.save()
                if q.reward_claimed:
                    user.scales_balance += DailyQuest.REWARD_SCALES

    def _literacy(self, user, prof, active):
        """Children move through the reading course: about one lesson every second active day.
        Each lesson attempt is 12 exercises on real syllables readable at that lesson."""
        n_done = min(len(cur.LESSONS), max(1, len(active) // 2))
        for n in range(1, n_done + 1):
            day = active[min(len(active) - 1, (n - 1) * 2)]
            percent = self.rng.randint(62, 100) if n < n_done else self.rng.randint(45, 95)
            stars = 3 if percent >= 90 else 2 if percent >= 75 else 1 if percent >= 60 else 0
            when = at(day, 18, self.rng.randrange(60))
            LiteracyProgress.objects.create(user=user, lesson=n, best_percent=percent, stars=stars,
                                            times_completed=1 + (self.rng.random() < .3),
                                            completed_at=when if percent >= 60 else None)
            syllables = [s.text for s, _ in cur.readable_syllables(n)[:40]]
            total, right = 12, round(12 * percent / 100)
            for i in range(total):
                expected = self.rng.choice(syllables)
                wrong = self.rng.choice([x for x in syllables if x != expected] or [""])
                LiteracyAttempt.objects.create(
                    user=user, session=f"s{user.id}l{n}"[:16], lesson=n, unit="review", index=i, correct=i < right,
                    exercise=["listen_choose", "find_unit", "build", "dictation"][i % 4], expected=expected,
                    answer=expected if i < right else wrong, response_ms=self.rng.randint(3000, 15000),
                    created_at=when - timedelta(minutes=total - i))
            if percent >= 60:
                self._xp(user, "practice", 2 * right, when, f"literacy:{n}", f"Học đọc – viết: {cur.LESSONS[n - 1]['title']}")

    # ------------------------------------------------------------------ exams

    def _exams(self, users):
        sentences = defaultdict(list)
        for ex in ExampleSentence.objects.filter(status=ReviewStatus.VERIFIED, language_id__in=["en", "zh-Hans", "zh-Hant"]):
            sentences[(ex.language_id, ex.word_id)].append(ex.text)
        for user, prof in users:
            if prof.get("kid") or prof["learn"] == "vi":
                continue
            code = self._target(prof)
            exams = list(Exam.objects.filter(language_id=code, is_published=True).order_by("id"))
            for exam in self.rng.sample(exams, min(len(exams), self.rng.choice([1, 2, 2, 3]))):
                day = self.rng.choice(self.active_days[user.id][-14:] or [self.today])
                start = at(day, 20, self.rng.randrange(40))
                sub = Submission.objects.create(user=user, exam=exam, started_at=start)
                pending = False
                for eq in exam.exam_questions.select_related("question").order_by("order"):
                    q = eq.question
                    ok = self.rng.random() < prof["acc"]
                    ans = Answer(submission=sub, exam_question=eq)
                    if q.kind == Question.Kind.MCQ:
                        right = next(i for i, o in enumerate(q.options) if o.get("correct"))
                        ans.selected_option = right if ok else self.rng.choice([i for i in range(len(q.options)) if i != right])
                        ans.is_correct, ans.score = ok, eq.points if ok else Decimal("0")
                    elif q.kind == Question.Kind.FILL:
                        ans.text = q.accepted_answers[0] if ok else ""
                        ans.is_correct, ans.score = ok, eq.points if ok else Decimal("0")
                    else:
                        # the essay answer is made of real (Tatoeba) sentences that use the requested words
                        words = WordTranslation.objects.filter(language_id=code, text__in=self._essay_words(q.prompt))
                        texts = [sentences[(code, t.word_id)][0] for t in words if sentences.get((code, t.word_id))]
                        ans.text = " ".join(texts[:3])
                        if not ans.text:
                            ans.is_correct, ans.score = False, Decimal("0")
                        elif self.rng.random() < .6:  # graded by the teacher
                            ans.is_correct, ans.score = True, eq.points
                            ans.feedback = "Câu đúng ngữ pháp, dùng từ chính xác. Tốt lắm!"
                        else:
                            pending = True
                    ans.save()
                answers = list(sub.answers.select_related("exam_question"))
                sub.max_score = sum((a.exam_question.points for a in answers), Decimal("0"))
                sub.score = sum((a.score or Decimal("0") for a in answers), Decimal("0"))
                sub.submitted_at = start + timedelta(minutes=self.rng.randint(6, 14))
                sub.status = Submission.Status.SUBMITTED if pending else Submission.Status.GRADED
                if not pending and any(a.feedback for a in answers):
                    sub.graded_by, sub.graded_at = self.staff if code == "en" else self.teacher, sub.submitted_at + timedelta(hours=5)
                sub.save()
                if not pending:
                    self._xp(user, "exam", int(sub.percent // 5), sub.submitted_at, str(sub.id), exam.title)
                    Notification.objects.create(user=user, kind=Notification.Kind.EXAM, title="Bài kiểm tra đã có điểm",
                                                 body=f"{exam.title}: {sub.percent}%", data={"route": f"/exams/results/{sub.id}"},
                                                 read_at=sub.submitted_at + timedelta(hours=6), created_at=sub.submitted_at)

    @staticmethod
    def _essay_words(prompt: str) -> list[str]:
        return [w.strip(" .") for w in prompt.split(":", 1)[-1].split(",")]

    # ------------------------------------------------------------------ leagues

    def _leagues(self, users):
        tiers = list(LeagueTier.objects.order_by("order"))
        level = {u.id: 0 for u, _ in users}
        start_this, _ = game.week_bounds()
        for weeks_ago in (4, 3, 2, 1):
            start = start_this - timedelta(weeks=weeks_ago)
            end = start + timedelta(weeks=1)
            by_tier = defaultdict(list)
            for user, _ in users:
                xp = sum(XpTransaction.objects.filter(user=user, created_at__gte=start, created_at__lt=end)
                         .values_list("amount", flat=True))
                if xp or weeks_ago < 4:
                    by_tier[level[user.id]].append((user, xp))
            for t, members in by_tier.items():
                cycle = LeagueCycle.objects.create(tier=tiers[t], start_at=start, end_at=end)
                for user, xp in members:
                    LeagueMember.objects.create(cycle=cycle, user=user, weekly_xp=xp)
                game.close_cycle(cycle)
                Notification.objects.filter(kind=Notification.Kind.LEAGUE, created_at__gte=timezone.now() - timedelta(minutes=5),
                                            user__in=[u for u, _ in members]).update(created_at=end)
                for m in cycle.members.all():
                    level[m.user_id] = min(len(tiers) - 1, level[m.user_id] + 1) if m.result == "promoted" else \
                        max(0, level[m.user_id] - 1) if m.result == "demoted" else level[m.user_id]
        for user, _ in users:
            xp = sum(XpTransaction.objects.filter(user=user, created_at__gte=start_this).values_list("amount", flat=True))
            if xp:
                member = game.join_current_league(user)
                LeagueMember.objects.filter(pk=member.pk).update(weekly_xp=xp)

    # ------------------------------------------------------------------ shop

    def _shop(self, users):
        freeze = Item.objects.filter(effect=Item.Effect.STREAK_FREEZE).first()
        boost = Item.objects.filter(effect=Item.Effect.XP_DOUBLE_15M).first() if hasattr(Item.Effect, "XP_DOUBLE_15M") else None
        for user, prof in users:
            if freeze and user.scales_balance >= freeze.cost_scales + 50 and self.rng.random() < .7:
                user.scales_balance -= freeze.cost_scales
                UserInventory.objects.create(user=user, item=freeze, quantity=1)
            if boost and boost.cost_scales and user.scales_balance >= boost.cost_scales + 100 and self.rng.random() < .4:
                user.scales_balance -= boost.cost_scales
                UserInventory.objects.create(user=user, item=boost, quantity=1)
            # monthly reward: 20 completed daily quests in a month → +2 gems
            for month in {d.strftime("%Y-%m") for d in self.active_days[user.id]}:
                done = DailyQuest.objects.filter(user=user, date__startswith=month, completed_at__isnull=False).count()
                mq = MonthlyQuest.objects.create(user=user, month=month, completed_count=done)
                if done >= MonthlyQuest.TARGET:
                    mq.reward_claimed, mq.reward_claimed_at = True, timezone.now()
                    mq.save()
                    user.gems_balance += MonthlyQuest.REWARD_GEMS
            User.objects.filter(pk=user.pk).update(scales_balance=user.scales_balance, gems_balance=user.gems_balance)

    # ------------------------------------------------------------------ photos, detection, posts

    def _photos_and_posts(self, users, detect=True):
        if not detect:
            return
        try:
            from apps.detection.inference import DetectorUnavailable, get_detector
            detector = get_detector()
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(f"Bỏ qua ảnh nhận diện: {exc}")
            return
        folder = Path(settings.BASE_DIR) / "seed" / "images"
        import csv

        with open(Path(settings.BASE_DIR) / "seed" / "concepts" / "images.csv", encoding="utf-8") as fh:
            self.credits = {r["slug"]: f"Ảnh: {r['author']} · {r['license']} · Wikimedia Commons"
                            for r in csv.DictReader(fh) if r["status"] == "verified" and r["source_url"]}
        labelled = list(Word.objects.exclude(yolo_label="").exclude(image="").filter(image__startswith="words/seed_"))
        social = [(u, p) for u, p in users if p.get("social")]
        photographers = social + [(u, p) for u, p in users if not p.get("kid") and not p.get("social")][:3]
        self.posts = []
        for user, prof in photographers:
            for word in self.rng.sample(labelled, self.rng.randint(1, 3)):
                src = folder / f"{word.slug}.jpg"
                if not src.exists():
                    continue
                day = self.rng.choice(self.active_days[user.id] or [self.today])
                when = at(day, self.rng.choice([8, 11, 17, 19]), self.rng.randrange(60))
                img = Image.open(src)
                boxes, ms = detector.predict(img)
                with transaction.atomic(), open(src, "rb") as fh:
                    photo = Photo(user=user, width=img.width, height=img.height,
                                  source=self.rng.choice([Photo.Source.CAMERA, Photo.Source.GALLERY]))
                    photo.image.save(f"{word.slug}.jpg", File(fh), save=False)
                    photo.save()
                    Photo.objects.filter(pk=photo.pk).update(created_at=when)
                    det = Detection.objects.create(user=user, photo=photo, model_name=detector.name, device=Detection.Device.SERVER,
                                                   inference_ms=ms, confirmed=bool(boxes))
                    Detection.objects.filter(pk=det.pk).update(created_at=when)
                    by_label = dict(Word.objects.filter(yolo_label__in=[b.label for b in boxes]).values_list("yolo_label", "id"))
                    items = []
                    for i, b in enumerate(boxes[:5]):
                        items.append(DetectionItem.objects.create(
                            detection=det, label=b.label, confidence=b.confidence, bbox=b.bbox, top_k=b.top_k,
                            word_id=by_label.get(b.label), selected=i == 0 and b.label in by_label,
                            feedback=DetectionItem.Feedback.CORRECT if b.label == word.yolo_label else DetectionItem.Feedback.UNKNOWN))
                    found = [it for it in items if it.word_id]
                    for it in found[:2]:
                        pw, created = PersonalWord.objects.get_or_create(
                            user=user, word_id=it.word_id, language=prof["learn"],
                            defaults={"source": PersonalWord.Source.CAMERA, "source_ref": str(det.id)})
                        if created:
                            PersonalWord.objects.filter(pk=pw.pk).update(created_at=when)
                    self._xp(user, "camera", 5, when, str(det.id), "Nhận diện ảnh")
                    if not found or not prof.get("social"):
                        continue
                    main = Word.objects.get(pk=found[0].word_id)
                    word_text = self.vi_text.get(main.id, main.slug)
                    credit = self.credits.get(word.slug, "")
                    caption = self.rng.choice(CAPTIONS).format(w=word_text) + (f"\n📷 {credit}" if credit else "")
                    post = Post(user=user, caption=caption[:500],
                                topic_label=word_text, detection=det)
                    with open(src, "rb") as fh2:
                        post.image.save(f"{word.slug}.jpg", File(fh2), save=False)
                    post.save()
                    Post.objects.filter(pk=post.pk).update(created_at=when + timedelta(minutes=3))
                    for order, it in enumerate(found[:3]):
                        PostWord.objects.get_or_create(post=post, word_id=it.word_id, defaults={"order": order})
                    self.posts.append((post, when))
                    DailyQuest.objects.filter(user=user, date=day, kind=DailyQuest.Kind.POST_COMMUNITY_IMAGE).update(
                        progress=1, completed_at=when)

    # ------------------------------------------------------------------ community

    def _community(self, users):
        social = [u for u, p in users if p.get("social")]
        adults = [u for u, p in users if not p.get("kid")]
        for user in social:
            for other in self.rng.sample([u for u in social if u != user], 4):
                f, created = UserFollow.objects.get_or_create(follower=user, following=other)
                if created:
                    when = timezone.now() - timedelta(days=self.rng.randint(1, 25))
                    UserFollow.objects.filter(pk=f.pk).update(created_at=when)
                    Notification.objects.create(user=other, kind=Notification.Kind.FOLLOW,
                                                title=f"{user.display_name} đã theo dõi bạn", data={"route": f"/community/users/{user.id}"},
                                                created_at=when, read_at=when + timedelta(hours=2) if self.rng.random() < .6 else None)
        for post, when in getattr(self, "posts", []):
            fans = self.rng.sample([u for u in social if u != post.user], self.rng.randint(2, min(9, len(social) - 1)))
            for i, fan in enumerate(fans):
                t = when + timedelta(minutes=15 + 37 * i)
                PostLike.objects.create(post=post, user=fan, created_at=t)
            for i, fan in enumerate(fans[: self.rng.randint(0, 3)]):
                t = when + timedelta(minutes=40 + 53 * i)
                if self.rng.random() < .2:
                    PostComment.objects.create(post=post, user=fan, kind=PostComment.Kind.STICKER,
                                               sticker=self.rng.choice(STICKERS), created_at=t)
                else:
                    PostComment.objects.create(post=post, user=fan, content=self.rng.choice(COMMENTS), created_at=t)
                Notification.objects.create(user=post.user, kind=Notification.Kind.COMMENT,
                                            title=f"{fan.display_name} đã bình luận bài viết của bạn",
                                            data={"route": "/community", "post": post.id}, created_at=t,
                                            read_at=t + timedelta(hours=1) if self.rng.random() < .7 else None)
                if self.rng.random() < .4:
                    PostComment.objects.create(post=post, user=post.user, content=self.rng.choice(REPLIES),
                                               created_at=t + timedelta(minutes=20))
            post.save_count = self.rng.randint(0, len(fans))
            post.save(update_fields=["save_count"])
        posts = [p for p, _ in getattr(self, "posts", [])]
        if posts and adults:
            # one real-looking moderation case: a learner thinks the tagged word does not match the photo
            p = self.rng.choice(posts)
            reporter = self.rng.choice([u for u in adults if u != p.user])
            PostReport.objects.create(post=p, reporter=reporter, reason=PostReport.Reason.WRONG_VOCAB,
                                      details="Mình thấy từ gắn kèm chưa đúng với vật chính trong ảnh, nhờ kiểm tra giúp.")

    def _groups(self, users):
        social = {u.email: (u, p) for u, p in users if p.get("social")}
        for g in GROUPS:
            members = [u for u, p in social.values() if p["learn"] == g["learn"]]
            if len(members) < 2:
                continue
            leader = members[0]
            group = Group.objects.create(name=g["name"], description=g["description"], icon=g["icon"],
                                         require_approval=g.get("require_approval", False), created_by=leader)
            start = timezone.now() - timedelta(days=20)
            for i, u in enumerate(members):
                GroupMember.objects.create(group=group, user=u, role=GroupMember.Role.LEADER if u == leader else GroupMember.Role.MEMBER,
                                           joined_at=start + timedelta(hours=7 * i))
            if g.get("require_approval"):
                outsider = next((u for u, p in social.values() if p["learn"] != g["learn"]), None)
                if outsider:
                    GroupMember.objects.create(group=group, user=outsider, status=GroupMember.Status.PENDING,
                                               request_message="Mình muốn học thêm phồn thể, cho mình tham gia với ạ.")
            t = start + timedelta(days=1)
            for i, line in enumerate(g["chat"]):
                t += timedelta(hours=self.rng.randint(5, 40))
                GroupMessage.objects.create(group=group, user=members[i % len(members)], content=line, created_at=t)
            badge = UserBadge.objects.filter(user__in=members).select_related("badge", "user").first()
            if badge:
                GroupMessage.objects.create(group=group, user=badge.user, kind=GroupMessage.Kind.BADGE, badge=badge.badge,
                                            content=f"Vừa nhận huy hiệu {badge.badge.name} 🎉", created_at=t + timedelta(hours=3))

    def _support(self):
        for email, subject, lines, status in SUPPORT:
            learner = User.objects.get(email=email)
            staff = self.teacher if learner.active_language == "zh" else self.staff
            start = timezone.now() - timedelta(days=self.rng.randint(2, 15), hours=self.rng.randint(0, 10))
            conv = SupportConversation.objects.create(learner=learner, staff=staff, subject=subject, status=status, created_at=start)
            t = start
            for who, text in lines:
                t += timedelta(minutes=self.rng.randint(8, 240))
                SupportMessage.objects.create(conversation=conv, sender=learner if who == "l" else staff, content=text,
                                              created_at=t, delivered_at=t, read_at=t + timedelta(minutes=5))
            conv.last_message_at = t
            conv.save(update_fields=["last_message_at"])

    def _reports(self):
        for email, slug, reason, details, status in REPORTS:
            word = Word.objects.filter(slug=slug).first()
            if not word:
                continue
            r = ErrorReport.objects.create(user=User.objects.get(email=email), word=word, reason=reason, details=details, status=status)
            if status != "open":
                r.handled_by, r.handled_at = self.teacher, timezone.now() - timedelta(days=1)
                r.save()

    def _geofence(self, users):
        pois = list(Poi.objects.filter(is_active=True))
        for user, prof in users:
            if prof.get("kid") or not pois:
                continue
            for poi in self.rng.sample(pois, self.rng.randint(0, 3)):
                d = self.rng.uniform(15, poi.radius_m * .9)
                when = timezone.now() - timedelta(days=self.rng.randint(0, 20), hours=self.rng.randint(0, 12))
                GeofenceEvent.objects.create(user=user, poi=poi, lat=poi.lat + d / 111_000, lng=poi.lng, distance_m=round(d, 1),
                                             created_at=when)
                Notification.objects.create(user=user, kind=Notification.Kind.LOCATION, title=f"Bạn đang ở gần {poi.name}",
                                            body="Học vài từ vựng hợp với nơi này nhé!", data={"route": "/map", "poi": poi.id},
                                            created_at=when, read_at=when + timedelta(minutes=10) if self.rng.random() < .5 else None)

    # ------------------------------------------------------------------ totals that must agree with the history

    def _totals(self, user, prof):
        active = sorted(set(self.active_days.get(user.id, [])))
        streak, longest, run, prev = 0, 0, 0, None
        for d in active:
            run = run + 1 if prev and (d - prev).days == 1 else 1
            longest, prev = max(longest, run), d
        if active and (self.today - active[-1]).days <= 1:
            streak = run
        xp = sum(XpTransaction.objects.filter(user=user).values_list("amount", flat=True))
        words = PersonalWord.objects.filter(user=user)
        stats = UserStats.objects.update_or_create(user=user, defaults={
            "lifetime_xp": xp, "current_streak": streak, "longest_streak": longest,
            "last_active_date": active[-1] if active else None,
            "words_learned": words.exclude(status=PersonalWord.Status.NEW).count(),
            "words_mastered": words.filter(status=PersonalWord.Status.MASTERED).count(),
            "detections": Detection.objects.filter(user=user).count(), "posts": Post.objects.filter(user=user).count(),
        })[0]
        game.check_badges(user, stats)
        # the learner moved up the 4-level path as each level reached the unlock threshold
        from apps.learning.levels import progress as level_progress
        from apps.vocab.services import Target

        target = Target(prof["learn"], self._target(prof), prof.get("script", "") if prof["learn"] == "zh" else "")
        top = max(r["level"] for r in level_progress(user, target)["levels"] if r["unlocked"])
        LearnerLevel.objects.filter(user=user, language=prof["learn"]).update(current=top)
        last = timezone.make_aware(datetime.combine(active[-1], time(21))) if active else timezone.now()
        UserBadge.objects.filter(user=user).update(awarded_at=last)
        Notification.objects.filter(user=user, kind=Notification.Kind.ACHIEVEMENT, created_at__gte=timezone.now() - timedelta(minutes=10)) \
            .update(created_at=last)
        for m in game.XP_MILESTONES:
            if xp >= m:
                Notification.objects.create(user=user, kind=Notification.Kind.XP_MILESTONE, title=f"Bạn đã đạt {m} XP!",
                                            image=brand.XP, data={"route": "/profile"},
                                            created_at=last - timedelta(days=max(0, len(active) - 1) * (1 - m / max(xp, 1))),
                                            read_at=last)
        if active and active[-1] < self.today:
            Notification.objects.create(user=user, kind=Notification.Kind.REMINDER, title="Đến giờ học rồi! 📚",
                                        body=f"Bạn có {words.filter(due_at__date__lte=self.today).count()} từ cần ôn hôm nay.",
                                        data={"route": "/learn?kind=review"}, created_at=at(self.today, 20, 30))
