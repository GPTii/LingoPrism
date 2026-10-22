# Ảnh tự chụp để đánh giá model nhận diện

Bỏ ảnh chụp thật vào đây (điện thoại, ở nhà / trường / ngoài đường), **tên file là vật trong ảnh** – nhãn YOLO hoặc
slug của từ (xem `AI/classes.yaml`):

* `cup.jpg`, `cup_2.jpg`, `cup_3.jpg` – ảnh một vật
* `cup+spoon+bowl.jpg` – ảnh nhiều vật (mọi vật trong ảnh mà app có từ vựng)
* hoặc theo thư mục: `pillow/IMG_001.jpg`, `pillow/IMG_002.jpg`

Mục tiêu khoảng 200 ảnh, mỗi lớp 2–3 ảnh, đủ góc chụp / ánh sáng / nền lộn xộn. Ảnh có tên không khớp lớp nào bị bỏ qua.
Sau đó chạy lại `AI/notebooks/07_yolo_report.ipynb` (hoặc `python AI/scripts/eval_photos.py AI/eval_photos --model ...`):
bảng "ảnh tự chụp" và `AI/report/yolo/` sẽ có số liệu trên ảnh thật của bạn.
