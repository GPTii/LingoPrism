"""Protections against abuse once the app is public (rate limits, sessions, uploaded images)."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.detection.models import Photo

pytestmark = pytest.mark.django_db


def _login(client, email, password="wrong-password", ip="10.0.0.1"):
    return client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json", REMOTE_ADDR=ip)


def test_password_guessing_is_rate_limited_per_ip():
    c = APIClient()
    codes = [_login(c, f"u{i}@example.com").status_code for i in range(41)]
    assert codes[:40] == [400] * 40 and codes[40] == 429  # 40/min: a classroom shares one IP
    assert _login(c, "u99@example.com").data["detail"].startswith("Bạn thao tác quá nhanh")


def test_password_guessing_one_account_from_many_ips_is_rate_limited():
    User.objects.create_user("victim@example.com", "Strong!Pass123")
    c = APIClient()
    codes = [_login(c, "victim@example.com", ip=f"10.0.1.{i}").status_code for i in range(11)]
    assert codes[10] == 429  # 10/hour per target e-mail, whatever the IP


def test_password_reset_logs_out_every_session():
    c = APIClient()
    res = c.post("/api/v1/auth/register/", {"email": "a@example.com", "password": "Strong!Pass123"}, format="json")
    refresh = res.data["tokens"]["refresh"]
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['tokens']['access']}")
    assert c.post("/api/v1/auth/password/change/", {"old_password": "Strong!Pass123",
                                                    "new_password": "Another!Pass456"}, format="json").status_code == 200
    # the refresh token issued before the change no longer works (a stolen session does not survive)
    assert APIClient().post("/api/v1/auth/refresh/", {"refresh": refresh}, format="json").status_code == 401


def _jpeg_with_gps():
    im = Image.new("RGB", (3000, 2000), (120, 80, 40))
    exif = Image.Exif()
    exif[0x8825] = {2: (21.0, 1.0, 30.0), 4: (105.0, 50.0, 0.0)}  # GPSInfo: latitude / longitude
    exif[0x0112] = 6  # orientation: rotate 90°
    buf = io.BytesIO()
    im.save(buf, "JPEG", exif=exif)
    return SimpleUploadedFile("IMG_1234.jpg", buf.getvalue(), content_type="image/jpeg")


def test_uploaded_photo_loses_gps_and_original_name(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    user = User.objects.create_user("p@example.com", "Strong!Pass123")
    photo = Photo.objects.create(user=user, image=_jpeg_with_gps())
    assert "IMG_1234" not in photo.image.name
    with Image.open(photo.image.path) as im:
        assert not im.getexif()  # no GPS, no camera data
        assert im.size == (1365, 2048)  # orientation applied to the pixels, then downscaled


def test_decompression_bomb_is_refused(settings, tmp_path):
    from django.core.exceptions import ValidationError

    from apps.core.images import MAX_PIXELS

    settings.MEDIA_ROOT = str(tmp_path)
    user = User.objects.create_user("b@example.com", "Strong!Pass123")
    buf = io.BytesIO()
    Image.new("1", (MAX_PIXELS // 1000 + 1000, 1000)).save(buf, "PNG")  # tiny file, huge declared size
    with pytest.raises(ValidationError):
        Photo.objects.create(user=user, image=SimpleUploadedFile("x.png", buf.getvalue(), content_type="image/png"))


def test_redis_down_is_a_cache_miss_not_an_error():
    """The rate-limit counters live in the cache: Redis being down must not take the API down with it."""
    import time

    from apps.core.cache import ResilientRedisCache

    ResilientRedisCache._down_until = 0.0
    cache = ResilientRedisCache("redis://127.0.0.1:6390/0", {"OPTIONS": {"socket_connect_timeout": 1, "socket_timeout": 1}})
    assert cache.get("k", "fallback") == "fallback"
    start = time.monotonic()
    assert cache.add("k", 1) is False and cache.get_many(["a", "b"]) == {} and cache.incr("n") == 1
    assert time.monotonic() - start < 0.5  # no new connection attempts while the breaker is open
    cache.set("k", 1)
    cache.delete("k")
    ResilientRedisCache._down_until = 0.0
