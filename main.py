from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import join_room, leave_room, send, SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
import random
import os
import sqlite3
from string import ascii_uppercase

# Flask app setup
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "default-secret-key")
socketio = SocketIO(app)

# Rooms dictionary to store active rooms
rooms = {}

# SQLite setup for users
def init_db():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, password):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()

init_db()

# Generate a unique room code
def generate_unique_code(length=4):
    code = ''.join(random.choice(ascii_uppercase) for _ in range(length))
    return code

@app.route("/", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST" and "login" in request.form:
        username = request.form.get("username")
        password = request.form.get("password")

        user = get_user(username)
        if user and check_password_hash(user[1], password):
            session["username"] = username
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST" and "signup" in request.form:
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("signup"))

        if get_user(username):
            flash("Username already exists.")
            return redirect(url_for("signup"))

        create_user(username, password)
        flash("Account created successfully! Please log in.")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/home", methods=["GET", "POST"])
def home():
    if "username" not in session:
        return redirect(url_for("login"))

    name = session["username"]
    code = None
    error = None

    if request.method == "POST":
        code = request.form.get("code")
        join = request.form.get("join")
        create = request.form.get("create")

        if join and not code:
            error = "Please enter a room code."
        elif create:
            code = generate_unique_code()
            rooms[code] = {"members": 0}
        elif join and code not in rooms:
            error = "Room does not exist."
        else:
            session["room"] = code
            return redirect(url_for("room"))

    return render_template("home.html", name=name, code=code, error=error)

@app.route("/room")
def room():
    # This route is just an example for handling room view
    if "username" not in session or "room" not in session:
        return redirect(url_for("login"))

    room_code = session["room"]
    return render_template("room.html", room_code=room_code)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

