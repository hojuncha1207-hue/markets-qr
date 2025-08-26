# --- 1. 필요한 라이브러리 불러오기 ---
# render_template: HTML 파일을 불러와 사용자에게 보여주는 기능
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS # 다른 주소에서의 요청을 허용하기 위한 라이브러리
import sqlite3
import json

# --- 2. Flask 앱 생성 및 기본 설정 ---
app = Flask(__name__)
CORS(app) # CORS 설정: 모든 외부 요청을 허용 (테스트 및 배포에 필요)

DB_NAME = "orders.db" # 데이터베이스 파일 이름

# --- 3. 데이터베이스 초기화 함수 ---
# 서버가 처음 시작될 때 'orders'라는 테이블이 없으면 자동으로 만들어줍니다.
def init_db():
    conn = sqlite3.connect(DB_NAME)
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

# --- 4. 라우트(URL 규칙) 정의 ---

# ⭐️⭐️⭐️ 새로 추가된 핵심 부분 ⭐️⭐️⭐️
# 기본 주소 ('https://내사이트주소.com/')로 접속했을 때의 처리
@app.route('/')
def home():
    # 'templates' 폴더 안에 있는 'index.html' 파일을 찾아서 사용자에게 보여줍니다.
    return render_template('index.html')

# API 엔드포인트: 프론트엔드로부터 주문 정보를 받아 DB에 저장
@app.route('/api/create-order', methods=['POST'])
def create_order():
    # 1. 프론트엔드에서 보낸 JSON 데이터 받기
    data = request.get_json()

    # 2. 데이터 유효성 검사
    if not data or 'userId' not in data or 'items' not in data:
        return jsonify({'success': False, 'message': '잘못된 데이터 형식입니다.'}), 400

    user_id = data['userId']
    # 주문 내역 전체를 JSON 문자열로 변환하여 저장 (나중에 확장하기 용이)
    order_data_str = json.dumps(data)

    # 3. 데이터베이스에 저장
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # 동일한 user_id가 있으면 덮어쓰기(UPDATE), 없으면 새로 추가(INSERT)
        cursor.execute('''
            INSERT INTO orders (user_id, order_data) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET order_data=excluded.order_data, timestamp=CURRENT_TIMESTAMP
        ''', (user_id, order_data_str))
        conn.commit()
        conn.close()
        # 4. 성공 응답 보내기
        return jsonify({'success': True, 'message': f'{user_id}의 주문이 저장되었습니다.'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': '서버 오류 발생', 'error': str(e)}), 500

# --- 5. 서버 실행 ---
if __name__ == '__main__':
    init_db() # 서버 시작 시 DB 테이블이 있는지 확인/생성
    # host='0.0.0.0'은 Render 같은 클라우드 환경에서 필요합니다.

    app.run(host='0.0.0.0', port=5000, debug=True)
# --- API 엔드포인트: 특정 사용자의 최신 주문 정보 조회 ---
@app.route('/api/get-order/<user_id>', methods=['GET'])
def get_order(user_id):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 해당 user_id를 가진 가장 최근의 주문 1개를 찾습니다.
        cursor.execute('''
            SELECT order_data FROM orders 
            WHERE user_id = ? 
            ORDER BY timestamp DESC LIMIT 1
        ''', (user_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            # 저장된 데이터는 JSON 문자열이므로, 파이썬 딕셔너리로 변환하여 반환합니다.
            order_data = json.loads(result[0])
            return jsonify({'success': True, 'order': order_data}), 200
        else:
            return jsonify({'success': False, 'message': '주문 정보를 찾을 수 없습니다.'}), 404

    except Exception as e:
        return jsonify({'success': False, 'message': '서버 오류 발생', 'error': str(e)}), 500
