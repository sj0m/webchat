from flask import Flask, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from Crypto.Cipher import AES
import base64
import os

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['UPLOAD_FOLDER'] = 'uploads'

# إنشاء مجلد uploads إذا لم يكن موجوداً
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# مفتاح التشفير (يجب أن يكون ثابتًا حتى يعمل التشفير وفك التشفير بشكل صحيح)
encryption_key = b'0123456789abcdef'  # مفتاح 16 بايت (128 بت)

def encrypt_message(message):
    cipher = AES.new(encryption_key, AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def decrypt_message(encrypted_message):
    try:
        decoded = base64.b64decode(encrypted_message)
        nonce = decoded[:16]  # النونس (Nonce) هو أول 16 بايت
        ciphertext = decoded[16:]  # باقي البيانات هي النص المشفر
        cipher = AES.new(encryption_key, AES.MODE_EAX, nonce=nonce)
        return cipher.decrypt(ciphertext).decode('utf-8')
    except Exception as e:
        print(f"فك التشفير فشل: {e}")
        return 'رسالة غير قابلة للفك'

# تحميل بيانات المستخدمين من الملف
def load_users():
    users_file_path = os.path.join(os.getcwd(), 'users.txt')
    print(f"مسار ملف users.txt: {users_file_path}")
    if not os.path.exists(users_file_path):
        print("ملف users.txt غير موجود، سيتم إنشاؤه تلقائيًا.")
        with open(users_file_path, 'w') as file:
            file.write('')  # إنشاء ملف فارغ
    users = {}
    try:
        with open(users_file_path, 'r') as file:
            for line in file:
                parts = line.strip().split(':', 1)
                if len(parts) == 2:
                    username, password_hash = parts
                    users[username] = password_hash
    except Exception as e:
        print(f"حدث خطأ أثناء قراءة ملف users.txt: {e}")
    return users

# حفظ بيانات المستخدمين إلى الملف
def save_users(users):
    users_file_path = os.path.join(os.getcwd(), 'users.txt')
    print(f"مسار ملف users.txt: {users_file_path}")
    try:
        with open(users_file_path, 'w') as file:
            for username, password_hash in users.items():
                file.write(f"{username}:{password_hash}\n")
        print("تم حفظ بيانات المستخدمين بنجاح.")
    except Exception as e:
        print(f"حدث خطأ أثناء حفظ بيانات المستخدمين: {e}")

# صفحة تسجيل الدخول
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return '<h3 style="text-align: center; color: red;">خطأ بتسجيل الدخول، تأكد من البيانات</h3>'
    return '''
        <html>
            <head>
                <title>تسجيل الدخول</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #f0f2f5;
                        margin: 0;
                        padding: 0;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                    }
                    .login-container {
                        background-color: #ffffff;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        width: 100%;
                        max-width: 400px;
                        text-align: center;
                    }
                    .login-container h2 {
                        margin-bottom: 20px;
                        color: #333;
                    }
                    .login-container input[type="text"],
                    .login-container input[type="password"] {
                        width: 100%;
                        padding: 10px;
                        margin: 10px 0;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        font-size: 16px;
                    }
                    .login-container button {
                        width: 100%;
                        padding: 10px;
                        background-color: #075e54;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 16px;
                        cursor: pointer;
                        margin-top: 10px;
                    }
                    .login-container button:hover {
                        background-color: #128c7e;
                    }
                    .login-container a {
                        display: block;
                        margin-top: 20px;
                        color: #075e54;
                        text-decoration: none;
                        font-size: 14px;
                    }
                    .login-container a:hover {
                        text-decoration: underline;
                    }
                </style>
            </head>
            <body>
                <div class="login-container">
                    <h2>تسجيل الدخول</h2>
                    <form method="post">
                        <input type="text" name="username" placeholder="اسم المستخدم" required>
                        <input type="password" name="password" placeholder="كلمة المرور" required>
                        <button type="submit">دخول</button>
                    </form>
                    <a href="/signup">إنشاء حساب جديد</a>
                </div>
            </body>
        </html>
    '''

# صفحة التسجيل
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return '<h3 style="text-align: center; color: red;">اسم المستخدم وكلمة المرور مطلوبان!</h3>'

        users = load_users()
        if username in users:
            return '<h3 style="text-align: center; color: red;">اسم المستخدم هذا موجود مسبقاً!</h3>'

        # توليد التجزئة لكلمة المرور
        password_hash = generate_password_hash(password)
        users[username] = password_hash
        save_users(users)
        return redirect(url_for('login'))

    return '''
        <html>
            <head>
                <title>التسجيل</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #f0f2f5;
                        margin: 0;
                        padding: 0;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                    }
                    .signup-container {
                        background-color: #ffffff;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        width: 100%;
                        max-width: 400px;
                        text-align: center;
                    }
                    .signup-container h2 {
                        margin-bottom: 20px;
                        color: #333;
                    }
                    .signup-container input[type="text"],
                    .signup-container input[type="password"] {
                        width: 100%;
                        padding: 10px;
                        margin: 10px 0;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        font-size: 16px;
                    }
                    .signup-container button {
                        width: 100%;
                        padding: 10px;
                        background-color: #075e54;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 16px;
                        cursor: pointer;
                        margin-top: 10px;
                    }
                    .signup-container button:hover {
                        background-color: #128c7e;
                    }
                    .signup-container a {
                        display: block;
                        margin-top: 20px;
                        color: #075e54;
                        text-decoration: none;
                        font-size: 14px;
                    }
                    .signup-container a:hover {
                        text-decoration: underline;
                    }
                </style>
            </head>
            <body>
                <div class="signup-container">
                    <h2>إنشاء حساب جديد</h2>
                    <form method="post">
                        <input type="text" name="username" placeholder="اسم المستخدم" required>
                        <input type="password" name="password" placeholder="كلمة المرور" required>
                        <button type="submit">تسجيل</button>
                    </form>
                    <a href="/">عودة لتسجيل الدخول</a>
                </div>
            </body>
        </html>
    '''

# صفحة الدردشة
@app.route('/chat', methods=['GET'])
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))

    return f'''
        <html>
            <head>
                <title>دردشة</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #ece5dd;
                        margin: 0;
                        padding: 0;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                    }}
                    .chat-container {{
                        width: 100%;
                        max-width: 600px;
                        height: 100vh;
                        background-color: #fff;
                        display: flex;
                        flex-direction: column;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        border-radius: 10px;
                        overflow: hidden;
                    }}
                    .header {{
                        background-color: #075e54;
                        color: white;
                        padding: 10px;
                        text-align: center;
                        font-size: 18px;
                        flex-shrink: 0;
                    }}
                    .messages {{
                        flex-grow: 1;
                        overflow-y: auto;
                        padding: 10px;
                        background-color: #ece5dd;
                    }}
                    .message {{
                        padding: 8px 12px;
                        border-radius: 7.5px;
                        margin: 5px 0;
                        max-width: 70%;
                        word-wrap: break-word;
                    }}
                    .message.sent {{
                        background-color: #dcf8c6;
                        align-self: flex-end;
                        margin-left: auto;
                    }}
                    .message.received {{
                        background-color: #ffffff;
                        align-self: flex-start;
                        margin-right: auto;
                    }}
                    .message .username {{
                        font-weight: bold;
                        color: #075e54;
                    }}
                    .message .timestamp {{
                        font-size: 12px;
                        color: #666;
                        margin-left: 10px;
                    }}
                    .message img {{
                        max-width: 100%;
                        border-radius: 10px;
                        margin-top: 5px;
                    }}
                    .input-container {{
                        display: flex;
                        padding: 10px;
                        background-color: #f0f0f0;
                        flex-shrink: 0;
                    }}
                    input[type="text"] {{
                        flex-grow: 1;
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 20px;
                        outline: none;
                    }}
                    input[type="file"] {{
                        display: none;
                    }}
                    .file-upload {{
                        padding: 10px 20px;
                        border: none;
                        background-color: #075e54;
                        color: white;
                        border-radius: 20px;
                        margin-left: 10px;
                        cursor: pointer;
                    }}
                    button {{
                        padding: 10px 20px;
                        border: none;
                        background-color: #075e54;
                        color: white;
                        border-radius: 20px;
                        margin-left: 10px;
                        cursor: pointer;
                    }}
                    button:hover, .file-upload:hover {{
                        background-color: #128c7e;
                    }}
                </style>
            </head>
            <body>
                <div class="chat-container">
                    <div class="header">
                        <h2>مرحباً <b>{session["username"]}</b></h2>
                        <a href="/logout" style="color: white; text-decoration: none;">تسجيل الخروج</a>
                    </div>
                    <div class="messages" id="chat-box"></div>
                    <div class="input-container">
                        <form method="post" action="/send" enctype="multipart/form-data">
                            <input type="text" name="message" placeholder="اكتب رسالة">
                            <label for="file-upload" class="file-upload">
      🅾
     </label>
                            <input id="file-upload" type="file" name="image" accept="image/*">
                            <button type="submit">إرسال</button>
                        </form>
                    </div>
                </div>
                <script>
                    function loadMessages() {{
                        fetch('/messages')
                        .then(response => response.json())
                        .then(data => {{
                            const chatBox = document.getElementById('chat-box');
                            chatBox.innerHTML = '';
                            data.forEach(msg => {{
                                const messageClass = msg.username === '{session["username"]}' ? 'sent' : 'received';
                                const imageContent = msg.image ? `<img src="/uploads/${{msg.image}}" alt="صورة">` : '';
                                chatBox.innerHTML += `
                                    <div class="message ${{messageClass}}">
                                        <span class="username">${{msg.username}}</span> (${{msg.timestamp}}): ${{msg.message}}
                                        ${{imageContent}}
                                    </div>
                                `;
                            }});
                            chatBox.scrollTop = chatBox.scrollHeight;
                        }});
                    }}
                    setInterval(loadMessages, 3000);
                    loadMessages();
                </script>
            </body>
        </html>
    '''

# API لعرض الرسائل (AJAX)
@app.route('/messages')
def get_messages():
    if not os.path.exists('messages.txt'):
        return jsonify([])
    with open('messages.txt', 'r') as file:
        messages = []
        for line in file:
            parts = line.strip().split('|')
            if len(parts) == 4:  # التأكد من أن السطر يحتوي على 4 أجزاء
                username, encrypted_message, image, timestamp = parts
                message = decrypt_message(encrypted_message)
                messages.append({
                    'username': username,
                    'message': message,
                    'image': image if image != 'None' else None,  # تحويل 'None' إلى قيمة null
                    'timestamp': timestamp
                })
        return jsonify(messages)

# إرسال رسالة
@app.route('/send', methods=['POST'])
def send():
    if 'username' not in session:
        return redirect(url_for('login'))

    message = request.form.get('message', '')
    image = request.files.get('image')
    image_filename = None

    if image and image.filename:
        image_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename}"
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    encrypted_message = encrypt_message(message)
    timestamp = datetime.now().strftime('%H:%M')
    with open('messages.txt', 'a') as file:
        file.write(f"{session['username']}|{encrypted_message}|{image_filename or 'None'}|{timestamp}\n")
    return redirect(url_for('chat'))

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# لعرض الصور
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)