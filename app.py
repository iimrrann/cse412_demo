from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify
import sqlite3
import numpy as np
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'database/portfolio.db'
app.secret_key = 'your_secret_key_here'

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Database initialization
def init_db():
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                contact_info TEXT,
                photo_path TEXT,
                bio TEXT,
                soft_skills TEXT,
                technical_skills TEXT,
                institute TEXT,
                degree TEXT,
                year TEXT,
                grade TEXT,
                work_experience TEXT,
                projects TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Handle login
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            return redirect(url_for('portfolio'))
        else:
            return "Invalid credentials", 401

# Handle signup
@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = generate_password_hash(request.form['password'])
    
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        
        # Check if the email already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user:
            return "Email already exists. Please use a different email.", 400
        
        # Insert new user if email doesn't exist
        try:
            cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
            conn.commit()
            return redirect(url_for('portfolio'))
        except sqlite3.IntegrityError:
            return "Signup failed. Email may already exist.", 400

# Handle portfolio submission
@app.route('/portfolio', methods=['POST'])
def portfolio():
    if 'user_id' not in session:
        return "Unauthorized", 401

    if request.method == 'POST':
        full_name = request.form['full-name']
        contact_info = request.form['contact-info']
        bio = request.form['bio']
        soft_skills = request.form['soft-skills']
        technical_skills = request.form['technical-skills']
        institute = request.form['institute']
        degree = request.form['degree']
        year = request.form['year']
        grade = request.form['grade']
        work_experience = request.form.getlist('work-experience')
        projects = request.form['projects']

        # Handle file upload
        photo = request.files['photo']
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(photo.filename))
        photo.save(photo_path)

        # Save to database
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolios (
                    user_id, full_name, contact_info, photo_path, bio, soft_skills, technical_skills,
                    institute, degree, year, grade, work_experience, projects
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], full_name, contact_info, photo_path, bio, soft_skills, technical_skills,
                  institute, degree, year, grade, str(work_experience), projects))
            conn.commit()

        return "Portfolio submitted successfully!"

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/save-progress', methods=['POST'])
def save_progress():
    if 'user_id' not in session:
        return "Unauthorized", 401

    data = {
        "full_name": request.form.get("full-name"),
        "contact_info": request.form.get("contact-info"),
        "bio": request.form.get("bio"),
        "soft_skills": request.form.get("soft-skills"),
        "technical_skills": request.form.get("technical-skills"),
        "institute": request.form.get("institute"),
        "degree": request.form.get("degree"),
        "year": request.form.get("year"),
        "grade": request.form.get("grade"),
        "projects": request.form.get("projects"),
    }
    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE portfolios SET
            full_name = ?, contact_info = ?, bio = ?, soft_skills = ?, technical_skills = ?,
            institute = ?, degree = ?, year = ?, grade = ?, projects = ?
            WHERE user_id = ?
        ''', (
            data["full_name"], data["contact_info"], data["bio"], data["soft_skills"], data["technical_skills"],
            data["institute"], data["degree"], data["year"], data["grade"], data["projects"], session['user_id']
        ))
        conn.commit()
    return "Progress saved!"

@app.route('/load-progress')
def load_progress():
    if 'user_id' not in session:
        return "Unauthorized", 401

    with sqlite3.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM portfolios WHERE user_id = ?', (session['user_id'],))
        portfolio = cursor.fetchone()
    return jsonify(portfolio) if portfolio else jsonify({})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
