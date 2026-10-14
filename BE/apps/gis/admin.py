from django.contrib import admin

from .models import GeofenceEvent, Poi

for m in (GeofenceEvent, Poi,):
    admin.site.register(m)
