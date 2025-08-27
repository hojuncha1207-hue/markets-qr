from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import psycopg2
import json
import os

# Flask 앱을 생성하고 templates 폴더를 지정합니다.
app = Flask(__name__, template_folder='templates')
CORS(app)

# Render의 환경 변수에 저장된 데이터베이스 URL을 안전하게 가져옵니다.
DATABASE_URL = os.environ.get('DATABASE_URL')

# --- 데이터베이스 테이블 초기화 함수 ---
# 서버가 처음 시작될 때 'orders'라는 테이블이 없으면 자동으로 만들어줍니다.
def init_db():
    conn = None
    try:
        # 환경 변수를 사용하여 데이터베이스에 연결합니다.
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
        # 서버 로그에 에러를 출력합니다.
        print(f"Database initialization error: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

# --- 페이지를 보여주는 라우트(URL 규칙) ---
@app.route('/')
def home():
    """기본 경로로 접속 시 index.html 파일을 보여줍니다."""
    return render_template('index.html')

@app.route('/view-orders.html')
def view_orders_page():
    """/view-orders.html 경로로 접속 시 view-orders.html 파일을 보여줍니다."""
    return render_template('view-orders.html')

# --- API 엔드포인트: 주문 정보 생성/업데이트 ---
@app.route('/api/create-order', methods=['POST'])
def create_order():
    """프론트엔드로부터 주문 정보를 받아 DB에 저장합니다."""
    data = request.get_json()
    if not data or 'userId' not in data or 'cart' not in data:
        return jsonify({'success': False, 'message': '잘못된 데이터 형식입니다.'}), 400

    user_id = data['userId']
    # 주문 내역 전체를 JSON 형식으로 변환하여 저장합니다.
    order_data_str = json.dumps(data)
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        # 동일한 user_id가 있으면 덮어쓰고(UPDATE), 없으면 새로 추가(INSERT)합니다.
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
    """URL에 포함된 user_id로 DB에서 주문 정보를 조회합니다."""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT order_data FROM orders WHERE user_id = %s', (user_id,))
        result = cursor.fetchone()
        if result:
            # result[0]은 DB에 저장된 주문 데이터(JSONB 타입)입니다.
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

# --- 서버 실행 ---
if __name__ == '__main__':
    init_db() # 서버 시작 시 DB 테이블이 있는지 확인/생성
    # host='0.0.0.0'은 Render 같은 클라우드 환경에서 필요합니다.
    # debug=False는 실제 서비스 환경에서의 표준 설정입니다.
    app.run(host='0.0.0.0', port=5000, debug=False)
