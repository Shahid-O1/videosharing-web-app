from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Use env var in deployment

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists (THIS IS THE FIXED CODE)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database setup (SQLite for demo, swap to Azure SQL for production)
def init_db():
    conn = sqlite3.connect('video_sharing.db')
    c = conn.cursor()

    # User table (role: creator/consumer)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('creator', 'consumer'))
                )''')

    # Videos table (with extra metadata)
    c.execute('''CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    publisher TEXT,
                    producer TEXT,
                    uploader TEXT NOT NULL,
                    genre TEXT,
                    age_rating TEXT,
                    file_path TEXT
                )''')

    # Comments table
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL,
                    commenter TEXT NOT NULL,
                    content TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )''')

    # Ratings table
    c.execute('''CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL,
                    rater TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )''')

    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Registration route (for consumers only, creators added manually)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'consumer')
        conn = sqlite3.connect('video_sharing.db')
        c = conn.cursor()
        try:
            hashed_pw = generate_password_hash(password)
            c.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_pw, role))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return 'Username already exists.'
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('video_sharing.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['username'] = username
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials, please try again.'

    return render_template('login.html')

# Dashboard - show latest videos, search option
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    query = request.args.get('q', '')
    conn = sqlite3.connect('video_sharing.db')
    c = conn.cursor()
    if query:
        c.execute('SELECT * FROM videos WHERE title LIKE ? OR genre LIKE ?', ('%'+query+'%', '%'+query+'%'))
    else:
        c.execute('SELECT * FROM videos ORDER BY id DESC')
    videos = c.fetchall()
    conn.close()
    return render_template('dashboard.html', videos=videos, query=query, role=session.get('role'))

# Video upload (creators only)
@app.route('/upload', methods=['GET', 'POST'])
def upload_video():
    if 'username' not in session or session.get('role') != 'creator':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        publisher = request.form['publisher']
        producer = request.form['producer']
        genre = request.form['genre']
        age_rating = request.form['age_rating']
        uploader = session['username']
        video_file = request.files['video_file']

        if video_file and allowed_file(video_file.filename):
            filename = secure_filename(video_file.filename)
            video_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(video_file_path)

            conn = sqlite3.connect('video_sharing.db')
            c = conn.cursor()
            c.execute('''INSERT INTO videos (title, description, publisher, producer, uploader, genre, age_rating, file_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (title, description, publisher, producer, uploader, genre, age_rating, video_file_path))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid file type.'
    return render_template('upload_video.html')

# Video details - show video, comments, ratings
@app.route('/video/<int:video_id>')
def video_detail(video_id):
    conn = sqlite3.connect('video_sharing.db')
    c = conn.cursor()
    c.execute('SELECT * FROM videos WHERE id=?', (video_id,))
    video = c.fetchone()
    c.execute('SELECT * FROM comments WHERE video_id=?', (video_id,))
    comments = c.fetchall()
    c.execute('SELECT AVG(rating) FROM ratings WHERE video_id=?', (video_id,))
    avg_rating = c.fetchone()[0]
    conn.close()
    return render_template('video_detail.html', video=video, comments=comments, avg_rating=avg_rating)

# Comment on video
@app.route('/comment/<int:video_id>', methods=['POST'])
def comment(video_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    content = request.form['content']
    commenter = session['username']
    conn = sqlite3.connect('video_sharing.db')
    c = conn.cursor()
    c.execute('INSERT INTO comments (video_id, commenter, content) VALUES (?, ?, ?)', (video_id, commenter, content))
    conn.commit()
    conn.close()
    return redirect(url_for('video_detail', video_id=video_id))

# Rate video
@app.route('/rate/<int:video_id>', methods=['POST'])
def rate(video_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    rating = int(request.form['rating'])
    rater = session['username']
    conn = sqlite3.connect('video_sharing.db')
    c = conn.cursor()
    # Allow user to rate only once
    c.execute('SELECT * FROM ratings WHERE video_id=? AND rater=?', (video_id, rater))
    if c.fetchone():
        conn.close()
        return 'You have already rated this video.'
    c.execute('INSERT INTO ratings (video_id, rater, rating) VALUES (?, ?, ?)', (video_id, rater, rating))
    conn.commit()
    conn.close()
    return redirect(url_for('video_detail', video_id=video_id))

# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# REST API endpoint: Get all videos (JSON)
@app.route('/api/videos')
def api_videos():
    conn = sqlite3.connect('video_sharing.db')
    c = conn.cursor()
    c.execute('SELECT id, title, description, genre, age_rating, uploader FROM videos ORDER BY id DESC')
    videos = c.fetchall()
    conn.close()
    return jsonify([{
        'id': v[0],
        'title': v[1],
        'description': v[2],
        'genre': v[3],
        'age_rating': v[4],
        'uploader': v[5]
    } for v in videos])

# Initialize database
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
