import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ruta_fria.db")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permisos_rol (
        rol TEXT PRIMARY KEY,
        puede_vender INTEGER,
        puede_editar_inventario INTEGER,
        puede_ver_finanzas INTEGER,
        puede_gestionar_usuarios INTEGER
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
    
    cursor.execute("INSERT OR IGNORE INTO permisos_rol (rol, puede_vender, puede_editar_inventario, puede_ver_finanzas, puede_gestionar_usuarios) VALUES ('Administrador', 1, 1, 1, 1)")
    cursor.execute("INSERT OR IGNORE INTO permisos_rol (rol, puede_vender, puede_editar_inventario, puede_ver_finanzas, puede_gestionar_usuarios) VALUES ('Socio', 1, 1, 1, 0)")
    cursor.execute("INSERT OR IGNORE INTO permisos_rol (rol, puede_vender, puede_editar_inventario, puede_ver_finanzas, puede_gestionar_usuarios) VALUES ('Operador', 1, 0, 0, 0)")

    conn.commit()
    conn.close()

init_tables()

st.set_page_config(
    page_title="Ruta Fría - Enterprise POS & Management",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS limpios y seguros (sin ocultar texto en inputs ni selectboxes)
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.025em;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 24px;
    }
    .enterprise-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

def get_config(clave):
    conn = get_connection()
    row = conn.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,)).fetchone()
    conn.close()
    return row['valor'] if row else None

def verificar_permiso(permiso_key):
    if not st.session_state.user:
        return False
    if st.session_state.user['rol'] == 'Administrador':
        return True
    conn = get_connection()
    row = conn.execute(f"SELECT {permiso_key} FROM permisos_rol WHERE rol = ?", (st.session_state.user['rol'],)).fetchone()
    conn.close()
    return bool(row[permiso_key]) if row else False

