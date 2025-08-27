from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2 # PostgreSQL 데이터베이스 라이브러리
import json
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Render 환경 변수에 저장된 데이터베이스 URL을 가져옵니다.
DATABASE_URL = os.environ.get('DATABASE_URL')

# --- 데이터베이스 테이블 초기화 함수 ---
def init_db():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        # 사용자 ID를 기본 키로 하는 테이블 생성 (JSONB 타입 사용)
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

# --- 라우트(URL 규칙) ---
# 기본 경로로 접속하면 index.html 파일을 보여줍니다.
@app.route('/')
def home():
    return render_template('index.html')

# --- API 엔드포인트: 주문 정보 생성/업데이트 ---
@app.route('/api/create-order', methods=['POST'])
def create_order():
    data = request.get_json()
    if not data or 'userId' not in data or 'cart' not in data:
        return jsonify({'success': False, 'message': '잘못된 데이터 형식입니다.'}), 400

    user_id = data['userId']
    # 주문 내역 전체를 JSON 문자열로 변환하여 저장
    order_data_str = json.dumps(data)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        # 동일한 user_id가 있으면 덮어쓰기(UPDATE), 없으면 새로 추가(INSERT)
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

# --- API 엔드포인트: 특정 사용자의 주문 정보 조회 ---
@app.route('/api/get-order/<user_id>', methods=['GET'])
def get_order(user_id):
    conn = None
    try:
        conn = psycopg2.connect(postgresql://neondb_owner:npg_G1D7eNAakmvC@ep-gentle-flower-a1xl0dan-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require)
        cursor = conn.cursor()
        cursor.execute('SELECT order_data FROM orders WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        if result:
            # result[0]은 DB에 저장된 order_data (JSONB 타입)
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
    # host='0.0.0.0'은 Render 같은 클라우드 환경에서 필요합니다.
    app.run(host='0.0.0.0', port=5000, debug=True)


