from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.learning.models import PersonalWord
from apps.learning.signals import session_finished

from . import services
from .models import DailyQuest, XpTransaction


@receiver(session_finished)
def on_session_finished(sender, session, **kwargs):
    user = session.user
    progress = services.progress_for(user)
    if session.kind == "learn":
        progress.new_learned += session.completed_count
    else:
        progress.reviews_done += session.completed_count
    progress.save(update_fields=["new_learned", "reviews_done"])
    if session.completed_count:
        services.mark_activity(user)
    services.award_xp(user, session.kind if session.kind in XpTransaction.Source.values else "learn",
                      session.xp_earned, source_id=str(session.id), note=f"Phiên {session.get_kind_display().lower()}")
    services.progress_quest(user, DailyQuest.Kind.REACH_LEARN_GOAL, absolute=progress.new_learned)
    services.progress_quest(user, DailyQuest.Kind.REACH_REVIEW_GOAL, absolute=progress.reviews_done)
    # first-try correct answers earn scales (SnapLingua: +1 Vảy per word)
    if session.correct_first_try:
        type(user).objects.filter(pk=user.pk).update(scales_balance=F("scales_balance") + session.correct_first_try)
    learned = PersonalWord.objects.filter(user=user).exclude(status="new").count()
    mastered = PersonalWord.objects.filter(user=user, status="mastered").count()
    stats = services.stats_for(user)
    stats.words_learned, stats.words_mastered = learned, mastered
    fields = ["words_learned", "words_mastered"]
    if session.completed_count:
        stats.sessions += 1
        fields.append("sessions")
        if session.completed_count >= 3 and session.correct_first_try == session.completed_count:
            stats.perfect_sessions += 1
            fields.append("perfect_sessions")
        hour = timezone.localtime(session.ended_at or timezone.now()).hour
        if hour < 7:
            stats.early_bird += 1
            fields.append("early_bird")
        elif hour >= 22:
            stats.night_owl += 1
            fields.append("night_owl")
    stats.save(update_fields=fields)
    services.check_badges(user, stats)


@receiver(post_save, sender=PersonalWord)
def on_word_saved(sender, instance, created, **kwargs):
    if created and instance.source == PersonalWord.Source.CAMERA:
        services.progress_quest(instance.user, DailyQuest.Kind.SAVE_WORDS)
