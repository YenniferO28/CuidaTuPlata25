BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Categoria" (
	"Id_categoria"	INTEGER,
	"Categoria_principal"	TEXT,
	PRIMARY KEY("Id_categoria" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Deudas" (
	"Id_deuda"	INTEGER,
	"Id_usuario"	INTEGER,
	"Descripcion"	TEXT,
	"Entidad"	TEXT,
	"Valor_actual"	REAL,
	"Cuotas_pendientes"	INTEGER,
	"Valor_cuota"	REAL,
	"Interes"	REAL,
	PRIMARY KEY("Id_deuda" AUTOINCREMENT),
	FOREIGN KEY("Id_usuario") REFERENCES "Usuarios"("Id_usuario")
);
CREATE TABLE IF NOT EXISTS "Gastos" (
	"Id_tabla"	INTEGER,
	"Id_usuario"	INTEGER,
	"Fecha"	TEXT,
	"Descripcion"	TEXT,
	"Valor"	REAL,
	"Id_categoria"	INTEGER,
	"Id_subcategoria"	INTEGER,
	PRIMARY KEY("Id_tabla" AUTOINCREMENT),
	FOREIGN KEY("Id_categoria") REFERENCES "Categoria"("Id_categoria"),
	FOREIGN KEY("Id_subcategoria") REFERENCES "Subcategoria"("Id_subcategoria"),
	FOREIGN KEY("Id_usuario") REFERENCES "Usuarios"("Id_usuario")
);
CREATE TABLE IF NOT EXISTS "Ingresos" (
	"Id_ingreso"	INTEGER,
	"Id_usuario"	INTEGER,
	"Sueldo_1"	REAL,
	"Sueldo_2"	REAL,
	"Ingresos_adicionales"	REAL,
	"Periodo"	TEXT,
	"Tipo_persona"	TEXT CHECK("Tipo_persona" IN ('P', 'F')),
	"Ahorro"	REAL,
	"Inversion"	REAL,
	"Frecuencia_pago"	TEXT,
	"Deudas"	TEXT CHECK("Deudas" IN ('S', 'N')),
	PRIMARY KEY("Id_ingreso" AUTOINCREMENT),
	FOREIGN KEY("Id_usuario") REFERENCES "Usuarios "("Id_usuario")
);
CREATE TABLE IF NOT EXISTS "Presupuesto" (
	"Id_presupuesto"	INTEGER,
	"Id_usuario"	INTEGER,
	"Secuencial"	INTEGER,
	"Periodo"	TEXT,
	"Descripcion"	TEXT,
	"Fecha_pago"	TEXT,
	"Id_categoria"	INTEGER,
	"Id_subcategoria"	INTEGER,
	"Tipo_gasto"	TEXT CHECK("Tipo_gasto" IN ('Fijo', 'Variable')),
	"Valor"	REAL,
	PRIMARY KEY("Id_presupuesto" AUTOINCREMENT),
	FOREIGN KEY("Id_categoria") REFERENCES "Categoria"("Id_categoria"),
	FOREIGN KEY("Id_subcategoria") REFERENCES "Subcategoria"("Id_subcategoria"),
	FOREIGN KEY("Id_usuario") REFERENCES "Usuarios"("Id_usuario")
);
CREATE TABLE IF NOT EXISTS "Subcategoria" (
	"Id_subcategoria"	INTEGER UNIQUE,
	"Id_categoria"	INTEGER,
	"Nombre"	TEXT,
	PRIMARY KEY("Id_subcategoria" AUTOINCREMENT),
	FOREIGN KEY("Id_categoria") REFERENCES "Categoria"("Id_categoria")
);
CREATE TABLE IF NOT EXISTS "Usuarios" (
	"Id_usuario"	INTEGER,
	"Nombre"	TEXT,
	"Usuario"	TEXT UNIQUE,
	"Contrasena"	TEXT,
	"Palabra_clave"	TEXT,
	"Estado"	TEXT CHECK("Estado" IN ('Activo', 'Inactivo')),
	"Tipo_usuario"	TEXT CHECK("Tipo_usuario" IN ('Administrador', 'Cliente')),
	"Permisos"	TEXT CHECK("Permisos" IN ('S', 'N')),
	PRIMARY KEY("Id_usuario" AUTOINCREMENT)
);
INSERT INTO "Categoria" VALUES (1,'Vivienda');
INSERT INTO "Categoria" VALUES (2,'Salud y Bienestar');
INSERT INTO "Categoria" VALUES (3,'Transporte y Movilidad');
INSERT INTO "Categoria" VALUES (4,'Ropa y Accesorios');
INSERT INTO "Categoria" VALUES (5,'Seguros');
INSERT INTO "Categoria" VALUES (6,'Cuidado Personal y Hogar');
INSERT INTO "Categoria" VALUES (7,'Educación y Desarrollo');
INSERT INTO "Categoria" VALUES (8,'Ocio y Entretenimiento');
INSERT INTO "Categoria" VALUES (9,'Mascotas y Naturaleza');
INSERT INTO "Categoria" VALUES (10,'Gastos Varios');
INSERT INTO "Subcategoria" VALUES (1,1,'Arriendo');
INSERT INTO "Subcategoria" VALUES (2,1,'Mantenimiento y reparaciones');
INSERT INTO "Subcategoria" VALUES (3,1,'Muebles y electrodomésticos');
INSERT INTO "Subcategoria" VALUES (4,1,'Servicios públicos');
INSERT INTO "Subcategoria" VALUES (5,1,'Otros gastos de vivienda');
INSERT INTO "Subcategoria" VALUES (6,2,'Consultas médicas');
INSERT INTO "Subcategoria" VALUES (7,2,'Medicamentos');
INSERT INTO "Subcategoria" VALUES (8,2,'Odontología');
INSERT INTO "Subcategoria" VALUES (9,2,'Otros gastos de salud');
INSERT INTO "Subcategoria" VALUES (10,3,'Combustible');
INSERT INTO "Subcategoria" VALUES (11,3,'Transporte público / Taxis / Apps');
INSERT INTO "Subcategoria" VALUES (12,3,'Reparaciones mecánicas');
INSERT INTO "Subcategoria" VALUES (13,3,'Servicios del vehículo');
INSERT INTO "Subcategoria" VALUES (14,3,'Lavado de vehículo');
INSERT INTO "Subcategoria" VALUES (15,3,'Otros costos de transporte');
INSERT INTO "Subcategoria" VALUES (16,4,'Ropa adultos');
INSERT INTO "Subcategoria" VALUES (17,4,'Ropa niños');
INSERT INTO "Subcategoria" VALUES (18,4,'Calzado');
INSERT INTO "Subcategoria" VALUES (19,4,'Accesorios');
INSERT INTO "Subcategoria" VALUES (20,4,'Otros complementos de moda');
INSERT INTO "Subcategoria" VALUES (21,5,'Vida');
INSERT INTO "Subcategoria" VALUES (22,5,'Salud');
INSERT INTO "Subcategoria" VALUES (23,5,'Vehículo');
INSERT INTO "Subcategoria" VALUES (24,5,'Otros seguros');
INSERT INTO "Subcategoria" VALUES (25,6,'Cosmética / Higiene personal');
INSERT INTO "Subcategoria" VALUES (26,6,'Peluquería y estética');
INSERT INTO "Subcategoria" VALUES (27,6,'Productos de aseo y limpieza');
INSERT INTO "Subcategoria" VALUES (28,6,'Otros servicios personales');
INSERT INTO "Subcategoria" VALUES (29,7,'Cursos / Formación');
INSERT INTO "Subcategoria" VALUES (30,7,'Libros y materiales');
INSERT INTO "Subcategoria" VALUES (31,7,'Suscripciones educativas');
INSERT INTO "Subcategoria" VALUES (32,8,'Cine');
INSERT INTO "Subcategoria" VALUES (33,8,'Deportes (gimnasio, piscina)');
INSERT INTO "Subcategoria" VALUES (34,8,'Pasatiempos');
INSERT INTO "Subcategoria" VALUES (35,8,'Equipos electrónicos');
INSERT INTO "Subcategoria" VALUES (36,8,'Otros gastos recreativos');
INSERT INTO "Subcategoria" VALUES (37,9,'Mascotas (alimento, cuidados)');
INSERT INTO "Subcategoria" VALUES (38,9,'Veterinario');
INSERT INTO "Subcategoria" VALUES (39,10,'Regalos');
INSERT INTO "Subcategoria" VALUES (40,10,'Vacaciones');
INSERT INTO "Subcategoria" VALUES (41,10,'Otros gastos no clasificados');
INSERT INTO "Usuarios" VALUES (1,'Yennifer','yeye28','1234','milo','Activo','Cliente','N');
COMMIT;
