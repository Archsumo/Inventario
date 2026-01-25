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
        return redirect(f"/state_dashboard/{selected_state}")  # Redirige a la vista del estado

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

# ---------- PANEL DEL ESTADO ----------
@app.route("/state_dashboard/<state>")
def state_dashboard(state):
    if "user" not in session:
        return redirect("/")

    return f"""
    <h2>Panel de {state}</h2>
    <h3>Selecciona una opción:</h3>
    <a href="/add_product/{state}">Agregar producto</a><br>
    <a href="/view_inventory/{state}">Ver inventario</a><br>
    <a href="/camiones/{state}">Entradas y salidas de camiones</a><br>
    <a href="/uniformes/{state}">Ver uniformes</a><br>
    <a href="/view_history/{state}">Ver historial de cambios</a><br>
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

# ---------- VER USUARIOS (SOLO ADMIN) ----------
@app.route("/view_users")
def view_users():
    if session.get("role") != "admin":
        return "No autorizado ❌"

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    db.close()

    return f"""
    <h2>Usuarios</h2>
    <ul>
        {''.join([f'<li>{user[1]} - {user[2]}</li>' for user in users])}
    </ul>
    <a href="/dashboard">Volver al Dashboard</a>
    """

# ---------- ELIMINAR USUARIO (SOLO ADMIN) ----------
@app.route("/delete_user_form", methods=["GET", "POST"])
def delete_user_form():
    if session.get("role") != "admin":
        return "No autorizado ❌"

    if request.method == "POST":
        password = request.form["password"]
        username = request.form["username"]

        # Comprobar que la contraseña ingresada sea la correcta para eliminar un usuario
        if password != "claveSecreta123":  # Aquí va la clave de seguridad
            return "Contraseña incorrecta ❌"

        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        db.commit()
        db.close()

        return "Usuario eliminado ✅"

    # Obtener todos los usuarios para que admin elija a quién eliminar
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()
    db.close()

    return f"""
    <h2>Eliminar usuario</h2>
    <form method="post">
        Introduce la clave de confirmación: <input name="password" type="password"><br>
        Selecciona un usuario a eliminar: 
        <select name="username">
            {''.join([f'<option value="{user[0]}">{user[0]}</option>' for user in users])}
        </select><br>
        <button>Eliminar</button>
    </form>
    <a href="/dashboard">Volver al Dashboard</a>
    """

# ---------- AGREGAR PRODUCTO (SOLO ADMIN) ----------
@app.route("/add_product/<state>", methods=["GET", "POST"])
def add_product(state):
    if session.get("role") != "admin":
        return "No autorizado ❌"

    if request.method == "POST":
        product_name = request.form["product_name"]
        quantity = request.form["quantity"]

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

    return f"""
    <h2>Agregar Producto en {state}</h2>
    <form method="post">
        Nombre del producto: <input name="product_name"><br>
        Cantidad: <input name="quantity"><br>
        <button>Agregar</button>
    </form>
    <a href="/state_dashboard/{state}">Volver al Panel de {state}</a>
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
    <a href="/state_dashboard/{state}">Volver al Panel de {state}</a>
    """

# ---------- HISTORIAL DE CAMBIOS POR ESTADO ----------
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
    <a href="/state_dashboard/{state}">Volver al Panel de {state}</a>
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
