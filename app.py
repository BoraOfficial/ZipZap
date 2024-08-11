from flask import Flask, request, redirect, url_for, render_template, send_file
import os
import hashlib
import sqlite3
import string
import random
from werkzeug.utils import secure_filename
import threading
import time
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

app.secret_key = os.urandom(24)
csrf = CSRFProtect(app)



def generate_random_text(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


# Define the upload folder and maximum file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'files')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB limit

def is_safe_file_path(file_path):
    return os.path.commonpath([file_path, app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']

# Initialize database
def init_db():
    with sqlite3.connect('files.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                          filename TEXT PRIMARY KEY,
                          salt TEXT,
                          ip TEXT,
                          original TEXT
                       )''')
        conn.commit()

init_db()

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_file(filename):
    with sqlite3.connect('files.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM files WHERE filename = ?''', (filename,))
        return cursor.fetchone()

def delete_file(filename):
    with sqlite3.connect('files.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM files WHERE filename = ?''', (filename,))
        conn.commit()

def generate_unique_filename(original, ip, extension):
    while True:
        random_string = generate_random_text(32)
        hashed_name = hashlib.sha256(random_string.encode('utf-8')+ip.encode('utf-8')).hexdigest()
        filename = f"{hashed_name}.{extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.isfile(file_path):
            with sqlite3.connect('files.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO files (filename, salt, ip, original) VALUES (?, ?, ?, ?)", (filename, random_string, ip, original))
                conn.commit()
            return filename

def delete_file_after_delay(file_path, filename):
    time.sleep(60)
    delete_file(filename)
    if os.path.isfile(file_path):
        os.remove(file_path)


@app.route('/')
def index():
    ip = request.args.get('ip')
    if ip == request.remote_addr:
        with sqlite3.connect('files.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT filename, original FROM files WHERE ip = ?''', (ip,))
            files_tuples = cursor.fetchall()
        files = [{'filename': row[0], 'original': row[1]} for row in files_tuples]
        return render_template("index.html", files=files)
    else:
        client_ip = request.remote_addr
        redirect_url = f"/?ip={client_ip}"
        return redirect(redirect_url)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    ip = request.form.get('ip')
    if file.filename == '':
        return 'No selected file', 400
    
    
    if ip == request.remote_addr:
        if file:
            original_filename = secure_filename(file.filename)
            extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            filename = generate_unique_filename(original_filename, ip, extension)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if not is_safe_file_path(file_path):
                return "An error has occurred. This request should not be tried again. That's all we know.", 500
            file.save(file_path)
            return redirect(url_for('index'))
        else:
            return 'No file uploaded', 400
        
    return 'Unauthorized', 401

@app.route('/download/<filename>')
def download_file(filename):
    file_data = get_file(filename)
    if not file_data:
        return 'File not found', 404
    salt = file_data[1]
    ip = request.args.get('ip')
    if ip == request.remote_addr:
        expected_filename = hashlib.sha256(salt.encode('utf-8') + ip.encode('utf-8')).hexdigest() + '.' + filename.split('.')[-1]
        if filename == expected_filename:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            thread = threading.Thread(target=delete_file_after_delay, args=(file_path, filename,))
            thread.start()
            return send_file(file_path, as_attachment=True, download_name=file_data[3])

    return 'Unauthorized', 401

@app.errorhandler(413)
def file_too_large(e):
    return 'File is too large. The maximum file size is 100 MB.', 413

CORS(app, resources={r"/*": {"origins": "*"}})

if __name__ == '__main__':
    app.run(debug=False)
