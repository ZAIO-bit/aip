from flask import Flask, request, jsonify, render_template_string
import sqlite3
import secrets
import os

app = Flask(__name__)
DB_NAME = "keys_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # الجدول المطور يدعم: اسم الملف، نوع المفتاح، والـ HWID المقفل للمدفوع
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS license_keys (
            key TEXT PRIMARY KEY,
            file_name TEXT,
            key_type TEXT,
            status TEXT DEFAULT 'active',
            hwid TEXT DEFAULT ''
        )
    ''''')
    conn.commit()
    conn.close()

init_db()

# تصميم لوحة التحكم الاحترافية
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZAIO SMART PROTECTOR</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #0f0f12; color: #e0e0e6; text-align: center; padding: 10px; margin: 0; }
        .container { max-width: 900px; margin: 20px auto; background: #17171f; padding: 25px; border-radius: 12px; box-shadow: 0 4px 25px rgba(0,0,0,0.6); border: 1px solid #232330; }
        h1 { color: #00ff88; font-size: 26px; margin-bottom: 5px; }
        .subtitle { color: #8a8a9e; font-size: 14px; margin-bottom: 25px; }
        .gen-box { background: #1f1f2e; padding: 15px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #2d2d3f; }
        select, input { background: #13131a; color: #fff; border: 1px solid #3d3d5c; padding: 8px 12px; border-radius: 5px; margin: 5px; font-size: 14px; }
        .btn { background: #00ff88; color: #000; border: none; padding: 9px 18px; font-size: 14px; font-weight: bold; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-danger { background: #ff3355; color: #fff; }
        .btn-success { background: #00cc66; color: #fff; }
        .btn-delete { background: #444; color: #ff5555; border: 1px solid #ff3355; padding: 4px 8px; font-size: 12px; }
        table { width: 100%; margin-top: 20px; border-collapse: collapse; font-size: 14px; }
        th, td { padding: 12px; border-bottom: 1px solid #232330; text-align: center; }
        th { background-color: #1f1f2e; color: #00ff88; }
        code { background: #111; padding: 4px 8px; border-radius: 4px; color: #ffb86c; font-family: monospace; }
        .status-active { color: #00ff88; font-weight: bold; }
        .status-expired { color: #ff3355; font-weight: bold; }
        .badge { padding: 3px 7px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .badge-paid { background: #ffaa00; color: #000; }
        .badge-free { background: #00bfff; color: #000; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ ZAIO SMART SYSTEM</h1>
        <div class="subtitle">نظام المفاتيح المدفوعة (قفل HWID) والمجانية التلقائي</div>
        
        <div class="gen-box">
            <form action="/panel/generate" method="GET">
                <input type="text" name="file_name" placeholder="اسم الملف المتصل" required style="width: 200px;">
                <select name="key_type" required>
                    <option value="paid">🔑 مفتاح مدفوع (لأول شخص فقط)</option>
                    <option value="free">🎁 مفتاح مجاني (عام للجميع)</option>
                </select>
                <button type="submit" class="btn">➕ توليد كود مخصص</button>
            </form>
        </div>
        
        <table>
            <tr>
                <th>المفتاح / الكود</th>
                <th>اسم الملف</th>
                <th>نوع الاشتراك</th>
                <th>جهاز العميل (HWID)</th>
                <th>الحالة</th>
                <th>التحكم</th>
            </tr>
            {% for row in keys %}
            <tr>
                <td><code>{{ row[0] }}</code></td>
                <td><b style="color: #fff;">{{ row[1] }}</b></td>
                <td>
                    {% if row[2] == 'paid' %}
                        <span class="badge badge-paid">مدفوع</span>
                    {% else %}
                        <span class="badge badge-free">مجاني</span>
                    {% endif %}
                </td>
                <td><span style="color: #aaa; font-size: 12px;">{{ row[4] if row[4] else 'لم يتم الربط بعد' }}</span></td>
                <td>
                    {% if row[3] == 'active' %}
                        <span class="status-active">شغال ✅</span>
                    {% else %}
                        <span class="status-expired">موقف 🛑</span>
                    {% endif %}
                </td>
                <td>
                    {% if row[3] == 'active' %}
                        <a href="/panel/toggle/{{ row[0] }}/expired" class="btn btn-danger" style="padding: 4px 8px; font-size: 12px;">إيقاف</a>
                    {% else %}
                        <a href="/panel/toggle/{{ row[0] }}/active" class="btn btn-success" style="padding: 4px 8px; font-size: 12px;">تفعيل</a>
                    {% endif %}
                    <a href="/panel/delete/{{ row[0] }}" class="btn btn-delete" onclick="return confirm('حذف نهائي؟')">حذف 🗑️</a>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT key, file_name, key_type, status, hwid FROM license_keys ORDER BY rowid DESC")
    keys = cursor.fetchall()
    conn.close()
    return render_template_string(DASHBOARD_HTML, keys=keys)

@app.route('/panel/generate', methods=['GET'])
def panel_generate():
    file_name = request.args.get('file_name', 'Unknown_File')
    key_type = request.args.get('key_type', 'paid')
    new_key = "ZAIO-" + secrets.token_hex(4).upper()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO license_keys (key, file_name, key_type, status, hwid) VALUES (?, ?, ?, ?, '')", (new_key, file_name, key_type, 'active'))
    conn.commit()
    conn.close()
    return '<script>window.location.href="/";</script>'

@app.route('/panel/toggle/<key_id>/<new_status>', methods=['GET'])
def toggle_key(key_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE license_keys SET status = ? WHERE key = ?", (new_status, key_id))
    conn.commit()
    conn.close()
    return '<script>window.location.href="/";</script>'

@app.route('/panel/delete/<key_id>', methods=['GET'])
def delete_key(key_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM license_keys WHERE key = ?", (key_id,))
    conn.commit()
    conn.close()
    return '<script>window.location.href="/";</script>'

# مسار الفحص السريع والذكي جداً للأدوات
@app.route('/check_key', methods=['POST'])
def check_key():
    data = request.json
    if not data:
        return jsonify({"status": "disabled"}), 400
        
    user_hwid = data.get("hwid")
    current_key = data.get("key")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT key_type, status, hwid FROM license_keys WHERE key = ?", (current_key,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return jsonify({"status": "disabled"}), 404

    key_type, status, db_hwid = result

    # 1. التحقق أولاً إذا كان المفتاح موقوفاً من اللوحة
    if status != 'active':
        conn.close()
        return jsonify({"status": "disabled"}), 403

    # 2. إذا كان المفتاح مدفوعاً، نقوم بقفله على أول جهاز يدخل
    if key_type == 'paid':
        if db_hwid == '':
            # تسجيل جهاز العميل الأول وقفل المفتاح عليه
            cursor.execute("UPDATE license_keys SET hwid = ? WHERE key = ?", (user_hwid, current_key))
            conn.commit()
            conn.close()
            return jsonify({"status": "granted"}), 200
        elif db_hwid != user_hwid:
            # إذا حاول جهاز آخر الدخول بنفس المفتاح المدفوع
            conn.close()
            return jsonify({"status": "wrong_device"}), 403

    # 3. إذا كان مجانياً أو مدفوعاً والجهاز مطابق
    conn.close()
    return jsonify({"status": "granted"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
