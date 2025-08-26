from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.environ.get('RENDER_DISK_PATH', '.'), 'orders.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            user_id TEXT PRIMARY KEY,
            order_data TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- 리다이렉트(중간 다리) 규칙 ---
@app.route('/launch/order')
def launch_order():
    return redirect(f"/user/{{user_id}}")

# ⭐️ 수정된 부분
@app.route('/launch/view-orders')
def launch_view_orders():
    return redirect(f"/view-orders/user/{{user_id}}")

# --- 최종 목적지 규칙 ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/user/<user_id>')
def home_with_user_id(user_id):
    return render_template('index.html')

# ⭐️ 수정된 부분
@app.route('/view-orders.html')
def view_orders_page():
    return render_template('view-orders.html')

# ⭐️ 수정된 부분
@app.route('/view-orders/user/<user_id>')
def view_orders_with_user_id(user_id):
    return render_template('view-orders.html')

# --- API 엔드포인트 ---
@app.route('/api/create-order', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or 'userId' not in data or 'items' not in data:
        return jsonify({'success': False, 'message': '잘못된 데이터 형식입니다.'}), 400
    user_id = data['userId']
    order_data_str = json.dumps(data)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, order_data) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET order_data=excluded.order_data, timestamp=CURRENT_TIMESTAMP
        ''', (user_id, order_data_str))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'{user_id}의 주문이 저장되었습니다.'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': '서버 오류 발생', 'error': str(e)}), 500

@app.route('/api/get-order/<user_id>', methods=['GET'])
def get_order(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT order_data FROM orders 
            WHERE user_id = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            order_data = json.loads(result[0])
            return jsonify({'success': True, 'order': order_data}), 200
        else:
            return jsonify({'success': False, 'message': '주문 정보를 찾을 수 없습니다.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': '서버 오류 발생', 'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
