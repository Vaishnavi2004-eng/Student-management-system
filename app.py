# app.py
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
def init_db():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    name TEXT NOT NULL,
    course TEXT NOT NULL,
    sub1 INTEGER,
    sub2 INTEGER,
    sub3 INTEGER,
    sub4 INTEGER,
    sub5 INTEGER
)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL)''')
    # Add default admin if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', 'admin123', 'admin'))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    if session['role'] == 'admin':
        cursor.execute("SELECT * FROM students")
    else:
        cursor.execute("SELECT * FROM students WHERE username = ?", (session['username'],))

    students = cursor.fetchall()
    conn.close()

    return render_template('index.html', students=students, role=session.get('role'), get_grade=get_grade)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect('/dashboard')
        else:
            return "Invalid credentials. <a href='/login'>Try again</a>"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        course = request.form['course']

        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, 'client'))
            cursor.execute("INSERT INTO students (username, name, course, sub1, sub2, sub3, sub4, sub5) VALUES (?, ?, ?, NULL, NULL, NULL, NULL, NULL)", (username, name, course))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists. <a href='/register'>Try again</a>"

        conn.close()
        return redirect('/login')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/add', methods=['POST'])
def add_student():
    if session.get('role') != 'admin':
        return "Unauthorized"
    name = request.form['name']
    course = request.form['course']
    username = request.form['username']
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name, course, username) VALUES (?, ?, ?)", (name, course, username))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/delete/<int:id>')
def delete_student(id):
    if session.get('role') != 'admin':
        return "Unauthorized"
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    if session.get('role') != 'admin':
        return "Unauthorized"

    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        course = request.form['course']
        cursor.execute("UPDATE students SET name = ?, course = ? WHERE id = ?", (name, course, id))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()
    conn.close()
    return render_template('update.html', student=student)

@app.route('/edit_marks/<int:id>', methods=['GET', 'POST'])
def edit_marks(id):
    if session.get('role') != 'admin':
        return "Unauthorized"

    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        sub1 = request.form['sub1']
        sub2 = request.form['sub2']
        sub3 = request.form['sub3']
        sub4 = request.form['sub4']
        sub5 = request.form['sub5']
        cursor.execute('''UPDATE students SET sub1=?, sub2=?, sub3=?, sub4=?, sub5=? WHERE id=?''',
                       (sub1, sub2, sub3, sub4, sub5, id))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()
    conn.close()
    return render_template('edit_marks.html', student=student)

def get_grade(mark):
    if mark is None:
        return "Not Yet Declared"
    elif mark >= 90:
        return "A+"
    elif mark >= 80:
        return "A"
    elif mark >= 70:
        return "B"
    elif mark >= 60:
        return "C"
    elif mark >= 50:
        return "D"
    else:
        return "F"

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
