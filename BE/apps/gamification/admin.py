from django.contrib import admin

from .models import Badge, DailyProgress, DailyQuest, Item, LeagueCycle, LeagueMember, LeagueTier, UserStats, XpTransaction

for model in (Badge, DailyProgress, DailyQuest, Item, LeagueCycle, LeagueMember, LeagueTier, UserStats, XpTransaction):
    admin.site.register(model)
