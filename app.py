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
        rol TEXT NOT NULL, -- 'Administrador', 'Socio', 'Operador'
        nombre TEXT
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
    # Asegurar usuarios por defecto si no existen
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

if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=200)
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
logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=160)
else:
    st.sidebar.image("https://img.icons8.com/color/96/cold-drink.png", width=80)

st.sidebar.title("Ruta Fría POS")
st.sidebar.markdown(f"👤 **{st.session_state.user['nombre']}**\n\n🛡️ Rol: *{st.session_state.user['rol']}*")
st.sidebar.markdown("---")

menu_options = ["🛒 Punto de Venta (POS)", "📦 Inventario de Insumos", "🍔 Productos y Recetas", "🎁 Combos y Paquetes", "👥 Clientes y Domicilios", "💰 Ventas y Finanzas", "📊 Reportes y Utilidad"]

if st.session_state.user['rol'] == 'Administrador':
    menu_options.append("⚙️ Gestión de Usuarios")

menu = st.sidebar.radio("Navegación", menu_options)

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.user = None
    st.session_state.carrito = []
    st.rerun()

# ----------------------------------------------------
# 1. PUNTO DE VENTA (POS) CON CLIENTE Y MODIFICACIÓN CON AUDITORÍA
# ----------------------------------------------------
if menu == "🛒 Punto de Venta (POS)":
    st.markdown('<p class="main-header">🧊 Punto de Venta - Ruta Fría</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Caja rápida con captura de datos de clientes para servicio a domicilio o local</p>', unsafe_allow_html=True)

    conn = get_connection()
    
    # Selección de Cliente
    clientes_rows = conn.execute("SELECT * FROM clientes").fetchall()
    cliente_nombres = ["Venta General / Mostrador"] + [f"{c['nombre']} ({c['telefono'] or 'Sin tel'})" for c in clientes_rows]
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        sel_cliente = st.selectbox("📍 Cliente (Domicilio o Mostrador)", cliente_nombres)
    with col_c2:
        if st.button("➕ Registrar Nuevo Cliente"):
            st.session_state.show_new_client = True

    if st.session_state.get('show_new_client', False):
        with st.form("quick_client_form"):
            st.subheader("Nuevo Cliente Rápido")
            qc_nombre = st.text_input("Nombre Completo")
            qc_tel = st.text_input("Teléfono / WhatsApp")
            qc_dir = st.text_area("Dirección de Entrega")
            if st.form_submit_button("Guardar Cliente"):
                if qc_nombre:
                    c_cur = conn.cursor()
                    c_cur.execute("INSERT INTO clientes (nombre, telefono, direccion) VALUES (?, ?, ?)", (qc_nombre, qc_tel, qc_dir))
                    conn.commit()
                    st.success("¡Cliente registrado!")
                    st.session_state.show_new_client = False
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
                if st.button(f"Agregar al Carrito", key=f"p_{prod['id']}"):
                    st.session_state.carrito.append({
                        "tipo": "producto",
                        "id": prod['id'],
                        "nombre": prod['nombre'],
                        "precio": prod['precio_venta'],
                        "costo": prod['costo_calculado'],
                        "cantidad": 1
                    })
                    st.success(f"¡Agregado: {prod['nombre']}!")

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
                if st.button(f"Agregar Combo", key=f"c_{combo['id']}"):
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
    st.subheader("🛒 Resumen de Ticket Actual y Modificación con Auditoría")

    if len(st.session_state.carrito) > 0:
        for i, item in enumerate(st.session_state.carrito):
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            c1.write(f"**{item['nombre']}** ({item['tipo']})")
            c2.write(f"${item['precio']:.2f}")
            
            nueva_cant = c3.number_input("Cant", value=item['cantidad'], min_value=1, key=f"cant_{i}")
            if nueva_cant != item['cantidad']:
                # Pedir motivo de modificación para auditoría
                motivo_mod = st.text_input(f"Motivo por el cual modifica la cantidad de {item['nombre']}:", key=f"mot_{i}")
                if motivo_mod:
                    item['cantidad'] = nueva_cant
                    # Registrar auditoría
                    cur_aud = conn.cursor()
                    cur_aud.execute("INSERT INTO auditoria_tickets (folio, usuario, accion, motivo, fecha_hora) VALUES (?, ?, ?, ?, ?)",
                                    ("EN_CURSO", st.session_state.user['username'], f"Modificar cantidad a {nueva_cant}", motivo_mod, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
            
            subtotal = item['precio'] * item['cantidad']
            c4.write(f"**${subtotal:.2f}**")
            
            if c5.button("❌", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()

        total_general = sum(item['precio'] * item['cantidad'] for item in st.session_state.carrito)
        costo_general = sum(item['costo'] * item['cantidad'] for item in st.session_state.carrito)
        utilidad_estimada = total_general - costo_general

        st.markdown(f"### Total a Pagar: <span style='color: #2b9348;'>${total_general:.2f}</span>", unsafe_allow_html=True)
        st.markdown(f"Utilidad neta estimada: **${utilidad_estimada:.2f}**")

        metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia / QR", "Tarjeta"])
        notas_venta = st.text_input("Notas adicionales del pedido")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🚨 Limpiar Carrito", type="secondary"):
                st.session_state.carrito = []
                st.rerun()
        with col_b2:
            if st.button("✅ Cobrar y Registrar Venta", type="primary"):
                folio = f"RF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cliente_final = sel_cliente if sel_cliente != "Venta General / Mostrador" else "Mostrador"

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
# 2. INVENTARIO DE INSUMOS (CON PERMISOS DE ELIMINACIÓN)
# ----------------------------------------------------
elif menu == "📦 Inventario de Insumos":
    st.markdown('<p class="main-header">📦 Control Total de Insumos y Materia Prima</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gestión de stock con restricciones de rol</p>', unsafe_allow_html=True)

    conn = get_connection()
    insumos_list = conn.execute("SELECT * FROM insumos").fetchall()

    for ins in insumos_list:
        with st.expander(f"📌 {ins['nombre']} (Stock: {ins['stock_actual']} {ins['unidad']})"):
            with st.form(f"form_edit_insumo_{ins['id']}"):
                nuevo_nombre = st.text_input("Nombre del Insumo", value=ins['nombre'], key=f"nom_{ins['id']}")
                nueva_cat = st.text_input("Categoría", value=ins['categoria'], key=f"cat_{ins['id']}")
                nueva_unidad = st.text_input("Unidad (ml, g, pza)", value=ins['unidad'], key=f"uni_{ins['id']}")
                nuevo_costo = st.number_input("Costo por Unidad Base ($)", value=float(ins['costo_unidad']), format="%.4f", key=f"cost_{ins['id']}")
                nuevo_stock = st.number_input("Stock Actual", value=float(ins['stock_actual']), key=f"stk_{ins['id']}")
                nuevo_min = st.number_input("Stock Mínimo Alerta", value=float(ins['stock_minimo']), key=f"min_{ins['id']}")
                nuevo_prov = st.text_input("Proveedor", value=str(ins['proveedor'] or ''), key=f"prov_{ins['id']}")

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    btn_guardar = st.form_submit_button("💾 Guardar Cambios")
                with col_e2:
                    btn_eliminar = st.form_submit_button("❌ Eliminar Insumo")

                if btn_guardar:
                    cursor = conn.cursor()
                    cursor.execute("""
                    UPDATE insumos SET nombre = ?, categoria = ?, unidad = ?, costo_unidad = ?, stock_actual = ?, stock_minimo = ?, proveedor = ?, fecha_actualizacion = ?
                    WHERE id = ?
                    """, (nuevo_nombre, nueva_cat, nueva_unidad, nuevo_costo, nuevo_stock, nuevo_min, nuevo_prov, datetime.now().strftime("%Y-%m-%d %H:%M"), ins['id']))
                    conn.commit()
                    conn.close()
                    st.success("¡Insumo actualizado correctamente!")
                    st.rerun()

                if btn_eliminar:
                    if st.session_state.user['rol'] == 'Operador':
                        st.error("⚠️ Los operadores no tienen permiso para eliminar insumos. Contacta al Administrador o Socio.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM insumos WHERE id = ?", (ins['id'],))
                        cursor.execute("DELETE FROM recetas WHERE insumo_id = ?", (ins['id'],))
                        conn.commit()
                        conn.close()
                        st.warning("Insumo eliminado del sistema.")
                        st.rerun()

    conn.close()

# ----------------------------------------------------
# 3. PRODUCTOS Y RECETAS
# ----------------------------------------------------
elif menu == "🍔 Productos y Recetas":
    st.markdown('<p class="main-header">🍔 Catálogo de Productos y Recetas</p>', unsafe_allow_html=True)
    conn = get_connection()
    productos_list = conn.execute("SELECT * FROM productos").fetchall()

    for prod in productos_list:
        with st.expander(f"🥤 {prod['nombre']} - Venta: ${prod['precio_venta']:.2f}"):
            with st.form(f"form_edit_prod_{prod['id']}"):
                p_nom = st.text_input("Nombre", value=prod['nombre'], key=f"pn_{prod['id']}")
                p_precio = st.number_input("Precio Venta ($)", value=float(prod['precio_venta']), key=f"pp_{prod['id']}")
                p_desc = st.text_area("Descripción", value=str(prod['descripcion'] or ''), key=f"pd_{prod['id']}")
                
                if st.form_submit_button("💾 Actualizar Producto"):
                    cursor = conn.cursor()
                    cursor.execute("UPDATE productos SET nombre = ?, precio_venta = ?, descripcion = ? WHERE id = ?", (p_nom, p_precio, p_desc, prod['id']))
                    conn.commit()
                    conn.close()
                    st.success("Actualizado con éxito")
                    st.rerun()
    conn.close()

# ----------------------------------------------------
# 4. COMBOS Y PAQUETES
# ----------------------------------------------------
elif menu == "🎁 Combos y Paquetes":
    st.markdown('<p class="main-header">🎁 Combos y Paquetes Estratégicos</p>', unsafe_allow_html=True)
    conn = get_connection()
    combos = conn.execute("SELECT * FROM combos").fetchall()
    for combo in combos:
        st.write(f"**{combo['nombre']}** - Precio Combo: ${combo['precio_combo']:.2f} (Ahorro {combo['descuento_porcentaje']:.1f}%)")
    conn.close()

# ----------------------------------------------------
# 5. CLIENTES Y DOMICILIOS
# ----------------------------------------------------
elif menu == "👥 Clientes y Domicilios":
    st.markdown('<p class="main-header">👥 Directorio de Clientes y Servicio a Domicilio</p>', unsafe_allow_html=True)
    conn = get_connection()
    clientes = pd.read_sql("SELECT * FROM clientes", conn)
    st.dataframe(clientes, use_container_width=True)

    st.markdown("---")
    st.subheader("➕ Registrar Nuevo Cliente")
    with st.form("nuevo_cliente_form"):
        ncl_nombre = st.text_input("Nombre del Cliente")
        ncl_tel = st.text_input("Teléfono / WhatsApp")
        ncl_dir = st.text_area("Dirección completa para entrega en moto")
        ncl_notas = st.text_input("Referencias de ubicación o gustos")

        if st.form_submit_button("Guardar Cliente"):
            cur = conn.cursor()
            cur.execute("INSERT INTO clientes (nombre, telefono, direccion, notas) VALUES (?, ?, ?, ?)", (ncl_nombre, ncl_tel, ncl_dir, ncl_notas))
            conn.commit()
            conn.close()
            st.success("¡Cliente registrado con éxito!")
            st.rerun()
    conn.close()

# ----------------------------------------------------
# 6. VENTAS Y FINANZAS (HISTORIAL DIARIO, SEMANAL, MENSUAL)
# ----------------------------------------------------
elif menu == "💰 Ventas y Finanzas":
    st.markdown('<p class="main-header">💰 Reporte de Ventas y Finanzas</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Filtros por periodo (Diario, Semanal, Mensual) y margen de utilidad</p>', unsafe_allow_html=True)

    conn = get_connection()
    ventas_df = pd.read_sql("SELECT * FROM ventas ORDER BY fecha_hora DESC", conn)

    if len(ventas_df) > 0:
        periodo = st.radio("Seleccionar Periodo de Reporte", ["Diario (Hoy)", "Semanal (Últimos 7 días)", "Mensual (Último mes)", "Histórico Completo"])

        ventas_df['fecha_dt'] = pd.to_datetime(ventas_df['fecha_hora'])
        hoy = datetime.now()

        if periodo == "Diario (Hoy)":
            ventas_filtradas = ventas_df[ventas_df['fecha_dt'].dt.date == hoy.date()]
        elif periodo == "Semanal (Últimos 7 días)":
            hace_7 = hoy - timedelta(days=7)
            ventas_filtradas = ventas_df[ventas_df['fecha_dt'] >= hace_7]
        elif periodo == "Mensual (Último mes)":
            hace_30 = hoy - timedelta(days=30)
            ventas_filtradas = ventas_df[ventas_df['fecha_dt'] >= hace_30]
        else:
            ventas_filtradas = ventas_df

        t_ing = ventas_filtradas['total_venta'].sum()
        t_cos = ventas_filtradas['costo_total'].sum()
        t_util = ventas_filtradas['utilidad_neta'].sum()
        margen_porc = (t_util / t_ing * 100) if t_ing > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ingresos Totales", f"${t_ing:.2f}")
        c2.metric("Costos Totales", f"${t_cos:.2f}")
        c3.metric("Utilidad Neta", f"${t_util:.2f}")
        c4.metric("Margen de Utilidad", f"{margen_porc:.1f}%")

        st.markdown("---")
        st.subheader("📋 Detalle de Tickets del Periodo")
        st.dataframe(ventas_filtradas[['folio', 'fecha_hora', 'total_venta', 'costo_total', 'utilidad_neta', 'metodo_pago', 'notas']], use_container_width=True)
    else:
        st.info("No hay ventas registradas aún.")
    conn.close()

# ----------------------------------------------------
# 7. REPORTES Y UTILIDAD
# ----------------------------------------------------
elif menu == "📊 Reportes y Utilidad":
    st.markdown('<p class="main-header">📊 Análisis de Utilidad y Rendimiento</p>', unsafe_allow_html=True)
    conn = get_connection()
    inversiones_total = conn.execute("SELECT SUM(monto) FROM inversiones").fetchone()[0] or 0.0
    ventas_total = conn.execute("SELECT SUM(utilidad_neta) FROM ventas").fetchone()[0] or 0.0

    st.metric("Inversión Inicial Total", f"${inversiones_total:.2f}")
    st.metric("Utilidad Neta Generada Histórica", f"${ventas_total:.2f}")
    
    retorno = (ventas_total / inversiones_total * 100) if inversiones_total > 0 else 0
    st.metric("Retorno de Inversión (ROI)", f"{retorno:.1f}%")
    conn.close()

# ----------------------------------------------------
# 8. GESTIÓN DE USUARIOS Y PERMISOS
# ----------------------------------------------------
elif menu == "⚙️ Gestión de Usuarios":
    if st.session_state.user['rol'] != 'Administrador':
        st.error("Acceso restringido solo al Administrador principal.")
    else:
        st.markdown('<p class="main-header">⚙️ Gestión de Usuarios y Permisos</p>', unsafe_allow_html=True)
        conn = get_connection()
        usuarios = pd.read_sql("SELECT id, username, rol, nombre FROM usuarios", conn)
        st.dataframe(usuarios, use_container_width=True)

        st.markdown("---")
        st.subheader("➕ Crear Nuevo Usuario")
        with st.form("nuevo_usuario_form"):
            nu_user = st.text_input("Nombre de Usuario (login)")
            nu_pass = st.text_input("Contraseña", type="password")
            nu_rol = st.selectbox("Rol", ["Socio", "Operador"])
            nu_nombre = st.text_input("Nombre Completo")

            if st.form_submit_button("Crear Usuario"):
                try:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO usuarios (username, password, rol, nombre) VALUES (?, ?, ?, ?)", (nu_user, nu_pass, nu_rol, nu_nombre))
                    conn.commit()
                    st.success("¡Usuario creado con éxito!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: El nombre de usuario ya existe o datos inválidos.")
        conn.close()
