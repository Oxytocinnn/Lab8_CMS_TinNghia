import os
import jinja2
from flask import Flask, render_template, redirect, url_for, request, flash, make_response, abort
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_required, current_user, login_user, logout_user

from config import Config
from models import db, User, Role, Category, CafeShop, ReviewPost, CafeComment, Follow, Permission
from markdown_utils import render_markdown, COMMENT_ALLOWED_TAGS, COMMENT_ALLOWED_ATTRS
from decorators import blogger_required, admin_required
from forms import LoginForm, RegisterForm, ReviewPostForm, CafeCommentForm

app = Flask(__name__)
app.config.from_object(Config)

# Hỗ trợ tìm file HTML ở cả thư mục templates lẫn thư mục gốc
app.jinja_loader = jinja2.ChoiceLoader([
    jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    jinja2.FileSystemLoader(os.path.dirname(__file__)),
])

Bootstrap(app)
db.init_app(app)

with app.app_context():
    try:
        db.create_all()
        Role.insert_roles()
        if User.query.count() == 0:
            from seed import run as seed_run
            seed_run()
    except Exception as e:
        print(f"[Init DB] Info: {e}")

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Vui lòng đăng nhập để thực hiện chức năng này."
login_manager.login_message_category = "warning"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_permissions():
    return dict(Permission=Permission)


