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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            quantity INTEGER
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            action TEXT,
            timestamp TEXT
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
        return """
        <h2>Bienvenido al panel ADMIN 🔑</h2>
        <a href="/add_product">Agregar producto</a><br>
        <a href="/view_inventory">Ver inventario</a><br>
        <a href="/view_history">Ver historial de cambios</a><br>
        <a href="/create_user">Crear usuario</a><br>
        <a href="/logout">Cerrar sesión</a>
        """
    else:
        return """
        <h2>Bienvenido al panel SUPERVISOR 👷</h2>
        <a href="/view_inventory">Ver inventario</a><br>
        <a href="/edit_quantities">Modificar cantidades</a><br>
        <a href="/logout">Cerrar sesión</a>
        """

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

# ---------- AGREGAR PRODUCTO (SOLO ADMIN) ----------
@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if session.get("role") != "admin":
        return "No autorizado ❌"

    if request.method == "POST":
        product_name = request.form["product_name"]
        quantity = request.form["quantity"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO inventory (product_name, quantity) VALUES (?, ?)",
                       (product_name, quantity))
        db.commit()
        db.close()

        return "Producto agregado ✅"

    return """
    <h2>Agregar Producto</h2>
    <form method="post">
        Nombre del producto: <input name="product_name"><br>
        Cantidad: <input name="quantity"><br>
        <button>Agregar</button>
    </form>
    """

# ---------- VER INVENTARIO ----------
@app.route("/view_inventory")
def view_inventory():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM inventory")
    inventory = cursor.fetchall()
    db.close()

    return f"""
    <h2>Inventario</h2>
    <ul>
        {''.join([f'<li>{item[1]}: {item[2]}</li>' for item in inventory])}
    </ul>
    <a href="/dashboard">Volver</a>
    """

# ---------- CERRAR SESIÓN ----------
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect("/")

def crear_admin_inicial():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users")
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("admin123"), "admin")
        )
        db.commit()

    db.close()

crear_admin_inicial()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

