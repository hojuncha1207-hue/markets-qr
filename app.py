from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
import json
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL')

def init_db():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                user_id TEXT PRIMARY KEY,
                order_data JSONB NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Database init error: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/view-orders.html')
def view_orders_page():
    return render_template('view-orders.html')

@app.route('/api/create-order', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or 'userId' not in data or 'cart' not in data:
        return jsonify({'success': False, 'message': '잘못된 데이터 형식입니다.'}), 400

    user_id = data['userId']
    order_data_str = json.dumps(data)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, order_data) VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE SET order_data = EXCLUDED.order_data, timestamp = NOW()
        ''', (user_id, order_data_str))
        conn.commit()
        return jsonify({'success': True, 'message': f'{user_id}의 주문이 저장되었습니다.'}), 201
    except Exception as e:
        print(f"Create order error: {e}")
        return jsonify({'success': False, 'message': '서버 오류 발생'}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/api/get-order/<user_id>', methods=['GET'])
def get_order(user_id):
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT order_data FROM orders WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        if result:
            return jsonify({'success': True, 'order': result[0]}), 200
        else:
            return jsonify({'success': False, 'message': '주문 정보를 찾을 수 없습니다.'}), 404
    except Exception as e:
        print(f"Get order error: {e}")
        return jsonify({'success': False, 'message': '서버 오류 발생'}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
