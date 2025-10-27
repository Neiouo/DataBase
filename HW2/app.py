from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import mysql.connector
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ---------- Database connection ----------
def get_db_conn():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        port=os.getenv("MYSQL_PORT")
    )

# ---------- Home page ----------
@app.route('/')
def home():
    return render_template('index.html')

# ---------- USERS CRUD ----------
@app.route('/users')
def users():
    cnx = get_db_conn()
    cur = cnx.cursor(dictionary=True)
    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    cur.close(); cnx.close()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    cnx = get_db_conn()
    cur = cnx.cursor()
    cur.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
    cnx.commit()
    cur.close(); cnx.close()
    return redirect(url_for('users'))

@app.route('/users/delete/<int:user_id>')
def delete_user(user_id):
    cnx = get_db_conn()
    cur = cnx.cursor()
    cur.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
    cnx.commit()
    cur.close(); cnx.close()
    return redirect(url_for('users'))


# ---------- ACTIVITIES CRUD ----------
@app.route('/activities')
def activities():
    cnx = get_db_conn()
    cur = cnx.cursor(dictionary=True)
    cur.execute("SELECT * FROM activities")
    activities = cur.fetchall()
    cur.close(); cnx.close()
    return render_template('activities.html', activities=activities)

@app.route('/activities/add', methods=['POST'])
def add_activity():
    name = request.form['name']
    type_ = request.form['type']
    cnx = get_db_conn()
    cur = cnx.cursor()
    cur.execute("INSERT INTO activities (name, type) VALUES (%s, %s)", (name, type_))
    cnx.commit()
    cur.close(); cnx.close()
    return redirect(url_for('activities'))

@app.route('/activities/delete/<int:activity_id>')
def delete_activity(activity_id):
    cnx = get_db_conn()
    cur = cnx.cursor()
    cur.execute("DELETE FROM activities WHERE activity_id=%s", (activity_id,))
    cnx.commit()
    cur.close(); cnx.close()
    return redirect(url_for('activities'))


# ---------- RECORDS CRUD + JOIN ----------
@app.route('/records')
def records():
    cnx = get_db_conn()
    cur = cnx.cursor(dictionary=True)
    cur.execute("""
        SELECT r.record_id, u.name AS user_name, a.name AS activity_name,
               r.date, r.duration_minutes, r.distance_km
        FROM records r
        INNER JOIN users u ON r.user_id = u.user_id
        LEFT JOIN activities a ON r.activity_id = a.activity_id
        ORDER BY r.date DESC
    """)
    records = cur.fetchall()
    # Get user/activity lists for dropdowns
    cur.execute("SELECT user_id, name FROM users")
    users = cur.fetchall()
    cur.execute("SELECT activity_id, name FROM activities")
    activities = cur.fetchall()
    cur.close(); cnx.close()
    return render_template('records.html', records=records, users=users, activities=activities)

@app.route('/records/add', methods=['POST'])
def add_record():
    user_id = request.form['user_id']
    activity_id = request.form['activity_id']
    date = request.form['date']
    duration = request.form['duration_minutes']
    distance = request.form['distance_km']
    cnx = get_db_conn()
    cur = cnx.cursor()
    cur.execute("""
        INSERT INTO records (user_id, activity_id, date, duration_minutes, distance_km)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, activity_id, date, duration, distance))
    cnx.commit()
    cur.close(); cnx.close()
    return redirect(url_for('records'))

@app.route('/records/delete/<int:record_id>')
def delete_record(record_id):
    cnx = get_db_conn()
    cur = cnx.cursor()
    cur.execute("DELETE FROM records WHERE record_id=%s", (record_id,))
    cnx.commit()
    cur.close(); cnx.close()
    return redirect(url_for('records'))

if __name__ == '__main__':
    app.run(debug=True)