@app.route("/quick-login/<username>")
def quick_login(username):
    user = User.query.filter_by(username=username).first_or_404()
    login_user(user)
    flash(f"Đã đăng nhập nhanh với tài khoản: {username} ({user.role.name}).", "success")
    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = LoginForm()
    if form.validate_on_submit():
        ident = form.username.data.strip()
        user = User.query.filter((User.username == ident) | (User.email == ident)).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f"Xin chào mừng trở lại, {user.username}!", "success")
            next_page = request.args.get("next")
            if not next_page or not next_page.startswith("/"):
                next_page = url_for("home")
            return redirect(next_page)
        flash("Tên đăng nhập hoặc mật khẩu không chính xác. Vui lòng kiểm tra lại.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f"Tài khoản {username} đã đăng xuất thành công.", "info")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data.strip()).first():
            flash("Tên tài khoản đã tồn tại. Vui lòng chọn tên khác.", "warning")
            return render_template("register.html", form=form)
        if User.query.filter_by(email=form.email.data.strip().lower()).first():
            flash("Email đã được sử dụng bởi một tài khoản khác.", "warning")
            return render_template("register.html", form=form)

        selected_role = Role.query.filter_by(name=form.role.data).first()
        if not selected_role:
            selected_role = Role.query.filter_by(name="Customer").first()

        new_user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            role=selected_role
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash("Đăng ký tài khoản thành công!", "success")
        return redirect(url_for("home"))
    return render_template("register.html", form=form)


@app.route("/")
def home():
    show_param = request.args.get("show")
    if show_param in ("followed", "all"):
        show_followed = (show_param == "followed")
    else:
        show_followed = request.cookies.get("show_followed", "0") == "1"

    if current_user.is_authenticated and show_followed:
        posts = current_user.followed_posts.all()
    else:
        posts = ReviewPost.query.order_by(ReviewPost.created_at.desc()).all()

    cafes = CafeShop.query.limit(4).all()

    resp = make_response(render_template("home.html", posts=posts, cafes=cafes, show_followed=show_followed))
    if show_param in ("followed", "all"):
        resp.set_cookie("show_followed", "1" if show_followed else "0", max_age=30 * 24 * 3600)
    return resp


@app.route("/users/<username>")
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    is_following = current_user.is_authenticated and current_user.is_following(user)
    followers_count = Follow.query.filter_by(followed_id=user.id).count()
    following_count = Follow.query.filter_by(follower_id=user.id).count()
    user_posts = ReviewPost.query.filter_by(author_id=user.id).order_by(ReviewPost.created_at.desc()).all()
    return render_template("profile.html", user=user, is_following=is_following,
                           followers_count=followers_count, following_count=following_count,
                           user_posts=user_posts)


@app.route("/users/<username>/follow", methods=["POST"])
@login_required
def toggle_follow(username):
    target_user = User.query.filter_by(username=username).first_or_404()
    if target_user.id == current_user.id:
        flash("Bạn không thể tự theo dõi chính bản thân mình.", "warning")
        return redirect(url_for("user_profile", username=username))

    if current_user.is_following(target_user):
        current_user.unfollow(target_user)
        flash(f"Đã bỏ theo dõi Food Blogger {username}.", "info")
    else:
        current_user.follow(target_user)
        flash(f"Đã theo dõi thành công Food Blogger {username}.", "success")
    db.session.commit()
    return redirect(url_for("user_profile", username=username))


@app.route("/reviews")
def review_list():
    page = request.args.get("page", 1, type=int)
    posts = ReviewPost.query.order_by(ReviewPost.created_at.desc()).paginate(
        page=page, per_page=3, error_out=False
    )
    return render_template("review_list.html", posts=posts)


@app.route("/reviews/<int:post_id>")
def review_detail(post_id):
    post = ReviewPost.query.get_or_404(post_id)
    return render_template("review_detail.html", post=post)


@app.route("/reviews/new", methods=["GET", "POST"])
@login_required
@blogger_required
def review_new():
    form = ReviewPostForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        summary = form.summary.data.strip() if form.summary.data else ""
        body_md = form.body_md.data.strip()

        body_html = render_markdown(body_md)

        post = ReviewPost(
            title=title,
            summary=summary,
            body_md=body_md,
            body_html=body_html,
            author_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        flash("Đã xuất bản bài viết review ẩm thực mới thành công!", "success")
        return redirect(url_for("review_detail", post_id=post.id))
    return render_template("review_new.html", form=form)


@app.route("/cafes")
def cafes_list():
    category_id = request.args.get("category_id", type=int)
    query = CafeShop.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    cafes = query.all()
    categories = Category.query.all()
    return render_template("cafes.html", cafes=cafes, categories=categories, active_cat=category_id)


@app.route("/cafes/<int:cafe_id>")
def cafe_detail(cafe_id):
    cafe = CafeShop.query.get_or_404(cafe_id)
    form = CafeCommentForm()
    return render_template("cafe_detail.html", cafe=cafe, form=form)


@app.route("/cafes/<int:cafe_id>/comments", methods=["POST"])
@login_required
def add_cafe_comment(cafe_id):
    cafe = CafeShop.query.get_or_404(cafe_id)
    form = CafeCommentForm()

    if form.validate_on_submit():
        body_md = form.body_md.data.strip()
        rating = int(form.rating.data)

        body_html = render_markdown(
            body_md,
            allowed_tags=COMMENT_ALLOWED_TAGS,
            allowed_attrs=COMMENT_ALLOWED_ATTRS
        )

        comment = CafeComment(
            cafe_id=cafe.id,
            author_id=current_user.id,
            rating=rating,
            body_md=body_md,
            body_html=body_html
        )
        db.session.add(comment)
        db.session.commit()
        flash("Cảm ơn bạn đã gửi đánh giá trải nghiệm tại quán!", "success")
    else:
        flash("Nội dung đánh giá không hợp lệ hoặc để trống.", "danger")

    return redirect(url_for("cafe_detail", cafe_id=cafe_id))


@app.route("/ai-log")
def ai_log():
    import markdown
    log_path = os.path.join(os.path.dirname(__file__), "copilot_log.md")
    if not os.path.exists(log_path):
        log_path = os.path.join(os.path.dirname(__file__), "ai_demo", "copilot_log.md")
    content = ""
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            content = markdown.markdown(f.read(), extensions=["fenced_code", "tables"])
    return render_template("ai_log.html", content=content)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
