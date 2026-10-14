from django.contrib import admin

from .models import Group, GroupMember, Post, PostComment, PostLike, PostReport, PostWord, UserFollow

for m in (Group, GroupMember, Post, PostComment, PostLike, PostReport, PostWord, UserFollow,):
    admin.site.register(m)
