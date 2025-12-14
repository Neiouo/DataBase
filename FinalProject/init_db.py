from app import create_app
from models import db, User
import os

app = create_app()
app.app_context().push()

print("Creating database tables...")
db.create_all()

# create a default admin user if not exist
if not User.query.filter_by(email="admin@campus.local").first():
    admin = User(name="Admin", email="admin@campus.local", role="staff")
    admin.set_password("adminpass")
    db.session.add(admin)
    db.session.commit()
    print("Created admin user: admin@campus.local / adminpass")
else:
    print("Admin user already exists.")
