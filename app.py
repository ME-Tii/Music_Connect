import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'music-connect-secret-key-2024')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 30  # 30 days
DATABASE = 'music_connect.db'

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID[:20]}..." if GOOGLE_CLIENT_ID else "GOOGLE_CLIENT_ID: NOT SET")
logger.info(f"GOOGLE_CLIENT_SECRET: {GOOGLE_CLIENT_SECRET[:10]}..." if GOOGLE_CLIENT_SECRET else "GOOGLE_CLIENT_SECRET: NOT SET")

oauth = OAuth(app)
google = None

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    google = oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
        fetch_userinfo=False
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
            bio TEXT DEFAULT '',
            instruments TEXT DEFAULT '',
            location TEXT DEFAULT '',
            avatar_url TEXT DEFAULT '',
            genres TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    ''')
    try:
        cursor.execute('ALTER TABLE messages ADD COLUMN read INTEGER DEFAULT 0')
    except:
        pass
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
def profile_page():
    return render_template('profile.html')

@app.route('/messages')
def messages_page():
    return render_template('messages.html')

@app.route('/api/google/login')
def google_login():
    if not google:
        return jsonify({'error': 'Google OAuth not configured'}), 500
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/api/google/auth')
def google_auth():
    logger.info("Google auth route called")
    if not google:
        logger.error("Google OAuth not configured")
        return jsonify({'error': 'Google OAuth not configured'}), 500
    try:
        token = google.authorize_access_token()
        logger.info(f"Token received: {bool(token)}")
    except Exception as e:
        logger.error(f"Error in authorize_access_token: {e}")
        return jsonify({'error': str(e)}), 400
    
    # Fetch user info manually
    userinfo_resp = google.get('https://www.googleapis.com/oauth2/v2/userinfo', token=token)
    user_info = userinfo_resp.json()
    logger.info(f"User info: {user_info}")
    
    if not user_info:
        return jsonify({'error': 'Failed to get user info'}), 400
    
    email = user_info.get('email')
    name = user_info.get('name')
    google_id = user_info.get('sub')
    avatar_url = user_info.get('picture', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name FROM users WHERE google_id = ?', (google_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('SELECT id, name FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user:
            cursor.execute('UPDATE users SET google_id = ?, avatar_url = ? WHERE id = ?', 
                          (google_id, avatar_url, user['id']))
        else:
            cursor.execute(
                'INSERT INTO users (name, email, google_id, avatar_url, user_type) VALUES (?, ?, ?, ?, ?)',
                (name, email, google_id, avatar_url, 'musician')
            )
            cursor.execute('SELECT id, name FROM users WHERE google_id = ?', (google_id,))
            user = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    session['user_id'] = user['id']
    session['user_name'] = user['name']
    
    return redirect('/profile')

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
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT id, name, email, user_type, bio, instruments, location, avatar_url, genres 
                      FROM users WHERE id = ?''', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'user': None})
    
    return jsonify({
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'user_type': user['user_type'],
            'bio': user['bio'] or '',
            'instruments': user['instruments'] or '',
            'location': user['location'] or '',
            'avatar_url': user['avatar_url'] or '',
            'genres': user['genres'] or ''
        }
    })

