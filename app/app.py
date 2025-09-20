from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyodbc
from functools import wraps
from pathlib import Path

# --- Configuración de Flask ---
app = Flask(__name__)
app.secret_key = "cambia-esto-por-uno-seguro"

# --- Conexión a SQL Server (Windows Auth) ---
CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=BENJAMIN\\SQLEXPRESS;"
    "DATABASE=Web_python_Flask;"
    "Trusted_Connection=yes;"
)

# --- Helper: obtener usuario por email ---
def get_user_by_email(email: str):
    with pyodbc.connect(CONN_STR) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nombre, email, pass FROM dbo.usuarios WHERE email=? AND activo=1",
            (email,)
        )
        row = cur.fetchone()
    if row:
        return {"id": row[0], "nombre": row[1], "email": row[2], "pass": row[3]}
    return None

# --- Decorador para rutas protegidas ---
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

# --- Rutas ---
@app.route("/")
def index():
    return render_template("index.html", user_name=session.get("user_name"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(email)

        # Comparación directa (TEXTO PLANO, NO SEGURA)
        if user and user["pass"] == password:
            session["user_id"] = user["id"]
            session["user_name"] = user["nombre"]
            flash("Bienvenido/a, " + user["nombre"], "success")
            return redirect(url_for("panel"))

        flash("Email o contraseña incorrectos.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/panel")
@login_required
def panel():
    with pyodbc.connect(CONN_STR) as conn:
        cur = conn.cursor()
        cur.execute("SELECT modelo, precio, talla, imagen_url FROM dbo.zapatillas")
        rows = cur.fetchall()

    productos = [
        {"modelo": r[0], "precio": r[1], "talla": r[2], "imagen_url": r[3]}
        for r in rows
    ]

    return render_template("panel.html",
                           user_name=session.get("user_name"),
                           productos=productos)

@app.route("/db_test")
def db_test():
    try:
        with pyodbc.connect(CONN_STR) as conn:
            cur = conn.cursor()
            cur.execute("SELECT TOP 1 id, nombre, email, pass FROM dbo.usuarios;")
            row = cur.fetchone()
        return f"Conexión OK -> {row}" if row else "Conexión OK (sin filas)"
    except Exception as e:
        return f"Error BD: {e}"

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        try:
            with pyodbc.connect(CONN_STR) as conn:
                cur = conn.cursor()
                # Guardado en TEXTO PLANO (NO SEGURO). Más adelante cambiaremos a hash.
                cur.execute("""
                    INSERT INTO dbo.usuarios (nombre, email, pass, activo)
                    VALUES (?, ?, ?, ?)
                """, (nombre, email, password, 1))
                conn.commit()

            flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            flash(f"Error al registrar: {e}", "danger")

    return render_template("register.html")

# --- Ejecutar app ---
if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent.resolve()
    app.template_folder = str(BASE_DIR / "templates")
    app.static_folder = str(BASE_DIR / "static")
    app.run(debug=True)
