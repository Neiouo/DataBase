from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path = ".env")

PASSWORD = os.getenv("password")
print(PASSWORD)

app = Flask(__name__)

# MySQL 連線設定
db_config = {
    'host': 'localhost',          # MySQL 主機
    'user': 'root',               # MySQL 帳號
    'password': f'{PASSWORD}',    # MySQL 密碼
    'database': 'database',        # 資料庫名稱
}

def get_db_connection():
    """建立資料庫連線"""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print("資料庫連線錯誤：", e)
        return None

# 前端首頁
@app.route('/')
def index():
    return render_template('index.html')

# API：新增員工
@app.route('/add_employee', methods=['POST'])
def add_employee():
    try:
        data = request.get_json()
        employee_ID = data.get('employee_ID')
        employee_name = data.get('employee_name')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        # 驗證欄位完整性
        if not all([employee_ID, employee_name, first_name, last_name]):
            return jsonify({"error": "請完整填寫所有欄位"}), 400

        conn = get_db_connection()
        if conn is None:
            return jsonify({"error": "無法連線至資料庫"}), 500

        cursor = conn.cursor()

        # 插入 SQL
        insert_query = """
        INSERT INTO employee (employee_ID, employee_name, first_name, last_name)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (employee_ID, employee_name, first_name, last_name))
        conn.commit()

        return jsonify({"message": f"員工 {employee_name} (ID: {employee_ID}) 新增成功！"}), 200

    except mysql.connector.IntegrityError:
        return jsonify({"error": "此 employee_ID 已存在，請使用其他 ID"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)