@app.route('/api/profile', methods=['GET', 'PUT'])
def profile():
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = request.args.get('id')
    session.permanent = True
    
    if request.method == 'PUT':
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        user_id = session['user_id']
    elif user_id:
        # GET with specific user ID - public profile view, no login needed
        pass
    else:
        # GET without ID - require login
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        user_id = session['user_id']
    
    if request.method == 'GET':
        cursor.execute('''SELECT id, name, email, user_type, bio, instruments, location, avatar_url, genres 
                          FROM users WHERE id = ?''', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'user_type': user['user_type'],
                'bio': user['bio'] or '',
                'instruments': user['instruments'] or '',
                'location': user['location'] or '',
                'avatar_url': user['avatar_url'] or '',
                'genres': user['genres'] or ''
            }
        })
    
    elif request.method == 'PUT':
        if 'user_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        
        data = request.get_json()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET name = ?, user_type = ?, bio = ?, instruments = ?, location = ?, avatar_url = ?, genres = ?
                WHERE id = ?
            ''', (
                data.get('name', ''),
                data.get('user_type', 'musician'),
                data.get('bio', ''),
                data.get('instruments', ''),
                data.get('location', ''),
                data.get('avatar_url', ''),
                data.get('genres', ''),
                session['user_id']
            ))
            conn.commit()
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
        session['user_name'] = data.get('name', session['user_name'])
        
        cursor.execute('''SELECT id, name, email, user_type, bio, instruments, location, avatar_url, genres 
                          FROM users WHERE id = ?''', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'message': 'Profile updated',
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'user_type': user['user_type'],
                'bio': user['bio'] or '',
                'instruments': user['instruments'] or '',
                'location': user['location'] or '',
                'avatar_url': user['avatar_url'] or '',
                'genres': user['genres'] or ''
            }
        })

@app.route('/api/messages')
def get_conversations():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT 
            CASE 
                WHEN m.sender_id = ? THEN m.receiver_id 
                ELSE m.sender_id 
            END as other_user_id,
            u.name, u.avatar_url, u.instruments,
            (SELECT message FROM messages WHERE 
                (sender_id = ? AND receiver_id = u.id) OR 
                (sender_id = u.id AND receiver_id = ?) 
             ORDER BY created_at DESC LIMIT 1) as last_message,
            (SELECT created_at FROM messages WHERE 
                (sender_id = ? AND receiver_id = u.id) OR 
                (sender_id = u.id AND receiver_id = ?) 
             ORDER BY created_at DESC LIMIT 1) as last_message_time,
            (SELECT COUNT(*) FROM messages WHERE sender_id = u.id AND receiver_id = ? AND read = 0) as unread_count
        FROM messages m
        JOIN users u ON (u.id = CASE WHEN m.sender_id = ? THEN m.receiver_id ELSE m.sender_id END)
        WHERE m.sender_id = ? OR m.receiver_id = ?
        ORDER BY last_message_time DESC
    ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))
    
    conversations = []
    for row in cursor.fetchall():
        conversations.append({
            'id': row['other_user_id'],
            'name': row['name'],
            'avatar_url': row['avatar_url'] or '',
            'instruments': row['instruments'] or '',
            'last_message': row['last_message'] or '',
            'last_message_time': row['last_message_time'] or '',
            'unread_count': row['unread_count'] or 0
        })
    
    conn.close()
    return jsonify({'conversations': conversations})

@app.route('/api/messages/<int:user_id>')
def get_chat(user_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    current_user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, u.name as sender_name, u.avatar_url as sender_avatar
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
        ORDER BY created_at ASC
    ''', (current_user_id, user_id, user_id, current_user_id))
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            'id': row['id'],
            'sender_id': row['sender_id'],
            'sender_name': row['sender_name'],
            'sender_avatar': row['sender_avatar'] or '',
            'message': row['message'],
            'created_at': row['created_at'],
            'is_mine': row['sender_id'] == current_user_id
        })
    
    cursor.execute('SELECT name, avatar_url, instruments FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    cursor.execute('''
        UPDATE messages SET read = 1 
        WHERE sender_id = ? AND receiver_id = ? AND read = 0
    ''', (user_id, current_user_id))
    
    conn.commit()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'messages': messages,
        'other_user': {
            'id': user_id,
            'name': user['name'],
            'avatar_url': user['avatar_url'] or '',
            'instruments': user['instruments'] or ''
        }
    })

@app.route('/api/messages/send', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    message = data.get('message')
    
    if not receiver_id or not message:
        return jsonify({'error': 'Missing data'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO messages (sender_id, receiver_id, message, read)
        VALUES (?, ?, ?, 0)
    ''', (session['user_id'], receiver_id, message))
    
    message_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute('SELECT created_at FROM messages WHERE id = ?', (message_id,))
    created_at = cursor.fetchone()['created_at']
    
    conn.close()
    
    return jsonify({
        'id': message_id,
        'sender_id': session['user_id'],
        'message': message,
        'created_at': created_at,
        'is_mine': True
    }), 201

@app.route('/api/users/search')
def search_users():
    query = request.args.get('q', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if query:
        like_query = '%' + query + '%'
        cursor.execute('''
            SELECT id, name, avatar_url, instruments, genres, location
            FROM users 
            WHERE name LIKE ? OR instruments LIKE ? OR genres LIKE ? OR location LIKE ?
            LIMIT 20
        ''', (like_query, like_query, like_query, like_query))
    else:
        cursor.execute('''
            SELECT id, name, avatar_url, instruments, genres, location
            FROM users 
            LIMIT 20
        ''')
    
    users = []
    for row in cursor.fetchall():
        users.append({
            'id': row['id'],
            'name': row['name'],
            'avatar_url': row['avatar_url'] or '',
            'instruments': row['instruments'] or '',
            'genres': row['genres'] or '',
            'location': row['location'] or ''
        })
    
    conn.close()
    return jsonify({'users': users})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
