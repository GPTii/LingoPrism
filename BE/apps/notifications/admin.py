from django.contrib import admin

from .models import DeviceToken, Notification, NotificationSetting

admin.site.register(Notification)
admin.site.register(NotificationSetting)
admin.site.register(DeviceToken)
