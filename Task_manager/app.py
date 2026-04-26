from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, request, render_template, redirect, session
from database import get_connection

app = Flask(__name__)
app.secret_key = "helloworld"

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return wrapper

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT    
    )               
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        user_id INTEGER
    )
    ''')

    conn.commit()
    conn.close()

@app.route('/')
def home():
    if 'username' in session:
        return redirect('/dashboard')
    return render_template('home.html')

@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if username and password:
            hashed_password = generate_password_hash(password)

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            if user:
                return render_template('try_again.html', error='the username is taken')
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")
        return render_template('try_again.html', error='missing data')
    return render_template("register.html")

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
        "SELECT * FROM users WHERE username = ?", 
        (username,)
        )
        user = cursor.fetchone()
        conn.close()
        if user:
            if username and check_password_hash(user[2], password):
                session["user_id"] = user[0]
                session["username"] = user[1]
                return redirect('/dashboard')
        return render_template('try_again.html', error="invalid credentials")
    return render_template("login.html")

@app.route('/dashboard', methods=["GET"])
@login_required
def dashboard():
        return render_template("dashboard.html", user_id=session['user_id'], username=session['username'])
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

@app.route('/task_manager', methods=["GET"])
@login_required
def task_manager():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE user_id = ?",
            (session["user_id"],)
        )
        tasks = cursor.fetchall()
        conn.close()
        return render_template('task_manager.html', tasks=tasks)

@app.route("/add_task", methods=["POST", "GET"])
@login_required
def add_task():
    if request.method == "POST":
        title = request.form.get("title")
        if title:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO tasks(title, user_id) VALUES(?, ?)",
                (title, session["user_id"])
            )
            conn.commit()
            conn.close()
            return redirect("/task_manager")
        return render_template('try_again.html', error="missing task")
    return render_template('add_task.html')

@app.route("/remove_task/<int:task_id>", methods=["GET"])
@login_required
def remove_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    return redirect('/task_manager')

@app.route('/edit_task/<int:task_id>', methods=["GET"])
@login_required
def edit_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id=?",
        (task_id,)
    )
    task = cursor.fetchone()
    conn.close()
    return render_template("edit.html", task=task)

@app.route('/update_task/<int:task_id>', methods=["POST", "GET"])
@login_required
def update_task(task_id):
    if request.method == "POST":
        title = request.form.get("title")
        if title:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE tasks SET title=? WHERE id=? and user_id=?",
                (title, task_id, session["user_id"])
            )
            conn.commit()
            conn.close()
            return redirect("/task_manager")
        return render_template("try_again.html", error="invalid update task")
    return redirect("/task_manager")

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=10000)
