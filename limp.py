import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'presupuesto.db')

def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()
    c.execute("SELECT Id_ingreso, Ahorro, Inversion FROM Ingresos")
    rows = c.fetchall()
    for row in rows:
        id_ingreso, ahorro, inversion = row
        nuevo_ahorro = safe_float(ahorro)
        nuevo_inversion = safe_float(inversion)
        c.execute(
            "UPDATE Ingresos SET Ahorro=?, Inversion=? WHERE Id_ingreso=?",
            (nuevo_ahorro, nuevo_inversion, id_ingreso)
        )
    conn.commit()
print("¡Datos de Ahorro e Inversion limpiados correctamente!")