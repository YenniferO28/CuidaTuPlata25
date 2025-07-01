from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# --- Configuración de la base de datos ---
DB_PATH = os.path.join(os.path.dirname(__file__), 'presupuesto.db')
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Rutas principales ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        Usuario = request.form['Usuario']
        Contrasena = request.form['Contrasena']
        with get_db() as conn:
            c = conn.cursor()
            c.execute('SELECT Id_usuario, Nombre FROM Usuarios WHERE Usuario=? AND Contrasena=?', (Usuario, Contrasena))
            user = c.fetchone()
            if not user:
                c.execute('SELECT Id_usuario FROM Usuarios WHERE Usuario=?', (Usuario,))
                user_exists = c.fetchone()
                if not user_exists:
                    flash('El usuario no existe', 'danger')
                else:
                    flash('Contraseña incorrecta', 'danger')
                return render_template('login.html')
            session['user_id'] = user['Id_usuario']
            session['Nombre'] = user['Nombre']
            session['Usuario'] = Usuario

        # --- Lógica para primer ingreso ---
        with get_db() as conn:
            c = conn.cursor()
            c.execute('SELECT 1 FROM Ingresos WHERE Id_usuario=?', (user['Id_usuario'],))
            tiene_ingresos = c.fetchone()
        if not tiene_ingresos:
            return redirect(url_for('ingresos'))
        return redirect(url_for('principal'))
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        usuario = request.form.get('usuario')
        contrasena = request.form.get('contrasena')
        palabra_clave = request.form.get('palabra_clave')
        if not all([nombre, usuario, contrasena, palabra_clave]):
            flash('Todos los campos son obligatorios')
            return render_template('registro.html')
        estado = 'Activo'
        tipo_usuario = 'Cliente'
        permisos = 'N'
        fecha_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            with get_db() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO Usuarios (Nombre, Usuario, Contrasena, Palabra_clave, Estado, Tipo_usuario, Permisos, Fecha_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (nombre, usuario, contrasena, palabra_clave, estado, tipo_usuario, permisos, fecha_registro))
                conn.commit()
        except sqlite3.IntegrityError:
            flash('El usuario ya existe. Elige otro nombre de usuario.')
            return render_template('registro.html')
        flash('Usuario registrado correctamente')
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/ingresos', methods=['GET', 'POST'])
def ingresos():
    if request.method == 'POST':
        Tipo_persona = request.form.get('Tipo_persona')
        Sueldo_1 = request.form.get('Sueldo_1', 0)
        Sueldo_2 = request.form.get('Sueldo_2', 0)
        Ingresos_adicionales = request.form.get('Ingresos_adicionales', 0)
        Periodo = request.form.get('Periodo')
        Frecuencia_pago = request.form.get('Frecuencia_pago')
        Deudas = request.form.get('Deudas')
        Id_usuario = session.get('user_id')

        # Solo tomamos el valor numérico si el usuario seleccionó "Si"
        Ahorro = request.form.get('Ahorro', 'No')
        Cuanto_ahorrar = request.form.get('Cuanto_ahorrar', '0')
        Inversion = request.form.get('Inversion', 'No')
        Cuanto_invertir = request.form.get('Cuanto_invertir', '0')

        try:
            ahorro = float(Cuanto_ahorrar) if Ahorro == "Si" and Cuanto_ahorrar.strip() != "" else 0.0
        except (TypeError, ValueError):
            ahorro = 0.0

        try:
            inversion = float(Cuanto_invertir) if Inversion == "Si" and Cuanto_invertir.strip() != "" else 0.0
        except (TypeError, ValueError):
            inversion = 0.0

        with get_db() as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO Ingresos 
                (Id_usuario, Tipo_persona, Sueldo_1, Sueldo_2, Ingresos_adicionales, Periodo, Frecuencia_pago, Ahorro, Inversion, Deudas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (Id_usuario, Tipo_persona, Sueldo_1, Sueldo_2, Ingresos_adicionales, Periodo, Frecuencia_pago, ahorro, inversion, Deudas))
            conn.commit()
            flash('Ingresos registrados correctamente')
            return redirect(url_for('tabla_presupuesto'))
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
    with get_db() as conn:
        c = conn.cursor()
        hoy = datetime.now()
        mes_actual = hoy.strftime('%m')
        anio_actual = hoy.strftime('%Y')
        c.execute('''
            SELECT SUM(Sueldo_1 + Sueldo_2 + Ingresos_adicionales) as total
            FROM Ingresos
            WHERE Id_usuario=? AND strftime('%Y', Periodo)=? AND strftime('%m', Periodo)=?
        ''', (session['user_id'], anio_actual, mes_actual))
        ingresos_totales = c.fetchone()['total'] or 0

        c.execute('''
            SELECT SUM(Valor)
            FROM Gastos
            WHERE Id_usuario=? AND strftime('%m', Fecha)=? AND strftime('%Y', Fecha)=?
        ''', (session['user_id'], mes_actual, anio_actual))
        suma_gastos = c.fetchone()[0] or 0

        c.execute('SELECT Sueldo_1, Sueldo_2, Ingresos_adicionales FROM Ingresos WHERE Id_usuario=?', (session['user_id'],))
        ingresos_row = c.fetchone()
        if ingresos_row:
            ingresos_totales = sum(float(ingresos_row[k] or 0) for k in ['Sueldo_1', 'Sueldo_2', 'Ingresos_adicionales'])
        else:
            ingresos_totales = 0

        c.execute('''
            SELECT SUM(Valor) as total
            FROM Presupuesto
            WHERE Id_usuario=? AND Fecha_pago IS NOT NULL AND
                  strftime('%Y', Fecha_pago) = ? AND strftime('%m', Fecha_pago) = ?
        ''', (session['user_id'], anio_actual, mes_actual))
        suma_presupuesto = c.fetchone()['total'] or 0

        c.execute('''
            SELECT SUM(Valor_actual) as total
            FROM Deudas
            WHERE Id_usuario=?
        ''', (session['user_id'],))
        suma_deudas = c.fetchone()['total'] or 0

        c.execute('''
            SELECT Sueldo_1, Sueldo_2, Ingresos_adicionales
            FROM Ingresos
            WHERE Id_usuario=?
            ORDER BY Id_ingreso DESC
            LIMIT 1
        ''', (session['user_id'],))
        row = c.fetchone()
        if row:
            ultimo_ingreso = sum([row['Sueldo_1'] or 0, row['Sueldo_2'] or 0, row['Ingresos_adicionales'] or 0])
        else:
            ultimo_ingreso = 0

    nombre_usuario = session.get('Nombre', 'Usuario')
    return render_template(
        'principal.html',
        ingresos_totales=ingresos_totales,
        suma_presupuesto=suma_presupuesto,
        suma_gastos=suma_gastos,
        suma_deudas=suma_deudas,
        ultimo_ingreso=ultimo_ingreso,
        nombre_usuario=nombre_usuario
    )