if st.session_state.user is None:
    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        logo_file = get_config('logo_path')
        logo_path = os.path.join(os.path.dirname(__file__), logo_file if logo_file else "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=220)
        else:
            st.image("https://img.icons8.com/color/96/cold-drink.png", width=100)
        
        st.markdown("<h1 style='text-align: center; color: #0f172a; font-weight: 900;'>Ruta Fría POS</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #475569; font-size: 1rem;'>Plataforma Comercial de Alto Rendimiento</p>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="enterprise-card">', unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("Usuario Corporativo")
                password = st.text_input("Contraseña de Acceso", type="password")
                submit_login = st.form_submit_button("Iniciar Sesión Segura", use_container_width=True)
                
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
                        st.success(f"Bienvenido, {user_row['nombre']}")
                        st.rerun()
                    else:
                        st.error("Credenciales inválidas.")
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Menú lateral fijo y expandido con todas las secciones operativas visibles
logo_file = get_config('logo_path')
logo_path = os.path.join(os.path.dirname(__file__), logo_file if logo_file else "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=150)

st.sidebar.markdown(f"**{st.session_state.user['nombre']}**\n\n`Rol: {st.session_state.user['rol']}`")
st.sidebar.markdown("---")

menu_options = {}
if verificar_permiso('puede_vender'):
    menu_options["Punto de Venta"] = ":material/point_of_sale:"
if verificar_permiso('puede_editar_inventario'):
    menu_options.update({
        "Inventario": ":material/inventory_2:",
        "Productos y Recetas": ":material/receipt_long:",
        "Combos y Paquetes": ":material/local_offer:"
    })

menu_options["Clientes y Domicilios"] = ":material/groups:"

if verificar_permiso('puede_ver_finanzas'):
    menu_options.update({
        "Ventas y Tickets": ":material/payments:",
        "Reportes y Balances": ":material/analytics:"
    })

menu_options["Configuración"] = ":material/settings:"

if verificar_permiso('puede_gestionar_usuarios'):
    menu_options["Gestión de Usuarios"] = ":material/admin_panel_settings:"

selected_label = st.sidebar.radio(
    "Navegación Principal",
    options=list(menu_options.keys()),
    format_func=lambda x: f"{menu_options[x]}  {x}"
)

st.sidebar.markdown("---")
if st.sidebar.button("Cerrar Sesión", use_container_width=True):
    st.session_state.user = None
    st.session_state.carrito = []
    st.rerun()

menu = selected_label

# ----------------------------------------------------
# 1. PUNTO DE VENTA (POS)
# ----------------------------------------------------
if menu == "Punto de Venta":
    st.markdown('<p class="main-title">Punto de Venta (POS)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Terminal comercial para mostrador y entregas a domicilio en moto</p>', unsafe_allow_html=True)

    conn = get_connection()
    clientes_rows = conn.execute("SELECT * FROM clientes").fetchall()
    cliente_opciones = ["Venta General / Mostrador"] + [f"{c['nombre']} ({c['telefono'] or 'Sin tel'})" for c in clientes_rows]
    
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        sel_cliente_str = st.selectbox("Seleccionar Cliente Corporativo", cliente_opciones)
    with col_c2:
        st.markdown("<div style='height: 27px;'></div>", unsafe_allow_html=True)
        if st.button("Nuevo Cliente", use_container_width=True):
            st.session_state.show_quick_client = True

    cliente_seleccionado_obj = None
    if sel_cliente_str != "Venta General / Mostrador":
        for c in clientes_rows:
            if f"{c['nombre']} ({c['telefono'] or 'Sin tel'})" == sel_cliente_str:
                cliente_seleccionado_obj = c
                break
        if cliente_seleccionado_obj:
            st.info(f"**Dirección de Envío:** {cliente_seleccionado_obj['direccion'] or 'No especificada'} | **Contacto:** {cliente_seleccionado_obj['telefono'] or 'N/A'}")

    if st.session_state.get('show_quick_client', False):
        with st.form("quick_client_form"):
            st.markdown("##### Registro Rápido de Cliente")
            qc_nombre = st.text_input("Nombre Completo")
            qc_tel = st.text_input("Teléfono / WhatsApp")
            qc_dir = st.text_area("Dirección para Repartidor")
            if st.form_submit_button("Guardar Cliente"):
                if qc_nombre:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO clientes (nombre, telefono, direccion) VALUES (?, ?, ?)", (qc_nombre, qc_tel, qc_dir))
                    conn.commit()
                    st.success("¡Cliente guardado!")
                    st.session_state.show_quick_client = False
                    st.rerun()

    tab_prod, tab_combo = st.tabs(["Productos Individuales", "Paquetes y Combos"])

    if "carrito" not in st.session_state:
        st.session_state.carrito = []

    with tab_prod:
        productos = conn.execute("SELECT * FROM productos WHERE activo = 1").fetchall()
        cols = st.columns(3)
        for idx, prod in enumerate(productos):
            with cols[idx % 3]:
                img_path = prod['imagen_url'] if 'imagen_url' in prod.keys() else None
                if img_path and os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                
                st.markdown(f"""
                <div class="enterprise-card">
                    <h4 style="color: #0284c7; margin-top: 0; margin-bottom: 6px;">{prod['nombre']}</h4>
                    <p style="color: #475569; font-size: 0.85rem; min-height: 38px;">{prod['descripcion']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                        <span style="font-size: 1.2rem; font-weight: 700; color: #16a34a;">${prod['precio_venta']:.2f}</span>
                        <span style="font-size: 0.75rem; color: #64748b;">Costo: ${prod['costo_calculado']:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"Personalizar / Añadir##{prod['id']}"):
                    with st.form(f"form_add_{prod['id']}"):
                        cant_prod = st.number_input("Cantidad", min_value=1, value=1, key=f"cp_{prod['id']}")
                        insumos_disp = conn.execute("SELECT * FROM insumos").fetchall()
                        ins_nombres = [i['nombre'] for i in insumos_disp]
                        extra_elegido = st.selectbox("Ingrediente Extra", ["Ninguno"] + ins_nombres, key=f"ext_{prod['id']}")
                        cantidad_extra = st.number_input("Cantidad extra", min_value=0.0, value=0.0, key=f"cext_{prod['id']}")
                        nota_personalizada = st.text_input("Nota especial", key=f"np_{prod['id']}")

                        if st.form_submit_button("Agregar al Carrito", use_container_width=True):
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
                            st.success("Añadido al ticket.")
                            st.rerun()

    with tab_combo:
        combos = conn.execute("SELECT * FROM combos WHERE activo = 1").fetchall()
        cols_c = st.columns(2)
        for idx, combo in enumerate(combos):
            with cols_c[idx % 2]:
                st.markdown(f"""
                <div class="enterprise-card" style="border-left: 4px solid #0284c7;">
                    <h4 style="color: #0f172a; margin-top: 0; margin-bottom: 6px;">{combo['nombre']}</h4>
                    <p style="color: #475569; font-size: 0.85rem; min-height: 38px;">{combo['descripcion']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                        <div>
                            <span style="text-decoration: line-through; color: #94a3b8; font-size: 0.9rem;">${combo['precio_regular']:.2f}</span>
                            <span style="font-size: 1.2rem; font-weight: 700; color: #16a34a; margin-left: 8px;">${combo['precio_combo']:.2f}</span>
                        </div>
                        <span style="background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">Ahorro {combo['descuento_porcentaje']:.1f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Añadir Paquete##{combo['id']}", key=f"btn_c_{combo['id']}", use_container_width=True):
                    st.session_state.carrito.append({
                        "tipo": "combo",
                        "id": combo['id'],
                        "nombre": combo['nombre'],
                        "precio": combo['precio_combo'],
                        "costo": combo['costo_total'],
                        "cantidad": 1
                    })
                    st.success("Paquete añadido.")
                    st.rerun()

    st.markdown("---")
    st.markdown("### Resumen del Ticket Activo")

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
            
            if c5.button("Quitar##del_cart_" + str(i), key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()

        total_general = sum(item['precio'] * item['cantidad'] for item in st.session_state.carrito)
        costo_general = sum(item['costo'] * item['cantidad'] for item in st.session_state.carrito)
        utilidad_estimada = total_general - costo_general

        st.markdown(f"""
        <div class="enterprise-card" style="background: #ffffff; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p style="margin: 0; color: #475569; font-size: 0.9rem;">Utilidad Neta Estimada: <strong style="color: #16a34a;">${utilidad_estimada:.2f}</strong></p>
            </div>
            <div>
                <h2 style="margin: 0; color: #0f172a;">Total a Cobrar: <span style="color: #16a34a;">${total_general:.2f}</span></h2>
            </div>
        </div>
        """, unsafe_allow_html=True)

        metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia / QR", "Tarjeta"])
        notas_venta = st.text_input("Observaciones o notas del ticket")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Vaciar Carrito", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()
        with col_b2:
            if st.button("Procesar y Cobrar Venta", type="primary", use_container_width=True):
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

                st.success(f"¡Venta procesada con éxito! Folio: {folio}")
                st.session_state.carrito = []
                st.balloons()
    else:
        st.info("El ticket actual se encuentra vacío.")

    conn.close()

# ----------------------------------------------------
# 2. INVENTARIO
# ----------------------------------------------------
elif menu == "Inventario":
    st.markdown('<p class="main-title">Control de Inventario y Costos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Gestión de insumos, materias primas y control de stock mínimo</p>', unsafe_allow_html=True)

    conn = get_connection()
    insumos_list = conn.execute("SELECT * FROM insumos").fetchall()

    for idx, ins in enumerate(insumos_list):
        with st.expander(f"{ins['nombre']} — Stock: {ins['stock_actual']} {ins['unidad']}##{ins['id']}"):
            with st.form(f"form_edit_insumo_{ins['id']}"):
                nuevo_nombre = st.text_input("Nombre", value=ins['nombre'], key=f"ni_{ins['id']}")
                nueva_cat = st.text_input("Categoría", value=ins['categoria'], key=f"ci_{ins['id']}")
                nueva_unidad = st.text_input("Unidad", value=ins['unidad'], key=f"ui_{ins['id']}")
                nuevo_costo = st.number_input("Costo Unitario ($)", value=float(ins['costo_unidad']), format="%.4f", key=f"co_{ins['id']}")
                nuevo_stock = st.number_input("Stock Actual", value=float(ins['stock_actual']), key=f"st_{ins['id']}")
                nuevo_min = st.number_input("Stock Mínimo", value=float(ins['stock_minimo']), key=f"mi_{ins['id']}")
                nuevo_prov = st.text_input("Proveedor", value=str(ins['proveedor'] or ''), key=f"pr_{ins['id']}")

                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    b_ins_save = st.form_submit_button("Guardar Cambios", use_container_width=True)
                with col_i2:
                    b_ins_del = st.form_submit_button("Eliminar Insumo", use_container_width=True)

                if b_ins_save:
                    cur = conn.cursor()
                    cur.execute("""
                    UPDATE insumos SET nombre = ?, categoria = ?, unidad = ?, costo_unidad = ?, stock_actual = ?, stock_minimo = ?, proveedor = ?, fecha_actualizacion = ?
                    WHERE id = ?
                    """, (nuevo_nombre, nueva_cat, nueva_unidad, nuevo_costo, nuevo_stock, nuevo_min, nuevo_prov, datetime.now().strftime("%Y-%m-%d %H:%M"), ins['id']))
                    conn.commit()
                    conn.close()
                    st.success("Insumo actualizado.")
                    st.rerun()

                if b_ins_del:
                    if st.session_state.user['rol'] == 'Operador':
                        st.error("Permisos insuficientes.")
                    else:
                        cur = conn.cursor()
                        cur.execute("DELETE FROM insumos WHERE id = ?", (ins['id'],))
                        conn.commit()
                        conn.close()
                        st.warning("Insumo eliminado.")
                        st.rerun()
    conn.close()

# ----------------------------------------------------
# 3. PRODUCTOS Y RECETAS
# ----------------------------------------------------
elif menu == "Productos y Recetas":
    st.markdown('<p class="main-title">Catálogo de Productos y Recetas (Escandallo)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Estructura de costos, porciones y carga de fotografía oficial del producto</p>', unsafe_allow_html=True)

    conn = get_connection()
    productos_list = conn.execute("SELECT * FROM productos").fetchall()

    for idx, prod in enumerate(productos_list):
        with st.expander(f"{prod['nombre']} — Venta: ${prod['precio_venta']:.2f}##{prod['id']}"):
            img_curr = prod['imagen_url'] if 'imagen_url' in prod.keys() else None
            if img_curr and os.path.exists(img_curr):
                st.image(img_curr, width=150)

            with st.form(f"form_prod_{prod['id']}"):
                p_nom = st.text_input("Nombre", value=prod['nombre'], key=f"pn_{prod['id']}")
                p_cat = st.text_input("Categoría", value=prod['categoria'], key=f"pc_{prod['id']}")
                p_precio = st.number_input("Precio Venta ($)", value=float(prod['precio_venta']), key=f"pp_{prod['id']}")
                p_desc = st.text_area("Descripción", value=str(prod['descripcion'] or ''), key=f"pd_{prod['id']}")
                
                foto_subida = st.file_uploader("Subir fotografía corporativa (PNG / JPG)", type=["png", "jpg", "jpeg"], key=f"foto_{prod['id']}")

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    b_p_save = st.form_submit_button("Guardar Cambios", use_container_width=True)
                with col_p2:
                    b_p_del = st.form_submit_button("Eliminar Producto", use_container_width=True)

                if b_p_save:
                    ruta_guardada = img_curr
                    if foto_subida is not None:
                        filename = f"prod_{prod['id']}_{foto_subida.name}"
                        ruta_guardada = os.path.join(UPLOAD_DIR, filename)
                        with open(ruta_guardada, "wb") as f:
                            f.write(foto_subida.getbuffer())

                    cur = conn.cursor()
                    cur.execute("UPDATE productos SET nombre = ?, categoria = ?, precio_venta = ?, descripcion = ?, imagen_url = ? WHERE id = ?", 
                                (p_nom, p_cat, p_precio, p_desc, ruta_guardada, prod['id']))
                    conn.commit()
                    conn.close()
                    st.success("Producto e imagen actualizados con éxito.")
                    st.rerun()

                if b_p_del:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM productos WHERE id = ?", (prod['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Producto eliminado.")
                    st.rerun()
    conn.close()

# ----------------------------------------------------
# 4. COMBOS Y PAQUETES
# ----------------------------------------------------
elif menu == "Combos y Paquetes":
    st.markdown('<p class="main-title">Paquetes y Combos Promocionales</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Creación y configuración de estrategias comerciales por volumen</p>', unsafe_allow_html=True)

    conn = get_connection()
    combos = conn.execute("SELECT * FROM combos").fetchall()

    for idx, combo in enumerate(combos):
        with st.expander(f"{combo['nombre']} — Precio: ${combo['precio_combo']:.2f}##combo_{combo['id']}"):
            with st.form(f"combo_edit_{combo['id']}"):
                c_nom = st.text_input("Nombre del Combo", value=combo['nombre'], key=f"cn_{combo['id']}")
                c_desc = st.text_input("Descripción", value=combo['descripcion'], key=f"cd_{combo['id']}")
                c_reg = st.number_input("Precio Regular ($)", value=float(combo['precio_regular']), key=f"cr_{combo['id']}")
                c_com = st.number_input("Precio Combo ($)", value=float(combo['precio_combo']), key=f"cc_{combo['id']}")

                col_cb1, col_cb2 = st.columns(2)
                with col_cb1:
                    b_cs = st.form_submit_button("Actualizar", use_container_width=True)
                with col_cb2:
                    b_cd = st.form_submit_button("Eliminar", use_container_width=True)

                if b_cs:
                    desc_p = ((c_reg - c_com) / c_reg) * 100 if c_reg > 0 else 0
                    cur = conn.cursor()
                    cur.execute("UPDATE combos SET nombre = ?, descripcion = ?, precio_regular = ?, precio_combo = ?, descuento_porcentaje = ? WHERE id = ?",
                                (c_nom, c_desc, c_reg, c_com, desc_p, combo['id']))
                    conn.commit()
                    conn.close()
                    st.success("Combo actualizado.")
                    st.rerun()

                if b_cd:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM combos WHERE id = ?", (combo['id'],))
                    cur.execute("DELETE FROM combo_items WHERE combo_id = ?", (combo['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Combo eliminado.")
                    st.rerun()
    conn.close()

# ----------------------------------------------------
# 5. CLIENTES Y DOMICILIOS
# ----------------------------------------------------
elif menu == "Clientes y Domicilios":
    st.markdown('<p class="main-title">Directorio de Clientes y Domicilios</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Gestión de contactos para logística de entregas en moto</p>', unsafe_allow_html=True)

    conn = get_connection()
    clientes = conn.execute("SELECT * FROM clientes").fetchall()

    for idx, cli in enumerate(clientes):
        with st.expander(f"{cli['nombre']} — Tel: {cli['telefono'] or 'N/A'}##cli_{cli['id']}"):
            with st.form(f"form_cli_{cli['id']}"):
                cl_nom = st.text_input("Nombre", value=cli['nombre'], key=f"clin_{cli['id']}")
                cl_tel = st.text_input("Teléfono", value=str(cli['telefono'] or ''), key=f"clt_{cli['id']}")
                cl_dir = st.text_area("Dirección", value=str(cli['direccion'] or ''), key=f"cld_{cli['id']}")
                cl_not = st.text_input("Notas", value=str(cli['notas'] or ''), key=f"cln_{cli['id']}")

                col_cl1, col_cl2 = st.columns(2)
                with col_cl1:
                    b_cl_save = st.form_submit_button("Guardar", use_container_width=True)
                with col_cl2:
                    b_cl_del = st.form_submit_button("Eliminar", use_container_width=True)

                if b_cl_save:
                    cur = conn.cursor()
                    cur.execute("UPDATE clientes SET nombre = ?, telefono = ?, direccion = ?, notas = ? WHERE id = ?", (cl_nom, cl_tel, cl_dir, cl_not, cli['id']))
                    conn.commit()
                    conn.close()
                    st.success("Cliente actualizado.")
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
elif menu == "Ventas y Tickets":
    st.markdown('<p class="main-title">Historial de Ventas y Tickets</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Registro de operaciones comerciales y auditoría</p>', unsafe_allow_html=True)

    conn = get_connection()
    ventas_df = pd.read_sql("SELECT * FROM ventas ORDER BY fecha_hora DESC", conn)

    if len(ventas_df) > 0:
        periodo = st.radio("Periodo de consulta", ["Diario (Hoy)", "Semanal (7 días)", "Mensual (30 días)", "Histórico"])
        ventas_df['fecha_dt'] = pd.to_datetime(ventas_df['fecha_hora'])
        hoy = datetime.now()

        if periodo == "Diario (Hoy)":
            ventas_filt = ventas_df[ventas_df['fecha_dt'].dt.date == hoy.date()]
        elif periodo == "Semanal (7 días)":
            ventas_filt = ventas_df[ventas_df['fecha_dt'] >= hoy - timedelta(days=7)]
        elif periodo == "Mensual (30 días)":
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
        st.info("No hay ventas registradas.")
    conn.close()

# ----------------------------------------------------
# 7. REPORTES Y BALANCES
# ----------------------------------------------------
elif menu == "Reportes y Balances":
    st.markdown('<p class="main-title">Reportes y Balances Financieros</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Análisis corporativo por rango de fechas personalizado</p>', unsafe_allow_html=True)

    conn = get_connection()
    ventas_df = pd.read_sql("SELECT * FROM ventas", conn)
    inversiones_df = pd.read_sql("SELECT * FROM inversiones", conn)
    conn.close()

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        fecha_inicio = st.date_input("Fecha Inicial", value=datetime.now().date() - timedelta(days=30))
    with col_d2:
        fecha_fin = st.date_input("Fecha Final", value=datetime.now().date())

    if len(ventas_df) > 0:
        ventas_df['fecha_dt'] = pd.to_datetime(ventas_df['fecha_hora']).dt.date
        mask_v = (ventas_df['fecha_dt'] >= fecha_inicio) & (ventas_df['fecha_dt'] <= fecha_fin)
        ventas_rango = ventas_df.loc[mask_v]
        total_ingresos = ventas_rango['total_venta'].sum()
        utilidad_bruta = ventas_rango['utilidad_neta'].sum()
    else:
        ventas_rango = pd.DataFrame()
        total_ingresos = 0.0
        utilidad_bruta = 0.0

    if len(inversiones_df) > 0:
        inversiones_df['fecha_dt'] = pd.to_datetime(inversiones_df['fecha']).dt.date
        mask_i = (inversiones_df['fecha_dt'] >= fecha_inicio) & (inversiones_df['fecha_dt'] <= fecha_fin)
        inversiones_rango = inversiones_df.loc[mask_i]
        total_inversiones = inversiones_rango['monto'].sum()
    else:
        total_inversiones = 0.0

    balance_neto = utilidad_bruta - total_inversiones

    st.markdown("---")
    cb1, cb2, cb3, cb4 = st.columns(4)
    cb1.metric("Ingresos Totales", f"${total_ingresos:.2f}")
    cb2.metric("Utilidad Comercial", f"${utilidad_bruta:.2f}")
    cb3.metric("Gastos / Inversiones", f"${total_inversiones:.2f}")
    cb4.metric("Balance Neto", f"${balance_neto:.2f}", delta=f"{balance_neto:.2f}")

    if balance_neto >= 0:
        st.success(f"Balance Positivo: Utilidad neta de ${balance_neto:.2f} en el periodo.")
    else:
        st.error(f"Balance Negativo: Déficit de ${abs(balance_neto):.2f} en el periodo.")

    st.markdown("---")
    if len(ventas_rango) > 0:
        df_diario = ventas_rango.groupby('fecha_dt')['total_venta'].sum().reset_index()
        df_diario.columns = ['Fecha', 'Ventas ($)']
        st.bar_chart(df_diario.set_index('Fecha'))
    else:
        st.info("Sin datos para graficar en el rango seleccionado.")

# ----------------------------------------------------
# 8. CONFIGURACIÓN
# ----------------------------------------------------
elif menu == "Configuración":
    st.markdown('<p class="main-title">Configuración Corporativa y Logotipo</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Gestión y actualización de la imagen institucional de la empresa</p>', unsafe_allow_html=True)

    conn = get_connection()
    current_logo = get_config('logo_path')
    
    logo_path = os.path.join(os.path.dirname(__file__), current_logo if current_logo else "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)

    st.markdown("---")
    with st.form("config_logo_upload_form"):
        st.subheader("Cargar Nuevo Logotipo Corporativo")
        nuevo_logo_file = st.file_uploader("Seleccionar imagen institucional (PNG / JPG)", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("Actualizar y Guardar Logotipo", use_container_width=True):
            if nuevo_logo_file is not None:
                filename = f"logo_corp_{nuevo_logo_file.name}"
                ruta_logo = os.path.join(UPLOAD_DIR, filename)
                with open(ruta_logo, "wb") as f:
                    f.write(nuevo_logo_file.getbuffer())

                cur = conn.cursor()
                cur.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('logo_path', ?)", (ruta_logo,))
                conn.commit()
                conn.close()
                st.success("¡Logotipo corporativo actualizado con éxito!")
                st.rerun()
            else:
                st.warning("Por favor seleccione un archivo de imagen válido.")
    conn.close()

# ----------------------------------------------------
# 9. GESTIÓN DE USUARIOS
# ----------------------------------------------------
elif menu == "Gestión de Usuarios":
    if st.session_state.user['rol'] != 'Administrador':
        st.error("Acceso exclusivo para Administradores.")
    else:
        st.markdown('<p class="main-title">Gestión de Usuarios y Accesos</p>', unsafe_allow_html=True)
        conn = get_connection()
        
        st.subheader("Permisos por Rol")
        roles_permisos = conn.execute("SELECT * FROM permisos_rol").fetchall()

        for rp in roles_permisos:
            with st.expander(f"Rol: {rp['rol']}##rol_{rp['rol']}"):
                with st.form(f"form_permiso_{rp['rol']}"):
                    p_vende = st.checkbox("Permiso de Venta", value=bool(rp['puede_vender']), key=f"pv_{rp['rol']}")
                    p_inv = st.checkbox("Permiso de Inventario", value=bool(rp['puede_editar_inventario']), key=f"pi_{rp['rol']}")
                    p_fin = st.checkbox("Permiso de Finanzas", value=bool(rp['puede_ver_finanzas']), key=f"pf_{rp['rol']}")
                    p_usr = st.checkbox("Permiso de Usuarios", value=bool(rp['puede_gestionar_usuarios']), key=f"pu_{rp['rol']}")

                    if st.form_submit_button("Guardar Permisos"):
                        cur = conn.cursor()
                        cur.execute("""
                        UPDATE permisos_rol SET puede_vender = ?, puede_editar_inventario = ?, puede_ver_finanzas = ?, puede_gestionar_usuarios = ? WHERE rol = ?
                        """, (int(p_vende), int(p_inv), int(p_fin), int(p_usr), rp['rol']))
                        conn.commit()
                        conn.close()
                        st.success("Permisos actualizados.")
                        st.rerun()

        st.markdown("---")
        st.subheader("Directorio de Usuarios")
        usuarios_list = conn.execute("SELECT id, username, rol, nombre FROM usuarios").fetchall()

        for usr in usuarios_list:
            with st.expander(f"{usr['nombre']} ({usr['username']}) - {usr['rol']}##usr_{usr['id']}"):
                with st.form(f"form_edit_usr_{usr['id']}"):
                    e_nombre = st.text_input("Nombre", value=usr['nombre'], key=f"un_{usr['id']}")
                    e_user = st.text_input("Usuario", value=usr['username'], key=f"uu_{usr['id']}")
                    e_rol = st.selectbox("Rol", ["Administrador", "Socio", "Operador"], index=["Administrador", "Socio", "Operador"].index(usr['rol']), key=f"ur_{usr['id']}")
                    e_pass = st.text_input("Nueva Contraseña (opcional)", type="password", key=f"up_{usr['id']}")

                    col_u1, col_u2 = st.columns(2)
                    with col_u1:
                        b_u_save = st.form_submit_button("Actualizar", use_container_width=True)
                    with col_u2:
                        b_u_del = st.form_submit_button("Eliminar", use_container_width=True)

                    if b_u_save:
                        cur = conn.cursor()
                        if e_pass:
                            cur.execute("UPDATE usuarios SET nombre = ?, username = ?, rol = ?, password = ? WHERE id = ?", (e_nombre, e_user, e_rol, e_pass, usr['id']))
                        else:
                            cur.execute("UPDATE usuarios SET nombre = ?, username = ?, rol = ? WHERE id = ?", (e_nombre, e_user, e_rol, usr['id']))
                        conn.commit()
                        conn.close()
                        st.success("Usuario actualizado.")
                        st.rerun()

                    if b_u_del:
                        if usr['username'] == 'admin':
                            st.error("No se puede eliminar al admin principal.")
                        else:
                            cur = conn.cursor()
                            cur.execute("DELETE FROM usuarios WHERE id = ?", (usr['id'],))
                            conn.commit()
                            conn.close()
                            st.warning("Usuario eliminado.")
                            st.rerun()

        st.markdown("---")
        st.subheader("Crear Usuario")
        with st.form("new_user_form"):
            nu_u = st.text_input("Usuario")
            nu_p = st.text_input("Contraseña", type="password")
            nu_r = st.selectbox("Rol", ["Administrador", "Socio", "Operador"])
            nu_n = st.text_input("Nombre Completo")

            if st.form_submit_button("Crear Usuario", use_container_width=True):
                try:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO usuarios (username, password, rol, nombre) VALUES (?, ?, ?, ?)", (nu_u, nu_p, nu_r, nu_n))
                    conn.commit()
                    conn.close()
                    st.success("Usuario creado con éxito.")
                    st.rerun()
                except:
                    st.error("Error: El usuario ya existe.")
        conn.close()
