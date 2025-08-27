from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.environ.get('RENDER_DISK_PATH', '.'), 'orders.db')

# DB 초기화 함수는 이전과 동일
def init_db():
    # ... 이전 코드와 동일 ...

# --- 라우트(URL 규칙) 단순화 ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/view-orders.html')
def view_orders_page():
    return render_template('view-orders.html')

# API 엔드포인트들은 이전과 동일
@app.route('/api/create-order', methods=['POST'])
def create_order():
    # ... 이전 코드와 동일 ...

@app.route('/api/get-order/<user_id>', methods=['GET'])
def get_order(user_id):
    # ... 이전 코드와 동일 ...

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
