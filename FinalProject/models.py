from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    # Map the Python attribute `user_id` to the existing DB column `id` (for compatibility with older schemas)
    user_id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    # Map Python attribute to the existing DB column 'password' to stay compatible with legacy schema
    password_hash = db.Column('password', db.String(200), nullable=False)
    role = db.Column(db.String(20), default="student")  # student or staff
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reports = db.relationship("Report", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Flask-Login expects a string id; this ensures compatibility
        return str(self.user_id)

class Item(db.Model):
    __tablename__ = "items"
    item_id = db.Column(db.Integer, primary_key=True)
    # Legacy DB schema had a `name` column; keep it mapped but optional
    name = db.Column('name', db.String(150), nullable=True)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    # items table also has `location` and `date_found` in legacy schema
    location = db.Column(db.String(200), nullable=True)
    date_found = db.Column('date_found', db.DateTime, nullable=True)
    image_path = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    report = db.relationship("Report", back_populates="item", uselist=False)

class Report(db.Model):
    __tablename__ = "reports"
    report_id = db.Column(db.Integer, primary_key=True)
    # Ensure ForeignKey matches the actual DB column name `id` in the users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.item_id'), nullable=False)
    report_type = db.Column(db.String(10), nullable=False)  # lost or found
    location = db.Column(db.String(200), nullable=True)
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="pending")  # pending/matched/claimed

    user = db.relationship("User", back_populates="reports")
    item = db.relationship("Item", back_populates="report")