@app.route('/gastos', methods=['GET', 'POST'])
def gastos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT Id_categoria, Categoria_principal FROM Categoria')
        categorias = c.fetchall()
        c.execute('SELECT Id_subcategoria, Nombre, Id_categoria FROM Subcategoria')
        subcategorias = c.fetchall()
        if request.method == 'POST':
            Fecha = request.form.get('Fecha')
            Descripcion = request.form.get('Descripcion')
            Valor = request.form.get('Valor')
            Id_categoria = request.form.get('Id_categoria')
            Id_subcategoria = request.form.get('Id_subcategoria')   
            c.execute('INSERT INTO Gastos (Id_usuario, Fecha, Descripcion, Valor, Id_categoria, Id_subcategoria) VALUES (?, ?, ?, ?, ?, ?)',
                      (session['user_id'], Fecha, Descripcion, Valor, Id_categoria, Id_subcategoria))
            conn.commit()
            flash('Gasto guardado correctamente')
            return redirect(url_for('tabla_gastos'))
    return render_template('gastos.html', categorias=categorias, subcategorias=subcategorias)

@app.route('/presupuesto', methods=['GET', 'POST'])
def presupuesto():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT Id_categoria, Categoria_principal FROM Categoria WHERE Id_categoria != 11')
        categorias = c.fetchall()
        c.execute('SELECT Id_subcategoria, Nombre, Id_categoria FROM Subcategoria WHERE Id_categoria != 11')
        subcategorias = c.fetchall()
        if request.method == 'POST':
            Periodo = request.form.get('Periodo')
            Descripcion = request.form.get('Descripcion')
            Fecha_pago = request.form.get('Fecha_pago')
            Id_categoria = request.form.get('Id_categoria')
            Id_subcategoria = request.form.get('Id_subcategoria')
            Tipo_gasto = request.form.get('Tipo_gasto')
            Valor = request.form.get('Valor')
            c.execute('SELECT MAX(Secuencial) FROM Presupuesto WHERE Id_usuario=?', (session['user_id'],))
            max_secuencial = c.fetchone()[0]
            Secuencial = (max_secuencial + 1) if max_secuencial else 1
            c.execute('''INSERT INTO Presupuesto 
                (Id_usuario, Secuencial, Periodo, Descripcion, Fecha_pago, Id_categoria, Id_subcategoria, Tipo_gasto, Valor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (session['user_id'], Secuencial, Periodo, Descripcion, Fecha_pago, Id_categoria, Id_subcategoria, Tipo_gasto, Valor))
            conn.commit()
            flash('Presupuesto registrado correctamente')
            return redirect(url_for('tabla_presupuesto'))  # Redirige al resumen después de guardar
        # Si es GET, muestra el formulario:
        return render_template('presupuesto.html', categorias=categorias, subcategorias=subcategorias)

@app.route('/deudas', methods=['GET', 'POST'])
def deudas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT Id_categoria, Categoria_principal FROM Categoria')
        categorias = c.fetchall()
        c.execute('SELECT Id_subcategoria, Nombre, Id_categoria FROM Subcategoria')
        subcategorias = c.fetchall()
        if request.method == 'POST':
            Descripcion = request.form.get('descripcion')
            Entidad = request.form.get('Entidad')
            Valor_actual = request.form.get('Valor_actual')
            Cuotas_pendientes = request.form.get('Cuotas_pendientes')
            Valor_cuota = request.form.get('Valor_cuota')
            Interes = request.form.get('Interes')
            Id_categoria = request.form.get('Id_categoria')
            Id_subcategoria = request.form.get('Id_subcategoria')
            c.execute('''INSERT INTO Deudas 
                (Id_usuario, Descripcion, Entidad, Valor_actual, Cuotas_pendientes, Valor_cuota, Interes, Id_categoria, Id_subcategoria)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (session['user_id'], Descripcion, Entidad, Valor_actual, Cuotas_pendientes, Valor_cuota, Interes, Id_categoria, Id_subcategoria))
            conn.commit()
            flash('Deuda registrada correctamente')
            return redirect(url_for('ver_deudas'))
    return render_template('deudas.html', categorias=categorias, subcategorias=subcategorias)

