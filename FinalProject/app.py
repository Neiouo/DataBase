import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin
from models import db, User, Item, Report
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXT = {'png','jpg','jpeg','gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lost_and_found.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # no extra FLUser wrapper needed; User model now includes UserMixin

    @app.route('/')
    def index():
        q = request.args.get('q','').strip()
        category = request.args.get('category','')
        reports = Report.query.join(Item).order_by(Report.date_reported.desc())
        if q:
            reports = reports.filter(Item.description.ilike(f'%{q}%'))
        if category:
            reports = reports.filter(Item.category==category)
        reports = reports.all()
        categories = ['ID/Card','Bottle','Umbrella','Electronics','Clothing','Other']
        return render_template('index.html', reports=reports, categories=categories, q=q, category=category)

    @app.route('/register', methods=['GET','POST'])
    def register():
        if request.method=='POST':
            name = request.form['name'].strip()
            email = request.form['email'].strip().lower()
            password = request.form['password']
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'warning')
                return redirect(url_for('register'))
            user = User(name=name, email=email, role='student')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registered. Please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method=='POST':
            email = request.form['email'].strip().lower()
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                flash('Logged in', 'success')
                return redirect(url_for('index'))
            flash('Invalid credentials', 'danger')
            return redirect(url_for('login'))
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        logout_user()
        flash('Logged out', 'info')
        return redirect(url_for('index'))

    @app.route('/submit', methods=['GET','POST'])
    @login_required
    def submit():
        categories = ['ID/Card','Bottle','Umbrella','Electronics','Clothing','Other']
        if request.method=='POST':
            report_type = request.form.get('report_type')
            category = request.form.get('category')
            description = request.form.get('description')
            location = request.form.get('location')
            file = request.files.get('image')
            image_path = None
            if file and allowed_file(file.filename):
                fname = secure_filename(f"{int(datetime.utcnow().timestamp())}_" + file.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                file.save(save_path)
                image_path = os.path.join('static','uploads', fname)
            # create item and report
            # populate a legacy `name` field to keep compatibility with older DB schemas
            item = Item(category=category, name=category, description=description, image_path=image_path, location=location)
            db.session.add(item)
            db.session.commit()
            report = Report(user_id=current_user.user_id, item_id=item.item_id, report_type=report_type, location=location)
            db.session.add(report)
            db.session.commit()
            # simple notification: print to console (or integrate SMTP)
            print(f"Notification: new {report_type} report added (category={category}, location={location})")
            flash('Report submitted', 'success')
            return redirect(url_for('index'))
        return render_template('submit.html', categories=categories)

    @app.route('/report/<int:report_id>')
    def view_report(report_id):
        r = Report.query.get_or_404(report_id)
        return render_template('report.html', r=r)

    @app.route('/admin')
    @login_required
    def admin():
        # only staff can access; simple check
        if current_user.role!='staff':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        reports = Report.query.order_by(Report.date_reported.desc()).all()
        categories = ['ID/Card','Bottle','Umbrella','Electronics','Clothing','Other']
        return render_template('admin.html', reports=reports, categories=categories)

    @app.route('/admin/update_status/<int:report_id>', methods=['POST'])
    @login_required
    def update_status(report_id):
        if current_user.role!='staff':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        r = Report.query.get_or_404(report_id)
        new_status = request.form.get('status')
        r.status = new_status
        db.session.commit()
        flash('Status updated', 'success')
        return redirect(url_for('admin'))

    @app.route('/admin/delete_report/<int:report_id>', methods=['POST'])
    @login_required
    def delete_report(report_id):
        # only staff can delete reports
        if current_user.role!='staff':
            flash('Access denied', 'danger')
            return redirect(url_for('index'))
        r = Report.query.get_or_404(report_id)
        item = r.item
        try:
            db.session.delete(r)
            # ensure delete flushed so subsequent query reflects change
            db.session.flush()
            # if no other reports reference this item, delete it and its image file
            remaining = Report.query.filter_by(item_id=item.item_id).count()
            if remaining == 0:
                # delete image file if exists
                if item.image_path:
                    img_path = os.path.join(app.root_path, item.image_path)
                    if os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                        except Exception:
                            pass
                db.session.delete(item)
            db.session.commit()
            flash('Report deleted', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error deleting report: ' + str(e), 'danger')
        return redirect(url_for('admin'))

    @app.route('/uploads/<path:filename>')
    def uploads(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app

if __name__ == '__main__':
    create_app().run(debug=True)
