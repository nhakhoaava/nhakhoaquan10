# nhakhoaavadental.vn – Nha khoa quận 10 (Nha khoa AVA)

Site tĩnh (HTML/CSS/JS), deploy thẳng lên Vercel, không cần build phía server.
Từ khóa chính: **nha khoa quận 10**. Bảng màu giữ nguyên từ source niềng răng (biến `:root` trong `assets/css/style.css`).

## Cấu trúc trang
| URL | Nội dung | Từ khóa chính |
|---|---|---|
| `/` | Trang chủ tổng hợp 4 dịch vụ | nha khoa quận 10 |
| `/nieng-rang/` | Niềng răng | niềng răng quận 10 |
| `/trong-rang-implant/` | Trồng răng Implant | trồng răng implant quận 10 |
| `/rang-su/` | Răng sứ | bọc răng sứ quận 10 |
| `/tram-rang-tham-my/` | Trám răng thẩm mỹ | trám răng thẩm mỹ quận 10 |
| `/bang-gia/` | Bảng giá tham khảo | bảng giá nha khoa quận 10 |
| `/hinh-anh-truoc-sau/` + 4 trang `/hinh-anh-<dịch-vụ>/` | Thư viện ảnh ca thực tế | |
| `/gioi-thieu/`, `/bac-si-pham-viet-hung/`, 3 bài kiến thức niềng răng | Giữ từ source cũ | |

## Upload ảnh ca đã hoàn thành
Mỗi dịch vụ có 1 thư mục riêng:

    assets/images/nieng-rang/            (đã có 144 ca)
    assets/images/trong-rang-implant/
    assets/images/rang-su/
    assets/images/tram-rang-tham-my/

1. Bỏ ảnh vào thư mục tương ứng (tên file tùy ý).
2. `pip install pillow` (1 lần), rồi `python3 build.py`.
3. Script tự: đổi tên chuẩn SEO (`<dịch-vụ>-quan-10-truoc-sau-NN`), bỏ EXIF, tạo webp (rộng 900px) + thumb 420px,
   cập nhật trang thư viện, trang dịch vụ, trang chủ, sitemap.
4. Trang thư viện của dịch vụ **chưa có ảnh** tự đặt `noindex` và không nằm trong sitemap; có ảnh là tự bật index.
5. Commit và push để Vercel deploy.

Khuyến nghị ảnh: chụp/ghép dạng dọc (tỉ lệ 3:4) giống ảnh niềng răng hiện có để lưới ảnh đều.
Không đưa ảnh chứa thông tin bệnh nhân (tên, số điện thoại, mặt thấy rõ) khi chưa có đồng ý bằng văn bản.

## Sửa bảng giá
Mở `build.py`, sửa `PRICE_OTHER` (Implant, răng sứ, trám) và `PRICE_NIENG_ROWS` (niềng răng), chạy lại `python3 build.py`.
Để `None` thì trang hiển thị "Báo giá sau khi thăm khám".

## Việc cần làm / cần xác nhận
1. **Giá Implant, răng sứ, trám răng**: hiện để "Báo giá sau khi thăm khám" vì chưa có số liệu thật.
2. **Nội dung 3 dịch vụ mới** (Implant, răng sứ, trám) là nội dung giáo dục chung. Nhờ bác sĩ phụ trách duyệt lại,
   và bổ sung thông tin thật của AVA (vật liệu, hãng trụ, thời gian bảo hành, bác sĩ phụ trách từng dịch vụ).
3. **Trả góp**: các bài/đoạn nhắc trả góp kế thừa từ source cũ; chưa có kỳ hạn, lãi suất, giấy tờ cụ thể. Chỉ giữ nếu AVA thật sự có chính sách.
4. **Ảnh niềng răng cũ có chữ/banner** (`benhvienthammy.com.vn`, logo AVA, số điện thoại in trên ảnh). Nên xuất lại ảnh gốc không banner, hoặc thống nhất một mẫu banner cho cả 4 dịch vụ.
5. Khai báo domain `nhakhoaavadental.vn` trên Vercel, nộp `https://nhakhoaavadental.vn/sitemap.xml` lên Google Search Console,
   tạo/xác minh Google Business Profile "nha khoa quận 10" (rất quan trọng cho tìm kiếm cục bộ).
6. Nếu domain cũ `niengrangtphcm.vn` vẫn chạy, đặt redirect 301 về các trang tương ứng để không trùng nội dung.