@app.route('/ver_deudas')
def ver_deudas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT d.Descripcion, d.Entidad, d.Valor_actual, d.Valor_cuota, d.Cuotas_pendientes, d.Interes,
                   c.Categoria_principal AS Categoria, s.Nombre AS Subcategoria
            FROM Deudas d
            LEFT JOIN Categoria c ON d.Id_categoria = c.Id_categoria
            LEFT JOIN Subcategoria s ON d.Id_subcategoria = s.Id_subcategoria
            WHERE d.Id_usuario=?
        ''', (session['user_id'],))
        deudas_rows = c.fetchall()
        deudas = [dict(d) for d in deudas_rows]

        from collections import defaultdict
        subcat_suma = defaultdict(float)
        for d in deudas:
            subcat = d['Subcategoria'] or 'Sin subcategoría'
            subcat_suma[subcat] += d['Valor_actual']

        labels = list(subcat_suma.keys())
        data = list(subcat_suma.values())
        subcategorias = labels

    return render_template(
        'ver_deudas.html',
        deudas=deudas,
        labels=labels,
        data=data,
        subcategorias=subcategorias
    )

@app.route('/get_subcategorias/<int:categoria_id>')
def get_subcategorias(categoria_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT Id_subcategoria, Nombre FROM Subcategoria WHERE Id_categoria=?', (categoria_id,))
        subcategorias = [{'id': row['Id_subcategoria'], 'nombre': row['Nombre']} for row in c.fetchall()]
    return jsonify(subcategorias)

@app.route('/tabla_gastos')
def tabla_gastos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                g.Fecha, 
                g.Descripcion, 
                c.Categoria_principal AS Categoria, 
                s.Nombre AS Subcategoria, 
                g.Valor
            FROM Gastos g
            LEFT JOIN Categoria c ON g.Id_categoria = c.Id_categoria
            LEFT JOIN Subcategoria s ON g.Id_subcategoria = s.Id_subcategoria
            WHERE g.Id_usuario=?
        ''', (session['user_id'],))
        gastos_rows = c.fetchall()
        gastos = [dict(g) for g in gastos_rows]

        from collections import defaultdict
        categoria_suma = defaultdict(float)
        for g in gastos:
            categoria = g['Categoria'] or 'Sin categoría'
            categoria_suma[categoria] += g['Valor']

        labels = list(categoria_suma.keys())
        data = list(categoria_suma.values())
        subcategorias = labels

    return render_template(
        'tabla_gastos.html',
        gastos=gastos,
        labels=labels,
        data=data,
        subcategorias=subcategorias
    )

