import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "ruta_fria.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de Insumos (Materias primas)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS insumos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT DEFAULT 'General',
        unidad TEXT NOT NULL, -- ml, g, pza, paquete
        costo_unidad REAL NOT NULL, -- Costo por unidad base
        stock_actual REAL NOT NULL,
        stock_minimo REAL DEFAULT 5.0,
        proveedor TEXT,
        fecha_actualizacion TEXT
    )
    """)

    # Tabla de Productos Listos / Bebidas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT DEFAULT 'Bebidas',
        precio_venta REAL NOT NULL,
        costo_calculado REAL DEFAULT 0.0,
        descripcion TEXT,
        activo INTEGER DEFAULT 1
    )
    """)

    # Tabla de Recetas (Insumos requeridos por producto)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recetas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto_id INTEGER NOT NULL,
        insumo_id INTEGER NOT NULL,
        cantidad_requerida REAL NOT NULL,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY (insumo_id) REFERENCES insumos(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Combos / Paquetes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS combos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        precio_regular REAL NOT NULL,
        precio_combo REAL NOT NULL,
        costo_total REAL NOT NULL,
        descuento_porcentaje REAL NOT NULL,
        activo INTEGER DEFAULT 1,
        fecha_creacion TEXT
    )
    """)

    # Tabla de Ítems del Combo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS combo_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        combo_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER DEFAULT 1,
        FOREIGN KEY (combo_id) REFERENCES combos(id) ON DELETE CASCADE,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Ventas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folio TEXT NOT NULL,
        fecha_hora TEXT NOT NULL,
        total_venta REAL NOT NULL,
        costo_total REAL NOT NULL,
        utilidad_neta REAL NOT NULL,
        metodo_pago TEXT DEFAULT 'Efectivo',
        notas TEXT
    )
    """)

    # Tabla de Detalle de Ventas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS venta_detalles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER NOT NULL,
        tipo TEXT NOT NULL, -- 'producto' o 'combo'
        item_id INTEGER NOT NULL,
        nombre_item TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario REAL NOT NULL,
        costo_unitario REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Inversión Inicial y Gastos Fijos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inversiones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT NOT NULL,
        categoria TEXT DEFAULT 'Materia Prima Inicial', -- Materia Prima, Equipamiento, Licencias, Moviliario
        monto REAL NOT NULL,
        fecha TEXT NOT NULL,
        notas TEXT
    )
    """)

    # Tabla de Compras de Insumos (Histórico de Tickets)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compras_historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        insumo_nombre TEXT NOT NULL,
        cantidad_comprada REAL NOT NULL,
        unidad TEXT NOT NULL,
        costo_total REAL NOT NULL,
        proveedor_ticket TEXT
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada correctamente.")
