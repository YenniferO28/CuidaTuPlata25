from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from datetime import datetime

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

        # --- Lógica para primer ingreso ---
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT 1 FROM Ingresos WHERE Id_usuario=?', (user['Id_usuario'],))
        tiene_ingresos = c.fetchone()
        conn.close()
        if not tiene_ingresos:
            # Si NO tiene ingresos registrados, va a la pantalla de ingresos
            return redirect(url_for('ingresos'))
        # Si ya tiene ingresos, va a la pantalla principal
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

        conn = get_db()
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO Usuarios (Nombre, Usuario, Contrasena, Palabra_clave, Estado, Tipo_usuario, Permisos, Fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, usuario, contrasena, palabra_clave, estado, tipo_usuario, permisos, fecha_registro))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('El usuario ya existe. Elige otro nombre de usuario.')
            return render_template('registro.html')
        conn.close()
        flash('Usuario registrado correctamente')
        return redirect(url_for('login'))
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
        Ahorro = request.form.get('Ahorro', 0)  # Este será el valor numérico
        Inversion = request.form.get('Inversion', 0)  # Este será el valor numérico
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

        # Asegúrate de convertirlos a float antes de guardar
        try:
            ahorro = float(Ahorro)
        except (TypeError, ValueError):
            ahorro = 0.0

        try:
            inversion = float(Inversion)
        except (TypeError, ValueError):
            inversion = 0.0

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
    conn = get_db()
    c = conn.cursor()
    hoy = datetime.now()
    mes_actual = hoy.strftime('%m')
    anio_actual = hoy.strftime('%Y')
    # Suma de ingresos del mes actual
    c.execute('''
        SELECT SUM(Sueldo_1 + Sueldo_2 + Ingresos_adicionales) as total
        FROM Ingresos
        WHERE Id_usuario=? AND strftime('%Y', Periodo)=? AND strftime('%m', Periodo)=?
    ''', (session['user_id'], anio_actual, mes_actual))
    ingresos_totales = c.fetchone()['total'] or 0

    # Suma de gastos del mes actual
    c.execute('''
        SELECT SUM(Valor)
        FROM Gastos
        WHERE Id_usuario=? AND strftime('%m', Fecha)=? AND strftime('%Y', Fecha)=?
    ''', (session['user_id'], mes_actual, anio_actual))
    suma_gastos = c.fetchone()[0] or 0

    # Calcula los totales:
    # Traer ingresos
    c.execute('SELECT Sueldo_1, Sueldo_2, Ingresos_adicionales FROM Ingresos WHERE Id_usuario=?', (session['user_id'],))
    ingresos_row = c.fetchone()
    if ingresos_row:
        ingresos_totales = sum(float(ingresos_row[k] or 0) for k in ['Sueldo_1', 'Sueldo_2', 'Ingresos_adicionales'])
    else:
        ingresos_totales = 0

    # Suma el presupuesto del mes
    c.execute('''
        SELECT SUM(Valor) as total
        FROM Presupuesto
        WHERE Id_usuario=? AND Fecha_pago IS NOT NULL AND
              strftime('%Y', Fecha_pago) = ? AND strftime('%m', Fecha_pago) = ?
    ''', (session['user_id'], anio_actual, mes_actual))
    suma_presupuesto = c.fetchone()['total'] or 0

    # Suma las deudas activas
    c.execute('''
        SELECT SUM(Valor_actual) as total
        FROM Deudas
        WHERE Id_usuario=?
    ''', (session['user_id'],))
    suma_deudas = c.fetchone()['total'] or 0
        # Obtener el último registro de ingresos
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
    conn.close()
    nombre_usuario = session.get('Nombre', 'Usuario')  # <-- Cambia aquí
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
    conn = get_db()
    c = conn.cursor()
    # Traer categorías
    c.execute('SELECT Id_categoria, Categoria_principal FROM Categoria')
    categorias = c.fetchall()
    # Traer subcategorías
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
    conn.close()
    return render_template('gastos.html', categorias=categorias, subcategorias=subcategorias)

