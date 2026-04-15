import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'music-connect-secret-key-2024')
DATABASE = 'music_connect.db'

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

oauth = OAuth(app)
google = None

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    google = oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT,
            user_type TEXT DEFAULT 'musician',
            google_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/google/login')
def google_login():
    if not google:
        return jsonify({'error': 'Google OAuth not configured'}), 500
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/api/google/auth')
def google_auth():
    if not google:
        return jsonify({'error': 'Google OAuth not configured'}), 500
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        return jsonify({'error': 'Failed to get user info'}), 400
    
    email = user_info.get('email')
    name = user_info.get('name')
    google_id = user_info.get('sub')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name FROM users WHERE google_id = ?', (google_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('SELECT id, name FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user:
            cursor.execute('UPDATE users SET google_id = ? WHERE id = ?', (google_id, user['id']))
        else:
            cursor.execute(
                'INSERT INTO users (name, email, google_id, user_type) VALUES (?, ?, ?, ?)',
                (name, email, google_id, 'musician')
            )
            cursor.execute('SELECT id, name FROM users WHERE google_id = ?', (google_id,))
            user = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    session['user_id'] = user['id']
    session['user_name'] = user['name']
    
    return redirect('/?logged_in=true')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type', 'musician')

    if not all([name, email, password]):
        return jsonify({'error': 'All fields are required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Email already registered'}), 409

    hashed_password = generate_password_hash(password)
    cursor.execute(
        'INSERT INTO users (name, email, password, user_type) VALUES (?, ?, ?, ?)',
        (name, email, hashed_password, user_type)
    )
    conn.commit()
    
    cursor.execute('SELECT id, name, email, user_type FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    session['user_id'] = user['id']
    session['user_name'] = user['name']
    
    return jsonify({
        'message': 'Registration successful',
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'user_type': user['user_type']
        }
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'error': 'Email and password are required'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, password, user_type FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    session['user_id'] = user['id']
    session['user_name'] = user['name']

    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'user_type': user['user_type']
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/me')
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'user': None})
    
    return jsonify({
        'user': {
            'id': session['user_id'],
            'name': session['user_name']
        }
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
