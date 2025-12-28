from flask import Flask, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

# ---------- BASE DE DATOS ----------
def get_db():
    return sqlite3.connect("users.db")

def init_db():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    db.commit()
    db.close()

init_db()

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT password, role FROM users WHERE username = ?", (user,))
        result = cursor.fetchone()
        db.close()

        if result and check_password_hash(result[0], password):
            session["user"] = user
            session["role"] = result[1]
            return redirect("/dashboard")
        else:
            return "Usuario o contraseña incorrectos ❌"

    return """
    <h2>Login</h2>
    <form method="post">
        Usuario: <input name="username"><br>
        Contraseña: <input type="password" name="password"><br>
        <button>Entrar</button>
    </form>
    """

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    if session["role"] == "admin":
        return "Panel ADMIN 🔑"
    else:
        return "Panel SUPERVISOR 👷"

# ---------- CREAR USUARIO (SOLO ADMIN) ----------
@app.route("/create_user", methods=["POST"])
def create_user():
    if session.get("role") != "admin":
        return "No autorizado ❌"

    user = request.form["username"]
    password = generate_password_hash(request.form["password"])
    role = request.form["role"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   (user, password, role))
    db.commit()
    db.close()

    return "Usuario creado ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
