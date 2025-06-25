from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- Configuración de la base de datos ---
DB_PATH = os.path.join(os.path.dirname(__file__), 'presupuesto.db')
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
        c.execute('SELECT Id_usuario, Nombre FROM Usuarios WHERE Usuario=? AND Contrasena=?', (Usuario, Contrasena))
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
        session['Nombre'] = user['Nombre']
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
        Inversion = request.form.get('Inversion')
        Deudas = request.form.get('Deudas')
        Id_usuario = session.get('user_id')

        # Validación para evitar errores de integridad
        if Tipo_persona not in ['P', 'F']:
            flash('Debes seleccionar un tipo de persona válido.')
            return render_template('ingresos.html', nombre_usuario=session.get('Nombre', 'Usuario'))
        if Deudas not in ['S', 'N']:
            flash('Debes seleccionar una opción válida para deudas.')
            return render_template('ingresos.html', nombre_usuario=session.get('Nombre', 'Usuario'))

        # Guarda los ingresos en la base de datos
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO Ingresos 
            (Id_usuario, Sueldo_1, Sueldo_2, Ingresos_adicionales, Periodo, Tipo_persona, Ahorro, Inversion, Frecuencia_pago, Deudas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (Id_usuario, Sueldo_1, Sueldo_2, Ingresos_adicionales, Periodo, Tipo_persona, Ahorro, Inversion, Frecuencia_pago, Deudas))
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
        flash('Gasto registrado correctamente')
    # Mostrar gastos del usuario
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
        # Calcular el secuencial (puedes mejorarlo según tu lógica)
        c.execute('SELECT MAX(Secuencial) FROM Presupuesto WHERE Id_usuario=?', (session['user_id'],))
        max_secuencial = c.fetchone()[0]
        Secuencial = (max_secuencial + 1) if max_secuencial else 1
        c.execute('''INSERT INTO Presupuesto 
            (Id_usuario, Secuencial, Periodo, Descripcion, Fecha_pago, Id_categoria, Id_subcategoria, Tipo_gasto, Valor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (session['user_id'], Secuencial, Periodo, Descripcion, Fecha_pago, Id_categoria, Id_subcategoria, Tipo_gasto, Valor))
        conn.commit()
        flash('Presupuesto registrado correctamente')
    # Mostrar presupuestos del usuario
    c.execute('SELECT * FROM Presupuesto WHERE Id_usuario=? ORDER BY Fecha_pago', (session['user_id'],))
    presupuestos = c.fetchall()
    conn.close()
    return render_template('presupuesto.html', presupuestos=presupuestos)

@app.route('/deudas', methods=['GET', 'POST'])
def deudas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    if request.method == 'POST':
        Descripcion = request.form.get('descripcion')  # <-- minúscula
        Entidad = request.form.get('Entidad')
        Valor_actual = request.form.get('Valor_actual')
        Cuotas_pendientes = request.form.get('Cuotas_pendientes')
        Valor_cuota = request.form.get('Valor_cuota')
        Interes = request.form.get('Interes')
        c.execute('''INSERT INTO Deudas 
            (Id_usuario, Descripcion, Entidad, Valor_actual, Cuotas_pendientes, Valor_cuota, Interes)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (session['user_id'], Descripcion, Entidad, Valor_actual, Cuotas_pendientes, Valor_cuota, Interes))
        conn.commit()
        flash('Deuda registrada correctamente')
    # Mostrar deudas del usuario
    c.execute('SELECT * FROM Deudas WHERE Id_usuario=?', (session['user_id'],))
    deudas = c.fetchall()
    conn.close()
    return render_template('deudas.html', deudas=deudas)

@app.route('/ver_deudas')
def ver_deudas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT Descripcion, Entidad, Valor_actual, Valor_cuota, Cuotas_pendientes, Interes FROM Deudas WHERE Id_usuario=?', (session['user_id'],))
    deudas = c.fetchall()
    labels = [d['Descripcion'] for d in deudas]
    data = [d['Valor_actual'] for d in deudas]
    conn.close()
    return render_template('ver_deudas.html', deudas=deudas, labels=labels, data=data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/get_subcategorias/<int:categoria_id>')
def get_subcategorias(categoria_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT Id_subcategoria, Subcategoria FROM Subcategoria WHERE Id_categoria=?', (categoria_id,))
    subcategorias = [{'id': row['Id_subcategoria'], 'nombre': row['Subcategoria']} for row in c.fetchall()]
    conn.close()
    return jsonify(subcategorias)

# Puedes agregar aquí más rutas según lo necesites

if __name__ == '__main__':
    app.run(debug=True)

