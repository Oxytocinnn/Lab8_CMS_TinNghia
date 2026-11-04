import sys
import os

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from app import app
from config import ensure_database_exists
from models import db, Role, User, Follow, Category, CafeShop, ReviewPost, CafeComment
from markdown_utils import render_markdown, COMMENT_ALLOWED_TAGS, COMMENT_ALLOWED_ATTRS


def run():
    print("[Seed] Đang kiểm tra kết nối CSDL...")
    ensure_database_exists()

    with app.app_context():
        print("[Seed] Đang khởi tạo lại cấu trúc bảng (drop & create)...")
        db.drop_all()
        db.create_all()

        print("[Seed] Tạo các nhóm quyền (Roles)...")
        Role.insert_roles()
        admin_role = Role.query.filter_by(name="Admin").first()
        blogger_role = Role.query.filter_by(name="FoodBlogger").first()
        customer_role = Role.query.filter_by(name="Customer").first()

        print("[Seed] Tạo danh sách người dùng...")
        tam = User(
            email="tam@foodienest.vn",
            username="tam_blogger",
            bio="Food Blogger đam mê khám phá các tiệm cà phê đặc sản và không gian yên tĩnh.",
            role=blogger_role
        )
        tam.set_password("pass123")

        an = User(
            email="an@foodienest.vn",
            username="an_foodie",
            bio="Tín đồ cà phê phin và các món tráng miệng hấp dẫn.",
            role=customer_role
        )
        an.set_password("pass123")

        binh = User(
            email="binh@foodienest.vn",
            username="binh_admin",
            bio="Quản trị viên hệ thống FoodieNest Da Nang.",
            role=admin_role
        )
        binh.set_password("pass123")

        db.session.add_all([tam, an, binh])
        db.session.flush()

        print("[Seed] Thiết lập quan hệ Follow...")
        db.session.add_all([
            Follow(follower_id=an.id, followed_id=tam.id),
            Follow(follower_id=an.id, followed_id=binh.id),
            Follow(follower_id=binh.id, followed_id=tam.id),
        ])

        print("[Seed] Tạo danh mục và quán cà phê mẫu...")
        cat_specialty = Category(name="Specialty Coffee & Rang Xay")
        cat_work = Category(name="Không Gian Làm Việc & Acoustic")
        cat_retro = Category(name="Cà Phê Truyền Thống & Hoài Niệm")
        db.session.add_all([cat_specialty, cat_work, cat_retro])
        db.session.flush()

        corner_cafe = CafeShop(
            name="Corner Café Da Nang",
            address="22 Đào Duy Từ, Quận Thanh Khê, Đà Nẵng",
            price_range="25.000đ - 55.000đ",
            description="Quán cà phê mang phong cách Indochine hoài cổ, nổi tiếng với cà phê phin đậm vị và bạc xỉu kem béo.",
            category=cat_retro
        )
        tinnghia_cafe = CafeShop(
            name="Tín Nghĩa Specialty Coffee",
            address="108 Quang Trung, Quận Hải Châu, Đà Nẵng",
            price_range="45.000đ - 90.000đ",
            description="Trải nghiệm hương vị Arabica Cầu Đất nguyên bản cùng các phương pháp pha chế Pour Over V60 và Cold Brew ủ 24h.",
            category=cat_specialty
        )
        workshop_cafe = CafeShop(
            name="The Workshop Da Nang",
            address="45 Lê Duẩn, Quận Hải Châu, Đà Nẵng",
            price_range="35.000đ - 65.000đ",
            description="Không gian mở yên tĩnh ngập tràn ánh sáng tự nhiên, trang bị ổ cắm điện từng bàn, thích hợp học tập và làm việc.",
            category=cat_work
        )
        db.session.add_all([corner_cafe, tinnghia_cafe, workshop_cafe])
        db.session.flush()

        print("[Seed] Tạo bài viết CMS Markdown...")
        posts_data = [
            (
                "Trải nghiệm Pour Over V60 tại Tín Nghĩa Specialty Coffee",
                "Review chi tiết về hương vị hạt Ethiopia Yirgacheffe và phong cách phục vụ tại Tín Nghĩa.",
                """## Một buổi sáng tại Tín Nghĩa Specialty Coffee

Nếu bạn là người đam mê **cà phê thủ công**, Tín Nghĩa là điểm đến không thể bỏ qua:

### 1. Không gian và Trải nghiệm
- Quầy bar mở cho phép bạn trò chuyện trực tiếp với Barista.
- Mùi hương cà phê rang xay mới lan tỏa khắp phòng.

### 2. Đánh giá hương vị
Hạt cà phê *Ethiopia Yirgacheffe* mang hương hoa nhài thoang thoảng và hậu vị ngọt thanh của cam chanh. Nhiệt độ chiết xuất được kiểm soát rất chuẩn xác.

> **Lời khuyên:** Hãy thử thưởng thức ly không đường đá để cảm nhận trọn vẹn tầng hương!""",
                tam
            ),
            (
                "Ghé Corner Café tìm lại hương vị cà phê phin xưa",
                "Góc nhỏ bình yên giữa lòng Đà Nẵng với những tách cà phê thơm nồng.",
                """## Góc cà phê hoài niệm

Giữa phố thị ồn ào, **Corner Café** giữ lại nét mộc mạc của những năm 90:

- **Bạc xỉu ba tầng:** Béo ngậy, ngọt dịu vừa phải.
- **Cà phê muối:** Lớp bọt kem mặn kết hợp cà phê Robusta đậm vị.

Chỗ ngồi râm mát dưới tán cây xanh là nơi lý tưởng để đọc một cuốn sách hay vào cuối tuần.""",
                tam
            ),
            (
                "Quy chuẩn cộng đồng và Đạo đức Review trên FoodieNest",
                "Thông điệp từ Ban Quản trị về việc xây dựng cộng đồng ẩm thực văn minh, khách quan.",
                """## Tiêu chí đánh giá bài review trên FoodieNest

Để đảm bảo tính khách quan và trải nghiệm tốt nhất cho độc giả:

1. **Tính xác thực:** Mọi bài review đều dựa trên trải nghiệm thực tế.
2. **Tôn trọng tác quyền:** Ghi rõ nguồn hình ảnh và trích dẫn.
3. **Bảo vệ cộng đồng:** Nghiêm cấm chèn mã độc, link quảng cáo rác hoặc từ ngữ kích động.""",
                binh
            ),
            (
                "Top 5 món tráng miệng ăn kèm trà đào tại The Workshop",
                "Gợi ý các món bánh ngọt tươi ngon tiếp thêm năng lượng khi chạy deadline.",
                """## Bánh ngon cho ngày làm việc năng suất

Làm việc cả ngày tại The Workshop, đừng quên nạp năng lượng với:
- Croissant hạnh nhân nướng giòn.
- Tiramisu phô mai mascarpone béo mịn.
- Bánh mousse chanh dây thanh mát.""",
                tam
            )
        ]

        for title, summary, body_md, author in posts_data:
            post = ReviewPost(
                title=title,
                summary=summary,
                body_md=body_md,
                body_html=render_markdown(body_md),
                author=author
            )
            db.session.add(post)

        print("[Seed] Tạo bình luận và đánh giá quán...")
        comments_data = [
            (
                corner_cafe.id,
                an.id,
                5,
                "Cà phê sữa đá ở đây đậm đà đúng gu mình! Không gian hoài cổ chụp ảnh rất vintage. **Đánh giá 5/5**."
            ),
            (
                tinnghia_cafe.id,
                tam.id,
                5,
                "Cold Brew ủ lạnh 24h vị hoa quả nhiệt đới rất rõ ràng. Bạn barista tư vấn cực kỳ nhiệt tình và am hiểu hạt!"
            ),
            (
                workshop_cafe.id,
                an.id,
                4,
                "Wifi mạnh, điều hòa mát mẻ, bàn ghế ngồi làm việc cả ngày không mỏi lưng. Nhạc lofi nhẹ nhàng rất dễ tập trung."
            )
        ]

        for cafe_id, author_id, rating, body_md in comments_data:
            comment = CafeComment(
                cafe_id=cafe_id,
                author_id=author_id,
                rating=rating,
                body_md=body_md,
                body_html=render_markdown(body_md, allowed_tags=COMMENT_ALLOWED_TAGS, allowed_attrs=COMMENT_ALLOWED_ATTRS)
            )
            db.session.add(comment)

        db.session.commit()
        print("=" * 60)
        print("SEED DỮ LIỆU THÀNH CÔNG CHO LAB 8 (FoodieNest)!")
        print("Tài khoản mẫu (Mật khẩu chung: pass123):")
        print("  1. tam_blogger  (Role: FoodBlogger)  -> Đăng nhập nhanh: /quick-login/tam_blogger")
        print("  2. an_foodie    (Role: Customer)     -> Đăng nhập nhanh: /quick-login/an_foodie")
        print("  3. binh_admin   (Role: Admin)        -> Đăng nhập nhanh: /quick-login/binh_admin")
        print("Quan hệ Follow: an_foodie theo dõi tam_blogger & binh_admin; binh_admin theo dõi tam_blogger.")
        print("=" * 60)


if __name__ == "__main__":
    run()
