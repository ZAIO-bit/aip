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
            file_name TEXT,
            key_type TEXT,
            status TEXT DEFAULT 'active',
            hwid TEXT DEFAULT ''
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# تصميم لوحة التحكم المطور (أزرار كبيرة، ألوان متناسقة، وميزة النسخ التلقائي)
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ZAIO SMART PROTECTOR</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0b0b0e; color: #e2e2e9; text-align: center; padding: 10px; margin: 0; }
        .container { max-width: 950px; margin: 15px auto; background: #13131a; padding: 20px; border-radius: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); border: 1px solid #222230; }
        h1 { color: #00ff88; font-size: 24px; margin-bottom: 5px; font-weight: bold; }
        .subtitle { color: #79798c; font-size: 13px; margin-bottom: 20px; }
        
        /* صندوق التوليد */
        .gen-box { background: #1c1c27; padding: 15px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #2b2b3d; }
        select, input { background: #0b0b0e; color: #fff; border: 1px solid #3a3a52; padding: 12px; border-radius: 8px; margin: 6px; font-size: 14px; width: 90%; max-width: 240px; box-sizing: border-box; }
        
        /* الأزرار الرئيسية المحدثة كـ جرافيكس متناسق */
        .btn { background: #00ff88; color: #0b0b0e; border: none; padding: 12px 24px; font-size: 15px; font-weight: bold; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; transition: 0.2s; }
        .btn:active { transform: scale(0.95); }
        
        /* أزرار التحكم داخل الجدول (كبيرة ومريحة للموبايل) */
        .action-btn { display: inline-flex; align-items: center; justify-content: center; padding: 10px 16px; font-size: 13px; font-weight: bold; border-radius: 8px; text-decoration: none; margin: 4px; min-width: 80px; transition: 0.2s; border: none; cursor: pointer; }
        .action-btn:active { transform: scale(0.92); }
        
        .btn-toggle-off { background-color: #ff3355; color: #fff; }
        .btn-toggle-on { background-color: #00cc66; color: #fff; }
        .btn-delete { background-color: #242433; color: #ff5555; border: 1px solid #ff3355; }
        
        /* التنسيق البرمجي والجدول */
        .table-wrapper { overflow-x: auto; margin-top: 15px; border-radius: 12px; border: 1px solid #222230; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; background: #181824; }
        th, td { padding: 14px; border-bottom: 1px solid #222230; text-align: center; white-space: nowrap; }
        th { background-color: #1c1c27; color: #00ff88; font-weight: 600; }
        
        /* كود منسق وقابل للنسخ */
        .copy-code { background: #0b0b0e; padding: 8px 12px; border-radius: 6px; color: #ffb86c; font-family: monospace; font-size: 13px; border: 1px solid #2b2b3d; cursor: pointer; display: inline-block; position: relative; }
        .copy-code:hover { background: #1c1c27; }
        .copy-code::after { content: "اضغط للنسخ 📋"; position: absolute; bottom: -20px; left: 50%; transform: translateX(-50%); font-size: 10px; color: #8a8a9e; visibility: hidden; opacity: 0; transition: 0.2s; }
        .copy-code:hover::after { visibility: visible; opacity: 1; }
        
        .status-active { color: #00ff88; font-weight: bold; }
        .status-expired { color: #ff3355; font-weight: bold; }
        .badge { padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; }
        .badge-paid { background: rgba(255, 170, 0, 0.15); color: #ffaa00; border: 1px solid #ffaa00; }
        .badge-free { background: rgba(0, 191, 255, 0.15); color: #00bfff; border: 1px solid #00bfff; }
        
        /* إشعار منبثق عند النسخ تلقائياً */
        #toast { visibility: hidden; min-width: 200px; background-color: #00ff88; color: #000; text-align: center; padding: 12px; position: fixed; z-index: 1000; left: 50%; bottom: 30px; transform: translateX(-50%); border-radius: 8px; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        #toast.show { visibility: visible; animation: fadein 0.5s, fadeout 0.5s 2.5s; }
        @keyframes fadein { from { bottom: 0; opacity: 0; } to { bottom: 30px; opacity: 1; } }
        @keyframes fadeout { from { bottom: 30px; opacity: 1; } to { bottom: 0; opacity: 0; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ ZAIO SMART SYSTEM</h1>
        <div class="subtitle">نظام التحكم بالمفاتيح بنقرة واحدة والفحص الصامت التلقائي</div>
        
        <div class="gen-box">
            <form action="/panel/generate" method="GET">
                <input type="text" name="file_name" placeholder="اسم الملف المتصل" required>
                <select name="key_type" required>
                    <option value="paid">🔑 مفتاح مدفوع (جهاز واحد)</option>
                    <option value="free">🎁 مفتاح مجاني (عام للجميع)</option>
                </select>
                <br>
                <button type="submit" class="btn" style="margin-top: 10px;">➕ توليد كود مخصص</button>
            </form>
        </div>
        
        <div class="table-wrapper">
            <table>
                <tr>
                    <th>المفتاح (اضغط للنسخ)</th>
                    <th>اسم الملف</th>
                    <th>نوع الاشتراك</th>
                    <th>جهاز العميل (HWID)</th>
                    <th>الحالة</th>
                    <th>التحكم بالأداة</th>
                </tr>
                {% for row in keys %}
                <tr>
                    <td><div class="copy-code" onclick="copyKey('{{ row[0] }}')">{{ row[0] }}</div></td>
                    <td><b style="color: #fff;">{{ row[1] }}</b></td>
                    <td>
                        {% if row[2] == 'paid' %}
                            <span class="badge badge-paid">مدفوع</span>
                        {% else %}
                            <span class="badge badge-free">مجاني</span>
                        {% endif %}
                    </td>
                    <td><span style="color: #8a8a9e; font-size: 12px;">{{ row[4] if row[4] else 'لم يربط بعد' }}</span></td>
                    <td>
                        {% if row[3] == 'active' %}
                            <span class="status-active">شغال ✅</span>
                        {% else %}
                            <span class="status-expired">موقف 🛑</span>
                        {% endif %}
                    </td>
                    <td>
                        {% if row[3] == 'active' %}
                            <a href="/panel/toggle/{{ row[0] }}/expired" class="action-btn btn-toggle-off">إيقاف</a>
                        {% else %}
                            <a href="/panel/toggle/{{ row[0] }}/active" class="action-btn btn-toggle-on">تفعيل</a>
                        {% endif %}
                        <a href="/panel/delete/{{ row[0] }}" class="action-btn btn-delete" onclick="return confirm('هل أنت متأكد من حذف الكود نهائياً؟')">حذف 🗑️</a>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>

    <div id="toast">تم نسخ المفتاح بنجاح! 📋</div>

    <script>
        function copyKey(text) {
            navigator.clipboard.writeText(text).then(function() {
                var toast = document.getElementById("toast");
                toast.className = "show";
                setTimeout(function(){ toast.className = toast.className.replace("show", ""); }, 3000);
            });
        }
    </script>
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

    if status != 'active':
        conn.close()
        return jsonify({"status": "disabled"}), 403

    if key_type == 'paid':
        if db_hwid == '':
            cursor.execute("UPDATE license_keys SET hwid = ? WHERE key = ?", (user_hwid, current_key))
            conn.commit()
            conn.close()
            return jsonify({"status": "granted"}), 200
        elif db_hwid != user_hwid:
            conn.close()
            return jsonify({"status": "wrong_device"}), 403

    conn.close()
    return jsonify({"status": "granted"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
