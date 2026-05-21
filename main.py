from flask import Flask, request, jsonify
import sqlite3
import secrets
import os

app = Flask(__name__)
DB_NAME = "keys_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS license_keys (
            key TEXT PRIMARY KEY,
            status TEXT DEFAULT 'active'
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/generate_key', methods=['GET'])
def generate_key():
    new_key = "ZAIO-" + secrets.token_hex(6).upper()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO license_keys (key, status) VALUES (?, ?)", (new_key, 'active'))
        conn.commit()
        return jsonify({"status": "success", "key": new_key}), 200
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Key already exists"}), 400
    finally:
        conn.close()

@app.route('/check_key', methods=['POST'])
def check_key():
    data = request.json
    user_key = data.get("key")
    if not user_key:
        return jsonify({"status": "invalid", "message": "No key provided"}), 400

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM license_keys WHERE key = ?", (user_key,))
    result = cursor.fetchone()
    conn.close()

    if result:
        if result[0] == 'active':
            return jsonify({"status": "valid", "message": "Key is active!"}), 200
        else:
            return jsonify({"status": "expired", "message": "Key has been used"}), 403
    else:
        return jsonify({"status": "invalid", "message": "Key not found"}), 404

if __name__ == '__main__':
    init_db()
    # Railway يعطي بورت ديناميكي تلقائياً عبر متغيرات البيئة، لذلك نستخدم os.environ
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
