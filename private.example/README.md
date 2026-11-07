# private/ – những thứ KHÔNG BAO GIỜ lên git

Sao chép thư mục này thành `private/` (đã có trong `.gitignore`) rồi điền giá trị thật. Mọi script của dự án đọc
bí mật từ đây; trong code không có IP, mật khẩu hay khóa nào.

```
private/
├── secrets/
│   ├── server.env              # địa chỉ server + khóa SSH cho deploy/*.sh  (mẫu: server.env.example)
│   ├── firebase-adminsdk.json  # khóa service account Firebase (thông báo đẩy) – push.sh gửi lên server
│   └── google-services.json    # cấu hình Firebase của app Android (bản gốc; Gradle dùng bản ở MOBILE/android/app/)
├── bao-cao/                    # bản thảo báo cáo, đề cương, phiếu chấm, ảnh chụp màn hình
└── tham-khao/                  # mã nguồn SnapLingua cũ, bản train YOLO thô, datasets tải về
```

Ngoài thư mục này, hai chỗ bí mật khác cũng bị `.gitignore` chặn:

* `.env` ở thư mục gốc – cấu hình Django / Docker (mẫu: `.env.example`), `docker compose` và `BE/config/settings` đọc nó;
* khóa SSH `~/.ssh/lingoprism.pem` – nằm ngoài dự án, `server.env` trỏ tới.

Kiểm tra trước khi push: `git status` không được có `private/`, `.env`, `*.pem`, `*.json` khóa; CI chạy gitleaks
(`.gitleaks.toml`) để chặn lần nữa.
