from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- Configuración de la base de datos ---
DB_PATH = os.path.join(os.path.dirname(__file__), 'presupuesto.db')
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    conn.commit()
    conn.close()

# --- Rutas principales ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        Usuario = request.form['Usuario'] 
        Contrasena = request.form['Contrasena'] 
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT Id_usuario FROM Usuarios WHERE Usuario=? AND Contrasena=?', (Usuario, Contrasena))
        user = c.fetchone()
        if not user:
            c.execute('SELECT Id_usuario FROM Usuarios WHERE Usuario=?', (Usuario,))
            user_exists = c.fetchone()
            conn.close()
            if not user_exists:
                flash('El usuario no existe', 'danger')
            else:
                flash('Contraseña incorrecta', 'danger')
            return render_template('login.html')
        conn.close()
        session['user_id'] = user['Id_usuario']
        session['Usuario'] = Usuario
        return redirect(url_for('principal'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        Usuario = request.form.get('Usuario')
        Contrasena = request.form.get('Contrasena')
        Nombre = request.form.get('Nombre')
        Palabra_clave = request.form.get('Palabra_clave')
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute('INSERT INTO Usuarios (Nombre, Usuario, Contrasena, Palabra_clave, Estado, Tipo_usuario, Permisos) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (Nombre, Usuario, Contrasena, Palabra_clave, 'Activo', 'Cliente', 'N'))
            conn.commit()
            flash('Usuario registrado correctamente', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El usuario ya existe', 'danger')
        finally:
            conn.close()
    return render_template('registro.html')

@app.route('/ingresos', methods=['GET', 'POST'])
def ingresos():
    if request.method == 'POST':
        Tipo_persona = request.form.get('Tipo_persona')
        Sueldo_1 = request.form.get('Sueldo_1')
        Sueldo_2 = request.form.get('Sueldo_2')
        Ingresos_adicionales = request.form.get('Ingresos_adicionales')
        Periodo = request.form.get('Periodo')
        Frecuencia_pago = request.form.get('Frecuencia_pago')
        Ahorro = request.form.get('Ahorro')
        Cuanto_ahorrar = request.form.get('Cuanto_ahorrar')
        Inversion = request.form.get('Inversion')
        Cuanto_invertir = request.form.get('Cuanto_invertir')
        Deudas = request.form.get('Deudas')
        Id_usuario = session.get('Id_usuario')

        # Validación para evitar errores de integridad
        if Tipo_persona not in ['P', 'F']:
            flash('Debes seleccionar un tipo de persona válido.')
            return render_template('ingresos.html', nombre_usuario=session.get('Nombre', 'Usuario'))
        if Deudas not in ['S', 'N']:
            flash('Debes seleccionar una opción válida para deudas.')
            return render_template('ingresos.html', nombre_usuario=session.get('Nombre', 'Usuario'))

        # Guarda los ingresos en la base de datos
        conn = sqlite3.connect('presupuesto.db')
        c = conn.cursor()
        c.execute('''INSERT INTO Ingresos 
            (Id_usuario, Sueldo_1, Sueldo_2, Ingresos_adicionales, Periodo, Tipo_persona, Ahorro, Cuanto_ahorrar, Inversion, Cuanto_invertir, Frecuencia_pago, Deudas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (Id_usuario, Sueldo_1, Sueldo_2, Ingresos_adicionales, Periodo, Tipo_persona, Ahorro, Cuanto_ahorrar, Inversion, Cuanto_invertir, Frecuencia_pago, Deudas))
        conn.commit()
        conn.close()

        # Redirige según la opción de Deudas
        if Deudas == "S":
            session['mostrar_formulario_deuda'] = True
            return redirect(url_for('deudas'))
        else:
            flash('Ingresos guardados correctamente')
            return redirect(url_for('principal'))

    nombre_usuario = session.get('Nombre', 'Usuario')
    return render_template('ingresos.html', nombre_usuario=nombre_usuario)

@app.route('/principal')
def principal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Mostrar formulario de ingresos solo la primera vez
    if not session.get('ingresos_registrados'):
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT 1 FROM Ingresos WHERE Id_usuario=?', (session['user_id'],))
        existe = c.fetchone()
        conn.close()
        if not existe:
            return redirect(url_for('ingresos'))
        else:
            session['ingresos_registrados'] = True
    return render_template('principal.html', username=session['Usuario'])

@app.route('/gastos', methods=['GET', 'POST'])
def gastos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    if request.method == 'POST':
        Fecha = request.form.get('Fecha')
        Descripcion = request.form.get('Descripcion')
        Valor = request.form.get('Valor')
        Id_categoria = request.form.get('Id_categoria')
        Id_subcategoria = request.form.get('Id_subcategoria')
        c.execute('INSERT INTO Gastos (Id_usuario, Fecha, Descripcion, Valor, Id_categoria, Id_subcategoria) VALUES (?, ?, ?, ?, ?, ?)',
                  (session['user_id'], Fecha, Descripcion, Valor, Id_categoria, Id_subcategoria))
        conn.commit()
        flash('Gasto agregado correctamente', 'success')
    c.execute('SELECT Fecha, Descripcion, Valor FROM Gastos WHERE Id_usuario=? ORDER BY Fecha', (session['user_id'],))
    gastos = c.fetchall()
    conn.close()
    return render_template('gastos.html', gastos=gastos)

@app.route('/presupuesto', methods=['GET', 'POST'])
def presupuesto():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    if request.method == 'POST':
        Periodo = request.form.get('Periodo')
        Descripcion = request.form.get('Descripcion')
        Fecha_pago = request.form.get('Fecha_pago')
        Id_categoria = request.form.get('Id_categoria')
        Id_subcategoria = request.form.get('Id_subcategoria')
        Tipo_gasto = request.form.get('Tipo_gasto')
        Valor = request.form.get('Valor')
        c.execute('INSERT INTO Presupuesto (Id_usuario, Periodo, Descripcion, Fecha_pago, Id_categoria, Id_subcategoria, Tipo_gasto, Valor) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  (session['user_id'], Periodo, Descripcion, Fecha_pago, Id_categoria, Id_subcategoria, Tipo_gasto, Valor))
        conn.commit()
        flash('Presupuesto agregado correctamente', 'success')
    c.execute('SELECT Periodo, Descripcion, Valor FROM Presupuesto WHERE Id_usuario=? ORDER BY Periodo', (session['user_id'],))
    presupuestos = c.fetchall()
    conn.close()
    return render_template('presupuesto.html', presupuestos=presupuestos)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Funciones para gráficos ---
def get_gastos(user_id):
    conn = get_db()
    df = pd.read_sql_query("SELECT fecha, monto, descripcion FROM gastos WHERE user_id=? ORDER BY fecha", conn, params=(user_id,))
    conn.close()
    return df

def mostrar_graficas(df, ax):
    ax[0].clear()
    ax[1].clear()
    if not df.empty:
        df['fecha'] = pd.to_datetime(df['fecha'])
        # Gasto diario
        diario = df.groupby('fecha')['monto'].sum()
        diario.plot(kind='bar', ax=ax[0], title="Gasto Diario")
        # Gasto mensual
        df['mes'] = df['fecha'].dt.to_period('M')
        mensual = df.groupby('mes')['monto'].sum()
        mensual.plot(kind='bar', ax=ax[1], title="Gasto Mensual")

@app.route('/graficos')
def graficos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    df = get_gastos(session['user_id'])
    fig, ax = plt.subplots(1, 2, figsize=(8, 3))
    mostrar_graficas(df, ax)
    plt.tight_layout()
    # Guardar la figura
    fig.savefig('static/graficos/grafico.png')
    return render_template('graficos.html', url='static/graficos/grafico.png')

@app.route('/deudas', methods=['GET', 'POST'])
def deudas():
    if request.method == 'POST':
        Id_usuario = session.get('Id_usuario')
        descripcion = request.form.get('descripcion')
        entidad = request.form.get('entidad')
        valor_actual = request.form.get('valor_actual')
        valor_cuota = request.form.get('valor_cuota')
        cuotas = request.form.get('cuotas')
        interes = request.form.get('interes')

        # Validación antes de insertar
        try:
            if (not descripcion or not entidad or
                float(valor_actual) <= 0 or float(valor_cuota) <= 0 or
                int(cuotas) <= 0 or float(interes) < 0):
                flash('Todos los campos son obligatorios y deben tener valores válidos.')
                return render_template('deudas.html')

            conn = sqlite3.connect('presupuesto.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO Deudas 
                (Id_usuario, Descripcion, Entidad, Valor_actual, Valor_cuota, Cuotas, Interes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (Id_usuario, descripcion, entidad, valor_actual, valor_cuota, cuotas, interes))
            conn.commit()
            conn.close()
            flash('Deuda registrada correctamente')
            return redirect(url_for('ver_deudas'))
        except Exception as e:
            flash(f'Error al registrar la deuda: {e}')
            return render_template('deudas.html')

    return render_template('deudas.html')

@app.route('/ver_deudas')
def ver_deudas():
    Id_usuario = session.get('Id_usuario')
    if not Id_usuario:
        flash('Debes iniciar sesión para ver tus deudas.')
        return redirect(url_for('login'))

    conn = sqlite3.connect('presupuesto.db')
    c = conn.cursor()
    c.execute('''
        SELECT Descripcion, Entidad, Valor, Valor_cuota, Cuotas, Interes
        FROM Deudas
        WHERE Id_usuario = ?
    ''', (Id_usuario,))
    deudas = c.fetchall()
    conn.close()

    labels = [d[0] for d in deudas]
    data = [d[2] for d in deudas]

    return render_template('ver_deudas.html', deudas=deudas, labels=labels, data=data)

# --- Main ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)

