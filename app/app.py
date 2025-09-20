from flask import Flask, render_template, request, redirect, url_for, session, flash
import pyodbc
from functools import wraps
from pathlib import Path

app = Flask(__name__)
app.secret_key = "cambia-esto-por-uno-seguro"

# --- Conexión SQL Server (Windows Auth) ---
CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=BENJAMIN\\SQLEXPRESS;"
    "DATABASE=Web_python_Flask;"
    "Trusted_Connection=yes;"
)

# --- Helper BD ---
def get_user_by_email(email: str):
    with pyodbc.connect(CONN_STR) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nombre, email, pass FROM dbo.usuarios WHERE email=? AND activo=1",
            (email,)
        )
        #ejecuta una consulta en sql
        row = cur.fetchone()
       # Con fetchone():
        #Se trae solo la primera fila del resultado.
        #Si hay resultados, devuelve una tupla con los valores.
        #Si no hay filas, devuelve None.
    if row:
        return {"id": row[0], "nombre": row[1], "email": row[2], "pass": row[3]}
    return None

# --- Decorador de protección ---
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped
    #Un decorador = función que modifica el comportamiento de otra.
    #@login_required asegura que la ruta solo se ejecute si hay usuario en sesión.
    #Si no, redirige al login.
    #Esto permite proteger varias rutas de manera elegante y reutilizable.

# --- Rutas ---
@app.route("/")
def index():
    return render_template("index.html", user_name=session.get("user_name"))
#http://127.0.0.1:5000/
#Esa función carga la plantilla index.html.
#Le pasa la variable user_name desde la sesión 
#(si está logueado, muestra el nombre; si no, muestra el link de login).

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user = get_user_by_email(email)
        # Comparación directa con columna "pass"
        if user and user["pass"] == password:
            session["user_id"] = user["id"]
            session["user_name"] = user["nombre"]
            flash("Bienvenido/a, " + user["nombre"], "success")
            return redirect(url_for("panel"))
        flash("Email o contraseña incorrectos.", "danger")
    return render_template("login.html")
#Si la petición es GET, devuelve el archivo login.html, que contiene el formulario con dos campos de entrada: 
# uno con name="email" y otro con name="password".
#Si la petición es POST, significa que el usuario escribió su email 
# y su contraseña en esos campos, y los envió. Flask recibe esos valores mediante 
# request.form.get("email") y request.form.get("password").

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
#cerrar session y borrar datos del usuario

@app.route("/panel")
@login_required
def panel():
    with pyodbc.connect(CONN_STR) as conn:
        cur = conn.cursor()
        cur.execute("SELECT modelo, precio, talla, imagen_url FROM dbo.zapatillas")
        rows = cur.fetchall()

    # Convertir resultados a lista de diccionarios
    productos = [
        {"modelo": r[0], "precio": r[1], "talla": r[2], "imagen_url": r[3]}
        for r in rows
    ]

    return render_template(
        "panel.html",
        user_name=session.get("user_name"),
        productos=productos
    )

# --- Ruta de prueba BD ---
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
    

if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent.resolve()
    #BASE_DIR es la carpeta donde está tu app.py.
    app.template_folder = str(BASE_DIR / "templates")
    #ubica los html
    app.run(debug=True)
    #inicia y depura
