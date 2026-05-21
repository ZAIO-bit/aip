from flask import Flask, request, jsonify, render_template_string
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

init_db()

# تصميم لوحة التحكم (HTML + CSS) تظهر بشكل متناسق على الموبايل
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZAIO PROTECTOR PANEL</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #fff; text-align: center; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: #1e1e1e; padding: 20px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1 { color: #00ff88; font-size: 24px; }
        .btn { background: #00ff88; color: #000; border: none; padding: 10px 20px; font-size: 16px; font-weight: bold; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; margin: 10px; }
        .btn-danger { background: #ff3333; color: #fff; padding: 5px 10px; font-size: 14px; }
        .btn-success { background: #33cc33; color: #fff; padding: 5px 10px; font-size: 14px; }
        table { width: 100%; margin-top: 20px; border-collapse: collapse; }
        th, td { padding: 12px; border-bottom: 1px solid #333; text-align: center; }
        th { background-color: #2a2a2a; color: #00ff88; }
        .status-active { color: #33cc33; font-weight: bold; }
        .status-expired { color: #ff3333; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ ZAIO PROTECTOR PANEL</h1>
        <p>إدارة مفاتيح التفعيل والاشتراكات المربوطة بالأداة</p>
        <a href="/panel/generate" class="btn">➕ توليد مفتاح جديد</a>
        
        <table>
            <tr>
                <th>المفتاح</th>
                <th>الحالة</th>
                <th>التحكم</th>
            </tr>
            {% for row in keys %}
            <tr>
                <td><code>{{ row[0] }}</code></td>
                <td>
                    {% if row[1] == 'active' %}
                        <span class="status-active">فعال</span>
                    {% else %}
                        <span class="status-expired">موقوف</span>
                    {% endif %}
                </td>
                <td>
                    {% if row[1] == 'active' %}
                        <a href="/panel/toggle/{{ row[0] }}/expired" class="btn btn-danger">إيقاف 🛑</a>
                    {% else %}
                        <a href="/panel/toggle/{{ row[0] }}/active" class="btn btn-success">تفعيل ✅</a>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
'''

# 1. مسار لوحة التحكم الرئيسي (الموقع المباشر)
@app.route('/', methods=['GET'])
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT key, status FROM license_keys ORDER BY rowid DESC")
    keys = cursor.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_HTML, keys=keys)

# 2. مسار التوليد من داخل اللوحة
@app.route('/panel/generate', methods=['GET'])
def panel_generate():
    new_key = "ZAIO-" + secrets.token_hex(6).upper()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO license_keys (key, status) VALUES (?, ?)", (new_key, 'active'))
    conn.commit()
    conn.close()
    # بعد التوليد، يرجع تلقائياً للوحة التحكم ليظهر المفتاح الجديد في الجدول
    return '<script>window.location.href="/";</script>'

# 3. مسار تغيير حالة المفتاح (إيقاف أو إعادة تفعيل) بنقرة زر
@app.route('/panel/toggle/<key_id>/<new_status>', methods=['GET'])
def toggle_key(key_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE license_keys SET status = ? WHERE key = ?", (new_status, key_id))
    conn.commit()
    conn.close()
    return '<script>window.location.href="/";</script>'

# 4. مسار فحص المفتاح (الذي تتصل به الأداة المشفرة)
@app.route('/check_key', methods=['POST'])
def check_key():
    data = request.json
    if not data or not data.get("key"):
        return jsonify({"status": "invalid"}), 400
        
    user_key = data.get("key")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM license_keys WHERE key = ?", (user_key,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] == 'active':
        return jsonify({"status": "valid"}), 200
    else:
        return jsonify({"status": "invalid"}), 403

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
