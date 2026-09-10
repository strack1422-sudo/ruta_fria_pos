from database import get_connection, init_db
from datetime import datetime

def seed_all():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar si ya existen insumos
    cursor.execute("SELECT COUNT(*) FROM insumos")
    if cursor.fetchone()[0] > 0:
        print("La base de datos ya contiene datos iniciales. Omitiendo seed.")
        conn.close()
        return

    print("Cargando compras reales y tickets iniciales de Ruta Fría...")

    # 1. INSUMOS Y MATERIA PRIMA INICIAL (Basado en Compras Reales)
    insumos_data = [
        # (nombre, categoria, unidad, costo_unidad, stock_actual, stock_minimo, proveedor)
        ("Jarabe Natural San Marcos (1L)", "Jarabes y Endulzantes", "ml", 70.0 / 1000.0, 1000.0, 200.0, "San Marcos"),
        ("Endulzante Drac Valley (1L)", "Jarabes y Endulzantes", "ml", 58.0 / 1000.0, 1000.0, 200.0, "Drac Valley"),
        ("Vaso #16 Reyma (Paquete 50pza)", "Desechables", "pza", 148.0 / 50.0, 50.0, 10.0, "Reyma"),
        ("Clamato Original (2.54L)", "Bases y Mezclas", "ml", 91.0 / 2540.0, 2540.0, 500.0, "Clamato"),
        ("Frutimich Fresa (Frasco)", "Concentrados Frutimich", "pza", 75.0, 1.0, 1.0, "Frutimich"),
        ("Frutimich Mango (Frasco)", "Concentrados Frutimich", "pza", 75.0, 1.0, 1.0, "Frutimich"),
        ("Frutimich Tamarindo (Frasco)", "Concentrados Frutimich", "pza", 75.0, 1.0, 1.0, "Frutimich"),
        ("Frutimich Chamoy (Frasco)", "Concentrados Frutimich", "pza", 75.0, 1.0, 1.0, "Frutimich"),
        ("Jugo Maggi (800ml)", "Salsas y Sazonadores", "ml", 450.0 / 800.0, 800.0, 100.0, "Maggi"),
        ("Salsa Crosse & Blackwell Inglesa (290ml)", "Salsas y Sazonadores", "ml", 85.0 / 290.0, 290.0, 50.0, "Crosse & Blackwell"),
        ("Salsa Búfalo (370g)", "Salsas y Sazonadores", "ml", 65.0 / 370.0, 370.0, 50.0, "Búfalo"),
        ("Salsa Valentina Negra (1L)", "Salsas y Sazonadores", "ml", 45.0 / 1000.0, 1000.0, 150.0, "Valentina"),
        ("Chile Tajín en Polvo (500g)", "Chiles y Escarchados", "g", 60.0 / 500.0, 500.0, 100.0, "Tajín"),
        ("Chile Miguelito en Polvo (500g)", "Chiles y Escarchados", "g", 50.0 / 500.0, 500.0, 100.0, "Miguelito"),
        ("Gomitas y Botanas Variadas (1kg)", "Snacks y Toppings", "g", 120.0 / 1000.0, 1000.0, 200.0, "Surtido Local"),
        ("Agitadores de Madera (Paquete 100pza)", "Desechables", "pza", 35.0 / 100.0, 100.0, 20.0, "Distribuidora DPA")
    ]

    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")

    for nom, cat, uni, c_uni, st_act, st_min, prov in insumos_data:
        cursor.execute("""
        INSERT INTO insumos (nombre, categoria, unidad, costo_unidad, stock_actual, stock_minimo, proveedor, fecha_actualizacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nom, cat, uni, c_uni, st_act, st_min, prov, fecha_hoy))

    # Registramos compras históricas iniciales
    tickets_compras = [
        ("2026-09-01", "Jarabe Natural San Marcos (1L)", 1, "pza", 70.0, "San Marcos"),
        ("2026-09-01", "Endulzante Drac Valley (1L)", 1, "pza", 58.0, "Drac Valley"),
        ("2026-09-01", "Vaso #16 Reyma (Paquete 50pza)", 1, "paq", 148.0, "Reyma"),
        ("2026-09-01", "Clamato Original (2.54L)", 1, "pza", 91.0, "Clamato"),
        ("2026-09-01", "Frutimiches de Sabores (4 frascos)", 4, "pza", 300.0, "Frutimich"),
        ("2026-09-01", "Jugo Maggi (800ml)", 1, "pza", 450.0, "Maggi"),
        ("2026-09-01", "Salsas Variadas (Inglesa, Búfalo, Valentina)", 3, "pza", 195.0, "Abarrotes"),
        ("2026-09-01", "Chiles Polvo Tajín y Miguelito (1kg total)", 2, "pza", 110.0, "Abarrotes"),
        ("2026-09-01", "Gomitas y Botanas (1kg)", 1, "kg", 120.0, "Dulcería"),
        ("2026-09-01", "Agitadores de Madera (100pza)", 1, "paq", 35.0, "Desechables")
    ]

    for f_comp, i_nom, cant_c, uni_c, cost_t, prov_t in tickets_compras:
        cursor.execute("""
        INSERT INTO compras_historial (fecha, insumo_nombre, cantidad_comprada, unidad, costo_total, proveedor_ticket)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (f_comp, i_nom, cant_c, uni_c, cost_t, prov_t))

    # 2. INVERSIÓN INICIAL PRE-REGISTRADA
    monto_total_compras = sum(t[4] for t in tickets_compras) # $1,577.00
    cursor.execute("""
    INSERT INTO inversiones (concepto, categoria, monto, fecha, notas)
    VALUES (?, ?, ?, ?, ?)
    """, ("Compra Inicial de Insumos y Tickets Base", "Materia Prima Inicial", monto_total_compras, "2026-09-01", "Primer stock de arranque Ruta Fría"))

    cursor.execute("""
    INSERT INTO inversiones (concepto, categoria, monto, fecha, notas)
    VALUES (?, ?, ?, ?, ?)
    """, ("Hielera y Herramientas Bar de Preparación", "Equipamiento", 850.0, "2026-09-01", "Utensilios, cucharas medidoras y hielera"))

    # 3. PRODUCTOS Y BEBIDAS BASE DE RUTA FRÍA
    productos_base = [
        ("Michelada Clásica Ruta Fría (16 oz)", "Micheladas y Clamatos", 65.0, "Vaso #16 con escarchado de Tajín/Miguelito, mezcla de salsas Maggi/Inglesa/Búfalo/Valentina, Clamato y agitador."),
        ("Frutimiche Especial Ruta Fría (16 oz)", "Frutimiches", 85.0, "Vaso #16 con sabor Frutimich a elegir (Fresa/Mango/Tamarindo/Chamoy), Jarabe San Marcos, Clamato, escarchado y topping de gomitas."),
        ("Clamato Preparado con Snacking (16 oz)", "Micheladas y Clamatos", 75.0, "Clamato 16 oz bien frío con salsas sazonadoras, limonada endulzada, chile en polvo y brocheta de gomitas."),
        ("Vaso Snacking de Gomitas Preparadas", "Snacks y Botanas", 45.0, "Vaso con 150g de gomitas surtidas bañadas en Frutimich Chamoy, Tajín y Miguelito.")
    ]

    p_ids = {}
    for p_nom, p_cat, p_precio, p_desc in productos_base:
        cursor.execute("""
        INSERT INTO productos (nombre, categoria, precio_venta, descripcion)
        VALUES (?, ?, ?, ?)
        """, (p_nom, p_cat, p_precio, p_desc))
        p_ids[p_nom] = cursor.lastrowid

    # Obtener ID de insumos para asociar en Recetas
    cursor.execute("SELECT id, nombre FROM insumos")
    insumo_map = {row['nombre']: row['id'] for row in cursor.fetchall()}

    # 4. RECETAS (Para deducción automática de inventario y cálculo exacto de costo)
    recetas_data = [
        # Michelada Clásica
        (p_ids["Michelada Clásica Ruta Fría (16 oz)"], insumo_map["Vaso #16 Reyma (Paquete 50pza)"], 1.0),
        (p_ids["Michelada Clásica Ruta Fría (16 oz)"], insumo_map["Clamato Original (2.54L)"], 250.0), # 250ml
        (p_ids["Michelada Clásica Ruta Fría (16 oz)"], insumo_map["Jugo Maggi (800ml)"], 5.0), # 5ml
        (p_ids["Michelada Clásica Ruta Fría (16 oz)"], insumo_map["Salsa Crosse & Blackwell Inglesa (290ml)"], 5.0),
        (p_ids["Michelada Clásica Ruta Fría (16 oz)"], insumo_map["Salsa Búfalo (370g)"], 5.0),
        (p_ids["Michelada Clásica Ruta Fría (16 oz)"], insumo_map["Salsa Valentina Negra (1L)"], 10.0),
        (p_ids["Michelada Clásica Ruta Fría (16 oz)"], insumo_map["Chile Tajín en Polvo (500g)"], 10.0), # 10g escarchado
        (p_ids["Michelada Clásica Ruta Fría (16 oz)"], insumo_map["Agitadores de Madera (Paquete 100pza)"], 1.0),

        # Frutimiche Especial
        (p_ids["Frutimiche Especial Ruta Fría (16 oz)"], insumo_map["Vaso #16 Reyma (Paquete 50pza)"], 1.0),
        (p_ids["Frutimiche Especial Ruta Fría (16 oz)"], insumo_map["Clamato Original (2.54L)"], 200.0),
        (p_ids["Frutimiche Especial Ruta Fría (16 oz)"], insumo_map["Jarabe Natural San Marcos (1L)"], 20.0), # 20ml
        (p_ids["Frutimiche Especial Ruta Fría (16 oz)"], insumo_map["Frutimich Fresa (Frasco)"], 0.05), # ~5% del frasco por bebida
        (p_ids["Frutimiche Especial Ruta Fría (16 oz)"], insumo_map["Chile Miguelito en Polvo (500g)"], 10.0),
        (p_ids["Frutimiche Especial Ruta Fría (16 oz)"], insumo_map["Gomitas y Botanas Variadas (1kg)"], 30.0), # 30g gomitas
        (p_ids["Frutimiche Especial Ruta Fría (16 oz)"], insumo_map["Agitadores de Madera (Paquete 100pza)"], 1.0),

        # Clamato Preparado con Snacking
        (p_ids["Clamato Preparado con Snacking (16 oz)"], insumo_map["Vaso #16 Reyma (Paquete 50pza)"], 1.0),
        (p_ids["Clamato Preparado con Snacking (16 oz)"], insumo_map["Clamato Original (2.54L)"], 300.0),
        (p_ids["Clamato Preparado con Snacking (16 oz)"], insumo_map["Jugo Maggi (800ml)"], 5.0),
        (p_ids["Clamato Preparado con Snacking (16 oz)"], insumo_map["Salsa Crosse & Blackwell Inglesa (290ml)"], 5.0),
        (p_ids["Clamato Preparado con Snacking (16 oz)"], insumo_map["Gomitas y Botanas Variadas (1kg)"], 40.0),
        (p_ids["Clamato Preparado con Snacking (16 oz)"], insumo_map["Chile Tajín en Polvo (500g)"], 10.0),
        (p_ids["Clamato Preparado con Snacking (16 oz)"], insumo_map["Agitadores de Madera (Paquete 100pza)"], 1.0),

        # Vaso Snacking
        (p_ids["Vaso Snacking de Gomitas Preparadas"], insumo_map["Vaso #16 Reyma (Paquete 50pza)"], 1.0),
        (p_ids["Vaso Snacking de Gomitas Preparadas"], insumo_map["Gomitas y Botanas Variadas (1kg)"], 150.0),
        (p_ids["Vaso Snacking de Gomitas Preparadas"], insumo_map["Frutimich Chamoy (Frasco)"], 0.03),
        (p_ids["Vaso Snacking de Gomitas Preparadas"], insumo_map["Chile Miguelito en Polvo (500g)"], 10.0),
    ]

    for p_id, ins_id, cant in recetas_data:
        cursor.execute("""
        INSERT INTO recetas (producto_id, insumo_id, cantidad_requerida)
        VALUES (?, ?, ?)
        """, (p_id, ins_id, cant))

    # Actualizar el costo calculado de cada producto basado en su receta
    recalcular_costos_productos(cursor)

    # 5. CREACIÓN DE COMBOS BASE INICIALES
    # Combo Pareja / Fiesta: 2 Micheladas + 1 Vaso Snacking Gomitas
    # Precio regular individual: $65 + $65 + $45 = $175.00
    # Precio Combo Estratégico: $149.00 (Ahorro $26 -> 15% Desc)
    cursor.execute("SELECT costo_calculado FROM productos WHERE id = ?", (p_ids["Michelada Clásica Ruta Fría (16 oz)"],))
    c_mich = cursor.fetchone()[0] or 15.0
    cursor.execute("SELECT costo_calculado FROM productos WHERE id = ?", (p_ids["Vaso Snacking de Gomitas Preparadas"],))
    c_snack = cursor.fetchone()[0] or 20.0

    costo_combo_1 = (c_mich * 2) + c_snack
    cursor.execute("""
    INSERT INTO combos (nombre, descripcion, precio_regular, precio_combo, costo_total, descuento_porcentaje, fecha_creacion)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("PAQUETE DUO RUTA FRÍA (2 Micheladas + 1 Vaso Gomitas)", "Súper combo para compartir con 2 Micheladas clásicas de 16oz y 1 Vaso Snacking preparado.", 175.0, 149.0, costo_combo_1, 14.86, fecha_hoy))
    c_id_1 = cursor.lastrowid

    cursor.execute("INSERT INTO combo_items (combo_id, producto_id, cantidad) VALUES (?, ?, ?)", (c_id_1, p_ids["Michelada Clásica Ruta Fría (16 oz)"], 2))
    cursor.execute("INSERT INTO combo_items (combo_id, producto_id, cantidad) VALUES (?, ?, ?)", (c_id_1, p_ids["Vaso Snacking de Gomitas Preparadas"], 1))

    # Combo VIP Frutimich: 1 Frutimiche + 1 Clamato Snacking
    # Precio regular: $85 + $75 = $160.00
    # Precio Combo: $139.00 (Ahorro $21 -> 13% Desc)
    cursor.execute("SELECT costo_calculado FROM productos WHERE id = ?", (p_ids["Frutimiche Especial Ruta Fría (16 oz)"],))
    c_frut = cursor.fetchone()[0] or 20.0
    cursor.execute("SELECT costo_calculado FROM productos WHERE id = ?", (p_ids["Clamato Preparado con Snacking (16 oz)"],))
    c_clam = cursor.fetchone()[0] or 18.0

    costo_combo_2 = c_frut + c_clam
    cursor.execute("""
    INSERT INTO combos (nombre, descripcion, precio_regular, precio_combo, costo_total, descuento_porcentaje, fecha_creacion)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("COMBO RUTA EXPLOSIÓN (1 Frutimiche + 1 Clamato Snacking)", "Lo mejor de dos mundos: sabor dulce frutal y toque salado preparado.", 160.0, 139.0, costo_combo_2, 13.12, fecha_hoy))
    c_id_2 = cursor.lastrowid

    cursor.execute("INSERT INTO combo_items (combo_id, producto_id, cantidad) VALUES (?, ?, ?)", (c_id_2, p_ids["Frutimiche Especial Ruta Fría (16 oz)"], 1))
    cursor.execute("INSERT INTO combo_items (combo_id, producto_id, cantidad) VALUES (?, ?, ?)", (c_id_2, p_ids["Clamato Preparado con Snacking (16 oz)"], 1))

    conn.commit()
    conn.close()
    print("Precarga de datos iniciales realizada con éxito.")

def recalcular_costos_productos(cursor):
    cursor.execute("SELECT id FROM productos")
    productos = cursor.fetchall()
    for p in productos:
        pid = p['id']
        cursor.execute("""
        SELECT r.cantidad_requerida, i.costo_unidad 
        FROM recetas r 
        JOIN insumos i ON r.insumo_id = i.id 
        WHERE r.producto_id = ?
        """, (pid,))
        ingredientes = cursor.fetchall()
        costo_total = sum(r['cantidad_requerida'] * r['costo_unidad'] for r in ingredientes)
        cursor.execute("UPDATE productos SET costo_calculado = ? WHERE id = ?", (costo_total, pid))

if __name__ == "__main__":
    seed_all()
