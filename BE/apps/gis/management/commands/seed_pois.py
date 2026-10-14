from django.core.management.base import BaseCommand

from apps.gis.models import Poi
from apps.vocab.models import Topic

# Toạ độ gần đúng (WGS84) – có thể kéo thả chỉnh lại trên trang WebGIS của Admin.
POIS = [
    ("Trường ĐH Tài nguyên và Môi trường TP.HCM", "school", 10.7957, 106.6660, 200, "236B Lê Văn Sỹ, Tân Bình", ["education", "people"]),
    ("Chợ Bến Thành", "market", 10.7725, 106.6980, 150, "Lê Lợi, Quận 1", ["food", "fruits-vegetables", "clothing"]),
    ("Chợ Bình Tây (Chợ Lớn)", "market", 10.7496, 106.6510, 150, "Tháp Mười, Quận 6", ["food", "fruits-vegetables"]),
    ("Chợ Tân Định", "market", 10.7900, 106.6900, 120, "Hai Bà Trưng, Quận 1", ["food", "fruits-vegetables"]),
    ("Nhà thờ Đức Bà", "religious", 10.7798, 106.6990, 120, "Công xã Paris, Quận 1", ["places"]),
    ("Bưu điện Trung tâm Sài Gòn", "landmark", 10.7799, 106.7000, 100, "Công xã Paris, Quận 1", ["places"]),
    ("Dinh Độc Lập", "landmark", 10.7770, 106.6953, 200, "Nam Kỳ Khởi Nghĩa, Quận 1", ["places"]),
    ("Thảo Cầm Viên Sài Gòn", "zoo", 10.7875, 106.7053, 300, "Nguyễn Bỉnh Khiêm, Quận 1", ["animals", "nature"]),
    ("Công viên Tao Đàn", "park", 10.7745, 106.6925, 200, "Trương Định, Quận 1", ["nature", "sports"]),
    ("Công viên Gia Định", "park", 10.8131, 106.6787, 250, "Hoàng Minh Giám, Gò Vấp", ["nature", "sports"]),
    ("Công viên Lê Văn Tám", "park", 10.7883, 106.6937, 150, "Hai Bà Trưng, Quận 1", ["nature"]),
    ("Sân bay Tân Sơn Nhất", "airport", 10.8185, 106.6588, 800, "Trường Sơn, Tân Bình", ["transport", "places"]),
    ("Ga Sài Gòn", "station", 10.7822, 106.6772, 200, "Nguyễn Thông, Quận 3", ["transport", "places"]),
    ("Bảo tàng Chứng tích Chiến tranh", "museum", 10.7795, 106.6922, 120, "Võ Văn Tần, Quận 3", ["places"]),
    ("Bảo tàng Lịch sử Việt Nam", "museum", 10.7881, 106.7046, 120, "Nguyễn Bỉnh Khiêm, Quận 1", ["places"]),
    ("Phố đi bộ Nguyễn Huệ", "landmark", 10.7740, 106.7038, 250, "Nguyễn Huệ, Quận 1", ["places", "people"]),
    ("Nhà hát Thành phố", "theater", 10.7766, 106.7031, 100, "Công trường Lam Sơn, Quận 1", ["places"]),
    ("Thư viện Khoa học Tổng hợp", "library", 10.7737, 106.6963, 100, "Lý Tự Trọng, Quận 1", ["education"]),
    ("Bệnh viện Chợ Rẫy", "hospital", 10.7577, 106.6595, 250, "Nguyễn Chí Thanh, Quận 5", ["body", "people"]),
    ("Bệnh viện Nhi Đồng 1", "hospital", 10.7685, 106.6705, 200, "Sư Vạn Hạnh, Quận 10", ["body", "people"]),
    ("Chùa Vĩnh Nghiêm", "religious", 10.7901, 106.6827, 120, "Nam Kỳ Khởi Nghĩa, Quận 3", ["places"]),
    ("Landmark 81", "landmark", 10.7950, 106.7218, 200, "Điện Biên Phủ, Bình Thạnh", ["places", "technology"]),
    ("Bitexco Financial Tower", "landmark", 10.7716, 106.7044, 120, "Hải Triều, Quận 1", ["places"]),
    ("AEON Mall Tân Phú", "supermarket", 10.8018, 106.6178, 300, "Tân Thắng, Tân Phú", ["food", "clothing", "technology"]),
    ("Co.opmart Cống Quỳnh", "supermarket", 10.7680, 106.6890, 120, "Cống Quỳnh, Quận 1", ["food", "fruits-vegetables", "home"]),
    ("Công viên Văn hóa Đầm Sen", "park", 10.7680, 106.6380, 400, "Hòa Bình, Quận 11", ["nature", "sports", "animals"]),
    ("Khu du lịch Suối Tiên", "park", 10.8660, 106.8030, 500, "Xa lộ Hà Nội, TP. Thủ Đức", ["nature", "animals"]),
    ("Sân vận động Thống Nhất", "stadium", 10.7615, 106.6640, 200, "Đào Duy Từ, Quận 10", ["sports"]),
    ("Phố Bùi Viện", "restaurant", 10.7672, 106.6930, 150, "Bùi Viện, Quận 1", ["food", "places"]),
    ("Chợ đêm Hồ Thị Kỷ", "restaurant", 10.7660, 106.6800, 100, "Hồ Thị Kỷ, Quận 10", ["food", "fruits-vegetables"]),
]


class Command(BaseCommand):
    help = "Tạo ~30 điểm quan tâm (POI) mẫu quanh TP.HCM gắn với chủ đề từ vựng"

    def handle(self, *args, **opts):
        for name, cat, lat, lng, radius, address, topics in POIS:
            poi, _ = Poi.objects.update_or_create(name=name, defaults={
                "category": cat, "lat": lat, "lng": lng, "radius_m": radius, "address": address})
            poi.topics.set(Topic.objects.filter(slug__in=topics))
        self.stdout.write(self.style.SUCCESS(f"{len(POIS)} POI"))
