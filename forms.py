from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField("Tên người dùng hoặc Email", validators=[DataRequired(message="Vui lòng nhập tên người dùng hoặc email.")])
    password = PasswordField("Mật khẩu", validators=[DataRequired(message="Vui lòng nhập mật khẩu.")])
    remember = BooleanField("Ghi nhớ đăng nhập")
    submit = SubmitField("Đăng nhập")


class RegisterForm(FlaskForm):
    username = StringField("Tên tài khoản", validators=[DataRequired(message="Vui lòng nhập tên tài khoản."), Length(min=3, max=50, message="Tên tài khoản từ 3 đến 50 ký tự.")])
    email = StringField("Email", validators=[DataRequired(message="Vui lòng nhập email."), Email(message="Email không hợp lệ."), Length(max=120)])
    password = PasswordField("Mật khẩu", validators=[DataRequired(message="Vui lòng nhập mật khẩu."), Length(min=6, message="Mật khẩu tối thiểu 6 ký tự.")])
    confirm_password = PasswordField("Xác nhận mật khẩu", validators=[DataRequired(message="Vui lòng xác nhận mật khẩu."), EqualTo("password", message="Mật khẩu xác nhận không trùng khớp.")])
    role = SelectField("Vai trò", choices=[("Customer", "Customer (Khách hàng)"), ("FoodBlogger", "FoodBlogger (Blogger Review)")], default="Customer")
    submit = SubmitField("Đăng ký tài khoản")


class ReviewPostForm(FlaskForm):
    title = StringField("Tiêu đề bài viết", validators=[DataRequired(message="Tiêu đề không được để trống."), Length(max=255)])
    summary = StringField("Tóm tắt ngắn", validators=[Length(max=300)])
    body_md = TextAreaField("Nội dung bài viết (Hỗ trợ Markdown)", validators=[DataRequired(message="Nội dung không được để trống.")])
    submit = SubmitField("Xuất bản bài viết")


class CafeCommentForm(FlaskForm):
    rating = SelectField("Đánh giá sao", choices=[("5", "⭐⭐⭐⭐⭐ (5 sao - Tuyệt vời)"),
                                                  ("4", "⭐⭐⭐⭐ (4 sao - Rất tốt)"),
                                                  ("3", "⭐⭐⭐ (3 sao - Tạm ổn)"),
                                                  ("2", "⭐⭐ (2 sao - Cần cải thiện)"),
                                                  ("1", "⭐ (1 sao - Thất vọng)")], default="5")
    body_md = TextAreaField("Nhận xét của bạn (Hỗ trợ Markdown cơ bản)", validators=[DataRequired(message="Vui lòng nhập nhận xét của bạn.")])
    submit = SubmitField("Gửi đánh giá")