@app.route('/presupuesto', methods=['GET', 'POST'])
def presupuesto():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    # Traer todas las categorías menos la 11
    c.execute('SELECT Id_categoria, Categoria_principal FROM Categoria WHERE Id_categoria != 11')
    categorias = c.fetchall()
    # Traer subcategorías solo de esas categorías
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
    c.execute('''
        SELECT p.Descripcion, p.Fecha_pago, c.Categoria_principal AS Categoria, s.Nombre AS Subcategoria, 
               p.Tipo_gasto, p.Valor
        FROM Presupuesto p
        LEFT JOIN Categoria c ON p.Id_categoria = c.Id_categoria
        LEFT JOIN Subcategoria s ON p.Id_subcategoria = s.Id_subcategoria
        WHERE p.Id_usuario=?
    ''', (session['user_id'],))
    presupuestos = c.fetchall()
    conn.close()
    return render_template('presupuesto.html', categorias=categorias, subcategorias=subcategorias, presupuestos=presupuestos)

@app.route('/deudas', methods=['GET', 'POST'])
def deudas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    # Traer categorías y subcategorías para el formulario
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
    conn.close()
    return render_template('deudas.html', categorias=categorias, subcategorias=subcategorias)

@app.route('/ver_deudas')
def ver_deudas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
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

    # Agrupar por subcategoría
    from collections import defaultdict
    subcat_suma = defaultdict(float)
    for d in deudas:
        subcat = d['Subcategoria'] or 'Sin subcategoría'
        subcat_suma[subcat] += d['Valor_actual']

    labels = list(subcat_suma.keys())
    data = list(subcat_suma.values())
    subcategorias = labels  # Para compatibilidad con el template

    conn.close()
    return render_template(
        'ver_deudas.html',
        deudas=deudas,
        labels=labels,
        data=data,
        subcategorias=subcategorias
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/get_subcategorias/<int:categoria_id>')
def get_subcategorias(categoria_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT Id_subcategoria, Nombre FROM Subcategoria WHERE Id_categoria=?', (categoria_id,))
    subcategorias = [{'id': row['Id_subcategoria'], 'nombre': row['Nombre']} for row in c.fetchall()]
    conn.close()
    return jsonify(subcategorias)

@app.route('/tabla_gastos')
def tabla_gastos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    # Traer todos los gastos para la tabla
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

    # Agrupar por categoría
    from collections import defaultdict
    categoria_suma = defaultdict(float)
    for g in gastos:
        categoria = g['Categoria'] or 'Sin categoría'
        categoria_suma[categoria] += g['Valor']

    labels = list(categoria_suma.keys())
    data = list(categoria_suma.values())

    subcategorias = labels  # Para mantener compatibilidad con el template

    conn.close()
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
    conn = get_db()
    c = conn.cursor()
    # Obtener el último registro de ingresos
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

    # Suma el presupuesto del mes
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

    # Suma las deudas activas
    c.execute('''
        SELECT SUM(Valor_actual) as total
        FROM Deudas
        WHERE Id_usuario=?
    ''', (session['user_id'],))
    suma_deudas = c.fetchone()['total'] or 0
        # Agrupar el presupuesto del mes por categoría para el gráfico de torta
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
    subcategorias = labels  # Para compatibilidad con el template

    # Calcular porcentajes y valores de ahorro e inversión
    c.execute('SELECT Ahorro, Inversion FROM Ingresos WHERE Id_usuario=?', (session['user_id'],))
    ahorro_inversion = c.fetchone()
    valor_ahorro = float(ahorro_inversion['Ahorro'] or 0)
    valor_inversion = float(ahorro_inversion['Inversion'] or 0)
    ingreso_disponible = 0
    porcentaje_ahorro = 0
    porcentaje_inversion = 0

    # Calcula los valores si tienes datos
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

    conn.close()
    nombre_usuario = session.get('Nombre', 'Usuario')  # <-- Cambia aquí
    return render_template(
        'tabla_presupuesto.html',
        ultimo_ingreso=ultimo_ingreso,
        suma_presupuesto=suma_presupuesto,
        suma_deudas=suma_deudas,
        nombre_usuario=nombre_usuario,
        labels=labels,
        data=data,
        subcategorias=subcategorias,
        porcentaje_ahorro=porcentaje_ahorro,
        porcentaje_inversion=porcentaje_inversion,
        valor_ahorro=valor_ahorro,
        valor_inversion=valor_inversion,
        ingreso_disponible=ingreso_disponible,
    )

# Puedes agregar aquí más rutas según lo necesites

if __name__ == '__main__':
    app.run(debug=True)

