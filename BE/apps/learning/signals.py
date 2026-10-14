from django.dispatch import Signal

# Sent when a study session ends; gamification (XP, streak, quests) listens to it.
session_finished = Signal()
