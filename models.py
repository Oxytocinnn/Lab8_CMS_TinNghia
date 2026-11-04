import hashlib
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Permission:
    VIEW = 1
    COMMENT = 2
    WRITE_POST = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), unique=True, nullable=False)
    permissions = db.Column(db.Integer, nullable=False, default=0)

    users = db.relationship("User", back_populates="role")

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def has_permission(self, perm):
        return (self.permissions & perm) == perm

    @staticmethod
    def insert_roles():
        roles = {
            "Customer": Permission.VIEW | Permission.COMMENT,
            "FoodBlogger": Permission.VIEW | Permission.COMMENT | Permission.WRITE_POST,
            "Admin": (Permission.VIEW | Permission.COMMENT | Permission.WRITE_POST |
                      Permission.MODERATE | Permission.ADMIN),
        }
        for name, perms in roles.items():
            role = Role.query.filter_by(name=name).first()
            if role is None:
                role = Role(name=name)
            role.permissions = perms
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return f"<Role {self.name}>"


class Follow(db.Model):
    __tablename__ = "follows"

    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Unicode(120), unique=True, nullable=False, index=True)
    username = db.Column(db.Unicode(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Unicode(255), nullable=False)
    bio = db.Column(db.Unicode(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    role = db.relationship("Role", back_populates="users")

    def gravatar_url(self, size=80):
        email_hash = hashlib.md5(self.email.strip().lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s={size}"

    def follow(self, user):
        if not self.is_following(user) and user.id != self.id:
            db.session.add(Follow(follower_id=self.id, followed_id=user.id))

    def unfollow(self, user):
        f = Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        return Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return (ReviewPost.query
                .join(Follow, Follow.followed_id == ReviewPost.author_id)
                .filter(Follow.follower_id == self.id)
                .order_by(ReviewPost.created_at.desc()))

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_admin(self):
        return self.can(Permission.ADMIN)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username}>"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(100), unique=True, nullable=False, index=True)

    cafes = db.relationship("CafeShop", backref="category", lazy="select")

    def __repr__(self):
        return f"<Category {self.name}>"


class CafeShop(db.Model):
    __tablename__ = "cafe_shops"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(200), nullable=False, index=True)
    address = db.Column(db.Unicode(255), nullable=False)
    price_range = db.Column(db.Unicode(100), default="35.000đ - 70.000đ")
    description = db.Column(db.UnicodeText, nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    comments = db.relationship("CafeComment", backref="cafe", cascade="all, delete-orphan",
                               order_by="desc(CafeComment.created_at)")

    def __repr__(self):
        return f"<CafeShop {self.name}>"


class ReviewPost(db.Model):
    __tablename__ = "review_posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(255), nullable=False)
    summary = db.Column(db.Unicode(300), nullable=True)
    body_md = db.Column(db.UnicodeText, nullable=False)
    body_html = db.Column(db.UnicodeText, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    author = db.relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<ReviewPost {self.title}>"


class CafeComment(db.Model):
    __tablename__ = "cafe_comments"

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, default=5)
    body_md = db.Column(db.UnicodeText, nullable=False)
    body_html = db.Column(db.UnicodeText, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cafe_id = db.Column(db.Integer, db.ForeignKey("cafe_shops.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    author = db.relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<CafeComment #{self.id} on Cafe #{self.cafe_id}>"
