from django.contrib import admin

from .models import CorrectionMemory, Detection, DetectionItem, ModelVersion, Photo

for m in (Detection, DetectionItem, ModelVersion, Photo, CorrectionMemory):
    admin.site.register(m)
