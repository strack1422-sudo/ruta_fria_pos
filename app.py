import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ruta_fria.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        direccion TEXT,
        notas TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        rol TEXT NOT NULL,
        nombre TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracion (
        clave TEXT PRIMARY KEY,
        valor TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auditoria_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folio TEXT,
        usuario TEXT,
        accion TEXT,
        motivo TEXT,
        fecha_hora TEXT
    )
    """)
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN imagen_url TEXT")
    except:
        pass

    cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('logo_path', 'logo.png')")
    cursor.execute("INSERT OR IGNORE INTO usuarios (username, password, rol, nombre) VALUES ('admin', '1234', 'Administrador', 'Fernando (Dueño)')")
    cursor.execute("INSERT OR IGNORE INTO usuarios (username, password, rol, nombre) VALUES ('socio', '1234', 'Socio', 'Socio Ruta Fría')")
    cursor.execute("INSERT OR IGNORE INTO usuarios (username, password, rol, nombre) VALUES ('cajero', '1234', 'Operador', 'Personal de Caja')")
    conn.commit()
    conn.close()

init_tables()

st.set_page_config(
    page_title="Ruta Fría - Sistema POS y Gestión",
    page_icon="🧊",
    layout="wide"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #00A8E8;
        font-weight: bold;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# GESTIÓN DE SESIÓN Y LOGIN
if "user" not in st.session_state:
    st.session_state.user = None

def get_config(clave):
    conn = get_connection()
    row = conn.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
    conn.close()
    return row['valor'] if row else None

if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_file = get_config('logo_path')
        logo_path = os.path.join(os.path.dirname(__file__), logo_file if logo_file else "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=220)
        else:
            st.image("https://img.icons8.com/color/96/cold-drink.png", width=100)
        
        st.markdown("<h1 style='text-align: center; color: #00A8E8;'>Ruta Fría POS</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Inicia sesión para acceder al sistema</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit_login = st.form_submit_button("🔑 Entrar al Sistema")
            
            if submit_login:
                conn = get_connection()
                user_row = conn.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (username, password)).fetchone()
                conn.close()
                if user_row:
                    st.session_state.user = {
                        "id": user_row['id'],
                        "username": user_row['username'],
                        "nombre": user_row['nombre'],
                        "rol": user_row['rol']
                    }
                    st.success(f"¡Bienvenido, {user_row['nombre']}!")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
    st.stop()

# Menú lateral con Logo y Perfil
logo_file = get_config('logo_path')
logo_path = os.path.join(os.path.dirname(__file__), logo_file if logo_file else "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=160)
else:
    st.sidebar.image("https://img.icons8.com/color/96/cold-drink.png", width=80)

st.sidebar.title("Ruta Fría POS")
st.sidebar.markdown(f"👤 **{st.session_state.user['nombre']}**\n\n🛡️ Rol: *{st.session_state.user['rol']}*")
st.sidebar.markdown("---")

menu_options = [
    "🛒 Punto de Venta (POS)", 
    "📦 Inventario y Costos de Insumos", 
    "🍔 Productos y Recetas (Escandallo)", 
    "🎁 Combos y Paquetes", 
    "👥 Clientes y Domicilios", 
    "💰 Ventas y Finanzas", 
    "📊 Reportes y Utilidad",
    "⚙️ Configuración y Personalización"
]

if st.session_state.user['rol'] == 'Administrador':
    menu_options.append("👥 Gestión de Usuarios")

menu = st.sidebar.radio("Navegación", menu_options)

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.user = None
    st.session_state.carrito = []
    st.rerun()

# ----------------------------------------------------
# 1. PUNTO DE VENTA (POS)
# ----------------------------------------------------
if menu == "🛒 Punto de Venta (POS)":
    st.markdown('<p class="main-header">🧊 Punto de Venta - Ruta Fría</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Caja rápida con selección de cliente, dirección de entrega y personalización de extras</p>', unsafe_allow_html=True)

    conn = get_connection()
    
    clientes_rows = conn.execute("SELECT * FROM clientes").fetchall()
    cliente_map = {c['id']: c for c in clientes_rows}
    cliente_opciones = ["Venta General / Mostrador"] + [f"{c['nombre']} ({c['telefono'] or 'Sin tel'})" for c in clientes_rows]
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        sel_cliente_str = st.selectbox("📍 Seleccionar Cliente (Muestra Dirección)", cliente_opciones)
    with col_c2:
        if st.button("➕ Nuevo Cliente"):
            st.session_state.show_quick_client = True

    cliente_seleccionado_obj = None
    if sel_cliente_str != "Venta General / Mostrador":
        for c in clientes_rows:
            if f"{c['nombre']} ({c['telefono'] or 'Sin tel'})" == sel_cliente_str:
                cliente_seleccionado_obj = c
                break
        if cliente_seleccionado_obj:
            st.info(f"🛵 **Dirección de Entrega:** {cliente_seleccionado_obj['direccion'] or 'No especificada'} | 📱 **Teléfono:** {cliente_seleccionado_obj['telefono'] or 'N/A'}")

    if st.session_state.get('show_quick_client', False):
        with st.form("quick_client_form"):
            st.subheader("Registro Rápido de Cliente")
            qc_nombre = st.text_input("Nombre")
            qc_tel = st.text_input("Teléfono / WhatsApp")
            qc_dir = st.text_area("Dirección para Repartidor")
            if st.form_submit_button("Guardar y Seleccionar"):
                if qc_nombre:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO clientes (nombre, telefono, direccion) VALUES (?, ?, ?)", (qc_nombre, qc_tel, qc_dir))
                    conn.commit()
                    st.success("¡Cliente registrado!")
                    st.session_state.show_quick_client = False
                    st.rerun()

    tab_prod, tab_combo = st.tabs(["🥤 Productos Individuales", "🎁 Paquetes y Combos"])

    if "carrito" not in st.session_state:
        st.session_state.carrito = []

    with tab_prod:
        productos = conn.execute("SELECT * FROM productos WHERE activo = 1").fetchall()
        cols = st.columns(3)
        for idx, prod in enumerate(productos):
            with cols[idx % 3]:
                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 15px; background: white;">
                    <h4 style="color: #0077B6; margin-bottom: 5px;">{prod['nombre']}</h4>
                    <p style="color: #666; font-size: 0.9rem; min-height: 40px;">{prod['descripcion']}</p>
                    <h3 style="color: #2b9348;">${prod['precio_venta']:.2f}</h3>
                    <p style="font-size: 0.8rem; color: #888;">Costo est: ${prod['costo_calculado']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"➕ Agregar / Personalizar##{prod['id']}"):
                    with st.form(f"form_add_{prod['id']}"):
                        cant_prod = st.number_input("Cantidad", min_value=1, value=1, key=f"cp_{prod['id']}")
                        insumos_disp = conn.execute("SELECT * FROM insumos").fetchall()
                        ins_nombres = [i['nombre'] for i in insumos_disp]
                        extra_elegido = st.selectbox("Agregar ingrediente extra (opcional)", ["Ninguno"] + ins_nombres, key=f"ext_{prod['id']}")
                        cantidad_extra = st.number_input("Cantidad extra", min_value=0.0, value=0.0, key=f"cext_{prod['id']}")
                        nota_personalizada = st.text_input("Nota especial", key=f"np_{prod['id']}")

                        if st.form_submit_button("Añadir al Carrito"):
                            precio_final = prod['precio_venta']
                            costo_final = prod['costo_calculado']
                            nombre_item = prod['nombre']
                            
                            if extra_elegido != "Ninguno" and cantidad_extra > 0:
                                ins_obj = next(i for i in insumos_disp if i['nombre'] == extra_elegido)
                                costo_extra = ins_obj['costo_unidad'] * cantidad_extra
                                costo_final += costo_extra
                                precio_final += (costo_extra * 1.5)
                                nombre_item += f" (+ Extra {extra_elegido})"

                            if nota_personalizada:
                                nombre_item += f" [{nota_personalizada}]"

                            st.session_state.carrito.append({
                                "tipo": "producto",
                                "id": prod['id'],
                                "nombre": nombre_item,
                                "precio": precio_final,
                                "costo": costo_final,
                                "cantidad": int(cant_prod)
                            })
                            st.success(f"¡Agregado!")
                            st.rerun()

    with tab_combo:
        combos = conn.execute("SELECT * FROM combos WHERE activo = 1").fetchall()
        cols_c = st.columns(2)
        for idx, combo in enumerate(combos):
            with cols_c[idx % 2]:
                st.markdown(f"""
                <div style="border: 2px dashed #00A8E8; padding: 15px; border-radius: 10px; margin-bottom: 15px; background: #fdfefe;">
                    <h4 style="color: #d90429; margin-bottom: 5px;">{combo['nombre']}</h4>
                    <p style="color: #444; font-size: 0.9rem; min-height: 40px;">{combo['descripcion']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="text-decoration: line-through; color: #999; font-size: 1rem;">${combo['precio_regular']:.2f}</span>
                            <h2 style="color: #2b9348; margin: 0;">${combo['precio_combo']:.2f}</h2>
                        </div>
                        <span style="background: #ffb703; color: #fff; padding: 5px 10px; border-radius: 5px; font-weight: bold;">Ahorro {combo['descuento_porcentaje']:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Agregar Combo##{combo['id']}", key=f"btn_c_{combo['id']}"):
                    st.session_state.carrito.append({
                        "tipo": "combo",
                        "id": combo['id'],
                        "nombre": combo['nombre'],
                        "precio": combo['precio_combo'],
                        "costo": combo['costo_total'],
                        "cantidad": 1
                    })
                    st.success(f"¡Combo agregado!")

    st.markdown("---")
    st.subheader("🛒 Resumen de Ticket Actual")

    if len(st.session_state.carrito) > 0:
        for i, item in enumerate(st.session_state.carrito):
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            c1.write(f"**{item['nombre']}** ({item['tipo']})")
            c2.write(f"${item['precio']:.2f}")
            
            nueva_cant = c3.number_input("Cant", value=item['cantidad'], min_value=1, key=f"cant_{i}")
            if nueva_cant != item['cantidad']:
                motivo_mod = st.text_input(f"Motivo de modificación en {item['nombre']}:", key=f"mot_{i}")
                if motivo_mod:
                    item['cantidad'] = nueva_cant
                    cur_aud = conn.cursor()
                    cur_aud.execute("INSERT INTO auditoria_tickets (folio, usuario, accion, motivo, fecha_hora) VALUES (?, ?, ?, ?, ?)",
                                    ("EN_CURSO", st.session_state.user['username'], f"Modificar cantidad a {nueva_cant}", motivo_mod, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
            
            subtotal = item['precio'] * item['cantidad']
            c4.write(f"**${subtotal:.2f}**")
            
            if c5.button("❌##del_cart_" + str(i), key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()

        total_general = sum(item['precio'] * item['cantidad'] for item in st.session_state.carrito)
        costo_general = sum(item['costo'] * item['cantidad'] for item in st.session_state.carrito)
        utilidad_estimada = total_general - costo_general

        st.markdown(f"### Total a Pagar: <span style='color: #2b9348;'>${total_general:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"Utilidad neta estimada: **${utilidad_estimada:.2f}**")

        metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia / QR", "Tarjeta"])
        notas_venta = st.text_input("Notas adicionales del ticket")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🚨 Limpiar Carrito", type="secondary"):
                st.session_state.carrito = []
                st.rerun()
        with col_b2:
            if st.button("✅ Cobrar y Registrar Venta", type="primary"):
                folio = f"RF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cliente_final = sel_cliente_str if sel_cliente_str != "Venta General / Mostrador" else "Mostrador"

                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO ventas (folio, fecha_hora, total_venta, costo_total, utilidad_neta, metodo_pago, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (folio, fecha_hora, total_general, costo_general, utilidad_estimada, metodo_pago, f"Cliente: {cliente_final} | {notas_venta}"))
                venta_id = cursor.lastrowid

                for item in st.session_state.carrito:
                    subt = item['precio'] * item['cantidad']
                    cursor.execute("""
                    INSERT INTO venta_detalles (venta_id, tipo, item_id, nombre_item, cantidad, precio_unitario, costo_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (venta_id, item['tipo'], item['id'], item['nombre'], item['cantidad'], item['precio'], item['costo'], subt))

                    if item['tipo'] == 'producto':
                        recetas = cursor.execute("SELECT insumo_id, cantidad_requerida FROM recetas WHERE producto_id = ?", (item['id'],)).fetchall()
                        for rec in recetas:
                            gasto_insumo = rec['cantidad_requerida'] * item['cantidad']
                            cursor.execute("UPDATE insumos SET stock_actual = stock_actual - ? WHERE id = ?", (gasto_insumo, rec['insumo_id']))
                    
                    elif item['tipo'] == 'combo':
                        combo_prods = cursor.execute("SELECT producto_id, cantidad FROM combo_items WHERE combo_id = ?", (item['id'],)).fetchall()
                        for cp in combo_prods:
                            cant_prod_total = cp['cantidad'] * item['cantidad']
                            recetas = cursor.execute("SELECT insumo_id, cantidad_requerida FROM recetas WHERE producto_id = ?", (cp['producto_id'],)).fetchall()
                            for rec in recetas:
                                gasto_insumo = rec['cantidad_requerida'] * cant_prod_total
                                cursor.execute("UPDATE insumos SET stock_actual = stock_actual - ? WHERE id = ?", (gasto_insumo, rec['insumo_id']))

                conn.commit()
                conn.close()

                st.success(f"🎉 ¡Venta cobrada con éxito! Folio: {folio}")
                st.session_state.carrito = []
                st.balloons()
    else:
        st.info("El carrito está vacío. Agrega productos o combos para comenzar.")

    conn.close()

# ----------------------------------------------------
# 2. INVENTARIO Y COSTOS DE INSUMOS
# ----------------------------------------------------
elif menu == "📦 Inventario y Costos de Insumos":
    st.markdown('<p class="main-header">📦 Gestión de Insumos, Costos y Materia Prima</p>', unsafe_allow_html=True)
    conn = get_connection()
    insumos_list = conn.execute("SELECT * FROM insumos").fetchall()

    for idx, ins in enumerate(insumos_list):
        with st.expander(f"📌 {ins['nombre']} | Costo: ${ins['costo_unidad']:.4f}##{ins['id']}"):
            with st.form(f"form_edit_insumo_{ins['id']}"):
                nuevo_nombre = st.text_input("Nombre", value=ins['nombre'], key=f"ni_{ins['id']}")
                nueva_cat = st.text_input("Categoría", value=ins['categoria'], key=f"ci_{ins['id']}")
                nueva_unidad = st.text_input("Unidad base", value=ins['unidad'], key=f"ui_{ins['id']}")
                nuevo_costo = st.number_input("Costo por Unidad Base ($)", value=float(ins['costo_unidad']), format="%.4f", key=f"co_{ins['id']}")
                nuevo_stock = st.number_input("Stock Actual", value=float(ins['stock_actual']), key=f"st_{ins['id']}")
                nuevo_min = st.number_input("Stock Mínimo", value=float(ins['stock_minimo']), key=f"mi_{ins['id']}")
                nuevo_prov = st.text_input("Proveedor", value=str(ins['proveedor'] or ''), key=f"pr_{ins['id']}")

                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    b_ins_save = st.form_submit_button("💾 Guardar Insumo")
                with col_i2:
                    b_ins_del = st.form_submit_button("❌ Eliminar Insumo")

                if b_ins_save:
                    cur = conn.cursor()
                    cur.execute("""
                    UPDATE insumos SET nombre = ?, categoria = ?, unidad = ?, costo_unidad = ?, stock_actual = ?, stock_minimo = ?, proveedor = ?, fecha_actualizacion = ?
                    WHERE id = ?
                    """, (nuevo_nombre, nueva_cat, nueva_unidad, nuevo_costo, nuevo_stock, nuevo_min, nuevo_prov, datetime.now().strftime("%Y-%m-%d %H:%M"), ins['id']))
                    conn.commit()
                    conn.close()
                    st.success("¡Actualizado!")
                    st.rerun()

                if b_ins_del:
                    if st.session_state.user['rol'] == 'Operador':
                        st.error("Sin permisos.")
                    else:
                        cur = conn.cursor()
                        cur.execute("DELETE FROM insumos WHERE id = ?", (ins['id'],))
                        conn.commit()
                        conn.close()
                        st.warning("Eliminado.")
                        st.rerun()
    conn.close()

# ----------------------------------------------------
# 3. PRODUCTOS Y RECETAS (ESCANDALLO)
# ----------------------------------------------------
elif menu == "🍔 Productos y Recetas (Escandallo)":
    st.markdown('<p class="main-header">🍔 Catálogo de Productos y Recetas</p>', unsafe_allow_html=True)
    conn = get_connection()
    productos_list = conn.execute("SELECT * FROM productos").fetchall()

    for idx, prod in enumerate(productos_list):
        with st.expander(f"🥤 {prod['nombre']} | Venta: ${prod['precio_venta']:.2f}##{prod['id']}"):
            with st.form(f"form_prod_{prod['id']}"):
                p_nom = st.text_input("Nombre", value=prod['nombre'], key=f"pn_{prod['id']}")
                p_cat = st.text_input("Categoría", value=prod['categoria'], key=f"pc_{prod['id']}")
                p_precio = st.number_input("Precio Venta ($)", value=float(prod['precio_venta']), key=f"pp_{prod['id']}")
                p_desc = st.text_area("Descripción", value=str(prod['descripcion'] or ''), key=f"pd_{prod['id']}")
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    b_p_save = st.form_submit_button("💾 Guardar")
                with col_p2:
                    b_p_del = st.form_submit_button("❌ Eliminar Producto")

                if b_p_save:
                    cur = conn.cursor()
                    cur.execute("UPDATE productos SET nombre = ?, categoria = ?, precio_venta = ?, descripcion = ? WHERE id = ?", (p_nom, p_cat, p_precio, p_desc, prod['id']))
                    conn.commit()
                    conn.close()
                    st.success("Actualizado")
                    st.rerun()

                if b_p_del:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM productos WHERE id = ?", (prod['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Eliminado")
                    st.rerun()
    conn.close()

# ----------------------------------------------------
# 4. COMBOS Y PAQUETES (CON EDICIÓN, AÑADIR Y ELIMINAR TOTAL)
# ----------------------------------------------------
elif menu == "🎁 Combos y Paquetes":
    st.markdown('<p class="main-header">🎁 Combos y Paquetes Estratégicos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Crea, edita o elimina paquetes promocionales libremente</p>', unsafe_allow_html=True)

    conn = get_connection()
    combos = conn.execute("SELECT * FROM combos").fetchall()

    for idx, combo in enumerate(combos):
        with st.expander(f"📦 {combo['nombre']} | Precio: ${combo['precio_combo']:.2f} (Ahorro {combo['descuento_porcentaje']:.1f}%)##combo_{combo['id']}"):
            with st.form(f"combo_edit_{combo['id']}"):
                c_nom = st.text_input("Nombre del Combo", value=combo['nombre'], key=f"cn_{combo['id']}")
                c_desc = st.text_input("Descripción", value=combo['descripcion'], key=f"cd_{combo['id']}")
                c_reg = st.number_input("Precio Regular ($)", value=float(combo['precio_regular']), key=f"cr_{combo['id']}")
                c_com = st.number_input("Precio Combo ($)", value=float(combo['precio_combo']), key=f"cc_{combo['id']}")

                col_cb1, col_cb2 = st.columns(2)
                with col_cb1:
                    b_cs = st.form_submit_button("💾 Actualizar Combo")
                with col_cb2:
                    b_cd = st.form_submit_button("❌ Eliminar Combo")

                if b_cs:
                    desc_p = ((c_reg - c_com) / c_reg) * 100 if c_reg > 0 else 0
                    cur = conn.cursor()
                    cur.execute("""
                    UPDATE combos SET nombre = ?, descripcion = ?, precio_regular = ?, precio_combo = ?, descuento_porcentaje = ? WHERE id = ?
                    """, (c_nom, c_desc, c_reg, c_com, desc_p, combo['id']))
                    conn.commit()
                    conn.close()
                    st.success("¡Combo actualizado con éxito!")
                    st.rerun()

                if b_cd:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM combos WHERE id = ?", (combo['id'],))
                    cur.execute("DELETE FROM combo_items WHERE combo_id = ?", (combo['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Combo eliminado correctamente.")
                    st.rerun()

    st.markdown("---")
    st.subheader("➕ Crear Nuevo Combo o Paquete Promocional")
    with st.form("nuevo_combo_form"):
        nc_nom = st.text_input("Nombre del Paquete")
        nc_desc = st.text_input("Descripción breve (ej. 2 Micheladas + 1 Snack)")
        nc_reg = st.number_input("Precio Regular Sumado ($)", min_value=1.0, value=150.0)
        nc_com = st.number_input("Precio de Venta Combo ($)", min_value=1.0, value=129.0)

        if st.form_submit_button("Crear Nuevo Combo"):
            desc_calc = ((nc_reg - nc_com) / nc_reg) * 100 if nc_reg > 0 else 0
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO combos (nombre, descripcion, precio_regular, precio_combo, costo_total, descuento_porcentaje, fecha_creacion, activo)
            VALUES (?, ?, ?, ?, 50.0, ?, ?, 1)
            """, (nc_nom, nc_desc, nc_reg, nc_com, desc_calc, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("¡Combo creado con éxito!")
            st.rerun()

    conn.close()

# ----------------------------------------------------
# 5. CLIENTES Y DOMICILIOS
# ----------------------------------------------------
elif menu == "👥 Clientes y Domicilios":
    st.markdown('<p class="main-header">👥 Directorio de Clientes y Servicio a Domicilio</p>', unsafe_allow_html=True)
    conn = get_connection()
    clientes = conn.execute("SELECT * FROM clientes").fetchall()

    for idx, cli in enumerate(clientes):
        with st.expander(f"👤 {cli['nombre']} | Tel: {cli['telefono'] or 'N/A'}##cli_{cli['id']}"):
            with st.form(f"form_cli_{cli['id']}"):
                cl_nom = st.text_input("Nombre", value=cli['nombre'], key=f"clin_{cli['id']}")
                cl_tel = st.text_input("Teléfono", value=str(cli['telefono'] or ''), key=f"clt_{cli['id']}")
                cl_dir = st.text_area("Dirección", value=str(cli['direccion'] or ''), key=f"cld_{cli['id']}")
                cl_not = st.text_input("Notas", value=str(cli['notas'] or ''), key=f"cln_{cli['id']}")

                col_cl1, col_cl2 = st.columns(2)
                with col_cl1:
                    b_cl_save = st.form_submit_button("💾 Guardar Cliente")
                with col_cl2:
                    b_cl_del = st.form_submit_button("❌ Eliminar Cliente")

                if b_cl_save:
                    cur = conn.cursor()
                    cur.execute("UPDATE clientes SET nombre = ?, telefono = ?, direccion = ?, notas = ? WHERE id = ?", (cl_nom, cl_tel, cl_dir, cl_not, cli['id']))
                    conn.commit()
                    conn.close()
                    st.success("¡Cliente actualizado!")
                    st.rerun()

                if b_cl_del:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM clientes WHERE id = ?", (cli['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Cliente eliminado.")
                    st.rerun()
    conn.close()

# ----------------------------------------------------
# 6. VENTAS Y FINANZAS
# ----------------------------------------------------
elif menu == "💰 Ventas y Finanzas":
    st.markdown('<p class="main-header">💰 Reporte de Ventas y Finanzas</p>', unsafe_allow_html=True)
    conn = get_connection()
    ventas_df = pd.read_sql("SELECT * FROM ventas ORDER BY fecha_hora DESC", conn)

    if len(ventas_df) > 0:
        periodo = st.radio("Periodo", ["Diario (Hoy)", "Semanal (Últimos 7 días)", "Mensual (Último mes)", "Histórico Completo"])
        ventas_df['fecha_dt'] = pd.to_datetime(ventas_df['fecha_hora'])
        hoy = datetime.now()

        if periodo == "Diario (Hoy)":
            ventas_filt = ventas_df[ventas_df['fecha_dt'].dt.date == hoy.date()]
        elif periodo == "Semanal (Últimos 7 días)":
            ventas_filt = ventas_df[ventas_df['fecha_dt'] >= hoy - timedelta(days=7)]
        elif periodo == "Mensual (Último mes)":
            ventas_filt = ventas_df[ventas_df['fecha_dt'] >= hoy - timedelta(days=30)]
        else:
            ventas_filt = ventas_df

        t_ing = ventas_filt['total_venta'].sum()
        t_cos = ventas_filt['costo_total'].sum()
        t_util = ventas_filt['utilidad_neta'].sum()
        margen = (t_util / t_ing * 100) if t_ing > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos", f"${t_ing:.2f}")
        c2.metric("Costos", f"${t_cos:.2f}")
        c3.metric("Utilidad Neta", f"${t_util:.2f}")
        c4.metric("Margen", f"{margen:.1f}%")

        st.markdown("---")
        st.dataframe(ventas_filt[['folio', 'fecha_hora', 'total_venta', 'costo_total', 'utilidad_neta', 'metodo_pago', 'notas']], use_container_width=True)
    else:
        st.info("Sin ventas registradas.")
    conn.close()

# ----------------------------------------------------
# 7. REPORTES Y UTILIDAD
# ----------------------------------------------------
elif menu == "📊 Reportes y Utilidad":
    st.markdown('<p class="main-header">📊 Análisis de Rendimiento y Utilidad</p>', unsafe_allow_html=True)
    conn = get_connection()
    inv = conn.execute("SELECT SUM(monto) FROM inversiones").fetchone()[0] or 0.0
    util = conn.execute("SELECT SUM(utilidad_neta) FROM ventas").fetchone()[0] or 0.0

    st.metric("Inversión Inicial Total", f"${inv:.2f}")
    st.metric("Utilidad Neta Histórica Acumulada", f"${util:.2f}")
    st.metric("Retorno de Inversión (ROI)", f"{(util/inv*100):.1f}%" if inv > 0 else "0.0%")
    conn.close()

# ----------------------------------------------------
# 8. CONFIGURACIÓN Y PERSONALIZACIÓN
# ----------------------------------------------------
elif menu == "⚙️ Configuración y Personalización":
    st.markdown('<p class="main-header">⚙️ Configuración del Sistema y Logotipo</p>', unsafe_allow_html=True)
    conn = get_connection()
    current_logo = get_config('logo_path')
    
    st.info(f"Logotipo actual: **{current_logo}**")
    logo_path = os.path.join(os.path.dirname(__file__), current_logo if current_logo else "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=220)

    st.markdown("---")
    st.subheader("🖼️ Cambiar Logotipo Corporativo")
    with st.form("config_logo_form"):
        nuevo_nombre_logo = st.text_input("Nombre de archivo de imagen (ej. logo.png)", value=current_logo)
        if st.form_submit_button("Actualizar Logo"):
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('logo_path', ?)", (nuevo_nombre_logo,))
            conn.commit()
            conn.close()
            st.success("¡Logo actualizado con éxito!")
            st.rerun()
    conn.close()

# ----------------------------------------------------
# 9. GESTIÓN DE USUARIOS
# ----------------------------------------------------
elif menu == "👥 Gestión de Usuarios":
    if st.session_state.user['rol'] != 'Administrador':
        st.error("Acceso restringido al Administrador.")
    else:
        st.markdown('<p class="main-header">👥 Gestión de Usuarios y Accesos</p>', unsafe_allow_html=True)
        conn = get_connection()
        st.dataframe(pd.read_sql("SELECT id, username, rol, nombre FROM usuarios", conn), use_container_width=True)

        st.markdown("---")
        st.subheader("➕ Crear Usuario Nuevo")
        with st.form("new_user_form"):
            nu_u = st.text_input("Usuario")
            nu_p = st.text_input("Contraseña", type="password")
            nu_r = st.selectbox("Rol", ["Socio", "Operador"])
            nu_n = st.text_input("Nombre Completo")

            if st.form_submit_button("Crear Usuario"):
                try:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO usuarios (username, password, rol, nombre) VALUES (?, ?, ?, ?)", (nu_u, nu_p, nu_r, nu_n))
                    conn.commit()
                    conn.close()
                    st.success("¡Usuario creado!")
                    st.rerun()
                except:
                    st.error("Error: El usuario ya existe.")
        conn.close()
