# Lab 8 — FoodieNest: Nền tảng Đánh giá Quán Cà phê & Ẩm thực

**Môn học:** PWD301 — Python Web Development  
**Lĩnh vực lựa chọn:** Hệ thống CMS Đánh giá Quán Cà phê & Ẩm thực (Food & Coffee Community CMS)  
**Chuẩn đầu ra đáp ứng:** **CLO2** (Database ORM / Many-to-Many), **CLO5** (Authentication / Session / Cookie Personalization), **CLO8** (Web Security / XSS Prevention / AI Ethics).

---

## 1. Bảng đối chiếu yêu cầu Chapter 08 sang Lab 8

| Yêu cầu cốt lõi Chapter 08 | Triển khai trong Lab 8 (FoodieNest) |
| :--- | :--- |
| **Data Privacy & Avatar** | Tích hợp **Gravatar** qua hàm băm MD5 email (`user.gravatar_url()`). Không lưu trữ ảnh thật của người dùng, đảm bảo tính riêng tư tối đa. |
| **Mạng xã hội nội bộ (Follow Graph)** | Mô hình quan hệ **Self-referential Many-to-Many** trên bảng `User` thông qua `Follow(follower_id, followed_id)`. Logic: Follow / Unfollow chéo, cấm tự follow chính mình, đếm followers/following. |
| **Cá nhân hóa trang chủ qua Cookie** | Bộ lọc hiển thị bài review: `show_followed` (**Tất cả** vs **Chỉ người tôi theo dõi**). Lưu tùy chọn vào **Cookie trình duyệt 30 ngày**. JOIN `Follow` và `ReviewPost` qua thuộc tính `current_user.followed_posts`. |
| **CMS Blog ẩm thực** | Food Blogger và Admin có quyền soạn thảo các bài review chuyên sâu bằng **Markdown** đầy đủ (hỗ trợ `#`, `##`, `###`, blockquote, list, image). Có phân trang `paginate(page=page, per_page=3)` bằng pager Bootstrap. |
| **Bình luận / Đánh giá quán** | Khách hàng gửi đánh giá kèm sao (1-5) gắn với từng quán cà phê (`CafeShop`). Giới hạn Markdown trong comment (`COMMENT_ALLOWED_TAGS` — loại bỏ các thẻ tiêu đề để chống vỡ layout trang). |
| **Bảo mật chống XSS (Sanitize with Bleach)** | Sử dụng thư viện `bleach.clean(strip=True)` với whitelist thẻ nghiêm ngặt trước khi lưu vào CSDL và trước khi render bằng Jinja2 filter `\| safe`. Chống triệt để tấn công Stored XSS. |
| **Nhật ký AI & Ranh giới đạo đức** | File `ai_demo/copilot_log.md` ghi nhận toàn bộ prompt, code AI sinh ra, quá trình rà soát phát hiện lỗ hổng XSS do AI thiếu bleach, và quy chuẩn đạo đức Buổi 39. |

---

## 2. Hướng dẫn cài đặt và chạy hệ thống

### Bước 1: Kích hoạt môi trường ảo & Cài đặt thư viện
```bash
# Di chuyển vào thư mục Lab8
cd c:\ChuyenNganh5\PWD301\Lab8

# Cài đặt thư viện (nếu chưa có)
..\venv\Scripts\pip install -r requirements.txt
```

### Bước 2: Khởi tạo CSDL và Seed dữ liệu mẫu
Hệ thống tự động kết nối **SQL Server** (`localhost\SQLEXPRESS`, database `FoodieNest_Lab8`), và tự động fallback sang SQLite nếu máy không có SQL Server:
```bash
..\venv\Scripts\python seed.py
```

### Bước 3: Khởi chạy Web Server
```bash
..\venv\Scripts\python app.py
```
Mở trình duyệt truy cập: `http://127.0.0.1:5000`

---

## 3. Danh sách tài khoản thử nghiệm (Mật khẩu chung: `pass123`)

| Username | Role | Ý nghĩa trong kịch bản | Link Quick Login tiện lợi |
| :--- | :--- | :--- | :--- |
| `tam_blogger` | **FoodBlogger** | Blogger chuyên viết bài review quán, đã có sẵn nhiều bài viết | `/quick-login/tam_blogger` |
| `an_foodie` | **Customer** | Khách hàng đã theo dõi `tam_blogger` và `binh_admin` | `/quick-login/an_foodie` |
| `binh_admin` | **Admin** | Quản trị viên, kiểm duyệt hệ thống | `/quick-login/binh_admin` |

---

## 4. Kịch bản Demo 5 bước trên lớp

1. **Trang chủ cá nhân hóa qua Cookie:**
   - Vào `/quick-login/an_foodie` rồi về `/`.
   - Mặc định thấy bài của những người `an_foodie` theo dõi (`tam_blogger`, `binh_admin`). Bấm **"Tất cả bài viết"** &rarr; hiển thị toàn bộ bài viết trên hệ thống.
   - Tải lại trang (F5): Lựa chọn của bạn vẫn được lưu giữ nguyên vẹn nhờ **Cookie `show_followed` (30 ngày)**.

2. **Hồ sơ cá nhân & Mạng quan hệ Follow:**
   - Vào `/users/tam_blogger` để xem ảnh đại diện Gravatar, số lượng người theo dõi, và nút **Bỏ theo dõi / + Theo dõi**.
   - Bấm bỏ theo dõi rồi quay lại trang chủ &rarr; các bài viết của Tâm lập tức biến mất khỏi bảng tin cá nhân của An.

3. **CMS Blog ẩm thực có phân trang:**
   - Đăng nhập `tam_blogger`, click nút **+ Viết Review** trên thanh menu (`/reviews/new`).
   - Soạn bài viết bằng định dạng Markdown có tiêu đề `##`, in đậm `**...**`, trích dẫn `> ...`.
   - Vào danh mục `/reviews` để xem bài viết và kiểm tra thanh phân trang Pager Bootstrap (3 bài/trang).

4. **Đánh giá quán & Thử nghiệm bảo mật XSS (CLO8):**
   - Vào quán `Corner Café Da Nang` (`/cafes/1`).
   - Thử gửi nhận xét chứa mã độc XSS:
     ```markdown
     Quán rất đẹp! <script>alert('Bị tấn công XSS!')</script> Đồ uống **rất đậm đà**
     ```
   - Quan sát kết quả: Thẻ `<script>` bị `bleach.clean()` tước bỏ hoàn toàn, không thể thực thi JavaScript, chỉ còn lại chữ in đậm an toàn.

5. **Thảo luận Đạo đức AI & Rà soát Code (Buổi 39):**
   - Bấm vào menu **"🤖 Nhật ký AI (Buổi 39)"** (`/ai-log`) để theo dõi bản review đạo đức học thuật và ví dụ phát hiện lỗi do AI sinh thiếu sanitization.
