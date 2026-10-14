from django.contrib import admin

from .models import Detection, DetectionItem, ModelVersion, Photo

for m in (Detection, DetectionItem, ModelVersion, Photo,):
    admin.site.register(m)
