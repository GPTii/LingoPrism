from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.vocab.models import Topic


class Poi(TimeStampedModel):
    """Point of interest. Spatial index: GiST on ll_to_earth(lat, lng) (cube + earthdistance)."""

    class Category(models.TextChoices):
        MARKET = "market", "Chợ"
        SUPERMARKET = "supermarket", "Siêu thị / TTTM"
        HOSPITAL = "hospital", "Bệnh viện"
        SCHOOL = "school", "Trường học"
        PARK = "park", "Công viên"
        ZOO = "zoo", "Sở thú"
        MUSEUM = "museum", "Bảo tàng"
        AIRPORT = "airport", "Sân bay"
        STATION = "station", "Nhà ga / bến xe"
        RELIGIOUS = "religious", "Chùa / nhà thờ"
        RESTAURANT = "restaurant", "Nhà hàng / ẩm thực"
        STADIUM = "stadium", "Sân vận động"
        LANDMARK = "landmark", "Địa danh"
        LIBRARY = "library", "Thư viện"
        THEATER = "theater", "Nhà hát / rạp"
        OTHER = "other", "Khác"

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=12, choices=Category.choices)
    lat = models.FloatField()
    lng = models.FloatField()
    radius_m = models.PositiveIntegerField(default=150, help_text="Bán kính geofence (m)")
    address = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=300, blank=True)
    topics = models.ManyToManyField(Topic, related_name="pois", blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class GeofenceEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="geofence_events")
    poi = models.ForeignKey(Poi, on_delete=models.CASCADE, related_name="events")
    lat = models.FloatField()
    lng = models.FloatField()
    distance_m = models.FloatField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
