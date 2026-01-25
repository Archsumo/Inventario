from flask import Flask, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

# ---------- BASE DE DATOS ----------
def get_db():
    return sqlite3.connect("users.db")

# Función que inicializa las tablas de la base de datos
def init_db():
    db = get_db()
    cursor = db.cursor()

    # Crear tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    # Crear tabla de inventario
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT,
            quantity INTEGER,
            state TEXT
        )
    """)

    # Crear tabla de historial de cambios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            action TEXT,
            timestamp TEXT,
            state TEXT
        )
    """)

    db.commit()
    db.close()

# Inicializa las tablas al arrancar la app
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
        return redirect("/select_state")  # Redirige a la selección de estado
    else:
        return """
        <h2>Bienvenido al panel SUPERVISOR 👷</h2>
        <a href="/view_inventory">Ver inventario</a><br>
        <a href="/edit_quantities">Modificar cantidades</a><br>
        <a href="/logout">Cerrar sesión</a>
        """

# ---------- SELECCIONAR ESTADO ----------
@app.route("/select_state", methods=["GET", "POST"])
def select_state():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        selected_state = request.form["state"]
        return redirect(f"/view_inventory/{selected_state}")  # Redirige al inventario del estado seleccionado

    return """
    <h2>Selecciona un estado</h2>
    <form method="post">
        <select name="state">
            <option value="GDL">Guadalajara</option>
            <option value="SL">San Luis</option>
            <option value="SLP">Silao</option>
        </select><br>
        <button>Seleccionar</button>
    </form>
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
        state = request.form["state"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO inventory (product_name, quantity, state) VALUES (?, ?, ?)",
                       (product_name, quantity, state))

        # Guardar en historial
        cursor.execute("INSERT INTO history (user, action, timestamp, state) VALUES (?, ?, ?, ?)",
                       (session["user"], f"Agregó {product_name} con cantidad {quantity}", "2025-01-01 12:00", state))
        
        db.commit()
        db.close()

        return redirect(f"/view_inventory/{state}")  # Redirige al inventario del estado seleccionado

    return """
    <h2>Agregar Producto</h2>
    <form method="post">
        Nombre del producto: <input name="product_name"><br>
        Cantidad: <input name="quantity"><br>
        Estado: 
        <select name="state">
            <option value="GDL">Guadalajara</option>
            <option value="SL">San Luis</option>
            <option value="SLP">Silao</option>
        </select><br>
        <button>Agregar</button>
    </form>
    <a href="/dashboard">Volver al Dashboard</a>
    """

# ---------- VER INVENTARIO POR ESTADO ----------
@app.route("/view_inventory/<state>")
def view_inventory(state):
    if "user" not in session:
        return redirect("/")

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM inventory WHERE state = ?", (state,))
    inventory = cursor.fetchall()
    db.close()

    return f"""
    <h2>Inventario de {state}</h2>
    <ul>
        {''.join([f'<li>{item[1]}: {item[2]}</li>' for item in inventory])}
    </ul>
    <a href="/select_state">Seleccionar otro estado</a><br>
    <a href="/dashboard">Volver al Dashboard</a>
    """

# ---------- VER HISTORIAL DE CAMBIOS POR ESTADO ----------
@app.route("/view_history/<state>")
def view_history(state):
    if "user" not in session:
        return redirect("/")

    if session["role"] != "admin":
        return "No autorizado ❌"

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM history WHERE state = ?", (state,))
    history = cursor.fetchall()
    db.close()

    return f"""
    <h2>Historial de cambios en {state}</h2>
    <ul>
        {''.join([f'<li>{entry[1]} {entry[2]} | {entry[3]}</li>' for entry in history])}
    </ul>
    <a href="/select_state">Seleccionar otro estado</a><br>
    <a href="/dashboard">Volver al Dashboard</a>
    """

# ---------- GUARDIAS ----------
@app.route("/guardias")
def guardias():
    if "user" not in session:
        return redirect("/")

    return """
    <h2>Guardias</h2>
    <p>Información sobre los guardias.</p>
    <a href="/dashboard">Volver al Dashboard</a>
    """

# ---------- CAMIONES ----------
@app.route("/camiones")
def camiones():
    if "user" not in session:
        return redirect("/")

    return """
    <h2>Entradas y salidas de camiones</h2>
    <p>Información sobre los camiones.</p>
    <a href="/dashboard">Volver al Dashboard</a>
    """

# ---------- UNIFORMES ----------
@app.route("/uniformes")
def uniformes():
    if "user" not in session:
        return redirect("/")

    return """
    <h2>Uniformes</h2>
    <p>Información sobre botas, camisas y otros uniformes.</p>
    <a href="/dashboard">Volver al Dashboard</a>
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
