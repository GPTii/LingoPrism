from django.contrib import admin

from .models import GroupMessage, SupportConversation, SupportMessage

for m in (GroupMessage, SupportConversation, SupportMessage,):
    admin.site.register(m)