@app.route('/tabla_presupuesto')
def tabla_presupuesto():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT Sueldo_1, Sueldo_2, Ingresos_adicionales
            FROM Ingresos
            WHERE Id_usuario=?
            ORDER BY Id_ingreso DESC
            LIMIT 1
        ''', (session['user_id'],))
        row = c.fetchone()
        if row:
            ultimo_ingreso = sum([row['Sueldo_1'] or 0, row['Sueldo_2'] or 0, row['Ingresos_adicionales'] or 0])
        else:
            ultimo_ingreso = 0

        hoy = datetime.now()
        mes_actual = hoy.strftime('%m')
        anio_actual = hoy.strftime('%Y')
        c.execute('''
            SELECT SUM(Valor) as total
            FROM Presupuesto
            WHERE Id_usuario=? AND Fecha_pago IS NOT NULL AND
                  strftime('%Y', Fecha_pago) = ? AND strftime('%m', Fecha_pago) = ?
        ''', (session['user_id'], anio_actual, mes_actual))
        suma_presupuesto = c.fetchone()['total'] or 0

        c.execute('''
            SELECT SUM(Valor_actual) as total
            FROM Deudas
            WHERE Id_usuario=?
        ''', (session['user_id'],))
        suma_deudas = c.fetchone()['total'] or 0

        c.execute('''
            SELECT c.Categoria_principal AS Categoria, SUM(p.Valor) as total
            FROM Presupuesto p
            LEFT JOIN Categoria c ON p.Id_categoria = c.Id_categoria
            WHERE p.Id_usuario=? AND p.Fecha_pago IS NOT NULL AND
                  strftime('%Y', p.Fecha_pago) = ? AND strftime('%m', p.Fecha_pago) = ?
            GROUP BY c.Categoria_principal
        ''', (session['user_id'], anio_actual, mes_actual))
        rows = c.fetchall()
        labels = [row['Categoria'] or 'Sin categoría' for row in rows]
        data = [row['total'] for row in rows]
        subcategorias = [str(l) for l in labels]  # <-- Asegura que sea lista de strings

        c.execute('SELECT Ahorro, Inversion FROM Ingresos WHERE Id_usuario=?', (session['user_id'],))
        ahorro_inversion = c.fetchone()
        valor_ahorro = safe_float(ahorro_inversion['Ahorro'])
        valor_inversion = safe_float(ahorro_inversion['Inversion'])
        ingreso_disponible = 0
        porcentaje_ahorro = 0
        porcentaje_inversion = 0

        if suma_presupuesto > 0 and ultimo_ingreso > 0:
            for i, categoria in enumerate(labels):
                if categoria.lower() == "ahorro":
                    valor_ahorro = float(data[i])
                elif categoria.lower() == "inversión":
                    valor_inversion = float(data[i])
            ingreso_disponible = float(ultimo_ingreso) - float(suma_presupuesto)
            porcentaje_ahorro = (valor_ahorro / float(ultimo_ingreso)) * 100 if float(ultimo_ingreso) else 0
            porcentaje_inversion = (valor_inversion / float(ultimo_ingreso)) * 100 if float(ultimo_ingreso) else 0
        else:
            ingreso_disponible = float(ultimo_ingreso) - float(suma_presupuesto)

    # Obtener la lista de presupuestos para mostrar en la tabla
    c.execute('''
        SELECT p.Descripcion, p.Fecha_pago, c.Categoria_principal AS Categoria, s.Nombre AS Subcategoria, 
               p.Tipo_gasto, p.Valor
        FROM Presupuesto p
        LEFT JOIN Categoria c ON p.Id_categoria = c.Id_categoria
        LEFT JOIN Subcategoria s ON p.Id_subcategoria = s.Id_subcategoria
        WHERE p.Id_usuario=?
    ''', (session['user_id'],))
    presupuestos = c.fetchall()

    nombre_usuario = session.get('Nombre', 'Usuario')
    return render_template(
        'tabla_presupuesto.html',
        presupuesto=presupuestos,
        ultimo_ingreso=ultimo_ingreso,
        suma_presupuesto=suma_presupuesto,
        suma_deudas=suma_deudas,
        nombre_usuario=nombre_usuario,
        labels=labels,
        data=data,
        subcategorias=subcategorias,  # <-- Ahora es lista de strings
        porcentaje_ahorro=porcentaje_ahorro,
        porcentaje_inversion=porcentaje_inversion,
        valor_ahorro=valor_ahorro,
        valor_inversion=valor_inversion,
        ingreso_disponible=ingreso_disponible,
        mes_actual=mes_actual,
        anio_actual=anio_actual,
        saldo_disponible=ingreso_disponible
    )

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.')
    return redirect(url_for('login'))

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

# Puedes agregar aquí más rutas según lo necesites

if __name__ == '__main__':
    app.run(debug=True)

