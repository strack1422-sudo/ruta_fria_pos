import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ruta_fria.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

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

# Menú lateral
st.sidebar.image("https://img.icons8.com/color/96/cold-drink.png", width=80)
st.sidebar.title("Ruta Fría POS")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegación",
    ["🛒 Punto de Venta (POS)", "📦 Inventario de Insumos", "🍔 Productos y Recetas", "🎁 Combos y Paquetes", "💰 Ventas y Finanzas", "📊 Inversiones y Gastos"]
)

# ----------------------------------------------------
# 1. PUNTO DE VENTA (POS)
# ----------------------------------------------------
if menu == "🛒 Punto de Venta (POS)":
    st.markdown('<p class="main-header">🧊 Punto de Venta - Ruta Fría</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Caja rápida para venta de bebidas, clamatos, frutimiches y combos</p>', unsafe_allow_html=True)

    conn = get_connection()
    
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
    st.subheader("🛒 Resumen de Ticket Actual")

    if len(st.session_state.carrito) > 0:
        for i, item in enumerate(st.session_state.carrito):
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            c1.write(f"**{item['nombre']}** ({item['tipo']})")
            c2.write(f"${item['precio']:.2f}")
            
            nueva_cant = c3.number_input("Cant", value=item['cantidad'], min_value=1, key=f"cant_{i}")
            st.session_state.carrito[i]['cantidad'] = nueva_cant
            
            subtotal = item['precio'] * nueva_cant
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
        notas_venta = st.text_input("Notas o Nombre de Cliente (opcional)")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🚨 Limpiar Carrito", type="secondary"):
                st.session_state.carrito = []
                st.rerun()
        with col_b2:
            if st.button("✅ Cobrar y Registrar Venta", type="primary"):
                folio = f"RF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO ventas (folio, fecha_hora, total_venta, costo_total, utilidad_neta, metodo_pago, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (folio, fecha_hora, total_general, costo_general, utilidad_estimada, metodo_pago, notas_venta))
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
# 2. INVENTARIO DE INSUMOS (CON EDICIÓN Y ELIMINACIÓN LIBRE)
# ----------------------------------------------------
elif menu == "📦 Inventario de Insumos":
    st.markdown('<p class="main-header">📦 Control Total de Insumos y Materia Prima</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Edita, corrige nombres, unidades, stock o elimina insumos libremente</p>', unsafe_allow_html=True)

    conn = get_connection()
    insumos_list = conn.execute("SELECT * FROM insumos").fetchall()

    st.subheader("📝 Edición Rápida y Eliminación de Insumos")
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
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM insumos WHERE id = ?", (ins['id'],))
                    cursor.execute("DELETE FROM recetas WHERE insumo_id = ?", (ins['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Insumo eliminado del sistema.")
                    st.rerun()

    st.markdown("---")
    st.subheader("➕ Agregar Nuevo Insumo desde Cero")
    with st.form("form_nuevo_insumo"):
        n_nom = st.text_input("Nombre del nuevo insumo")
        n_cat = st.text_input("Categoría", value="General")
        n_uni = st.text_input("Unidad (ml, g, pza)", value="pza")
        n_costo = st.number_input("Costo por unidad base ($)", min_value=0.0, value=10.0)
        n_stock = st.number_input("Stock inicial", min_value=0.0, value=10.0)
        n_min = st.number_input("Stock mínimo alerta", value=2.0)
        n_prov = st.text_input("Proveedor", value="Local")

        if st.form_submit_button("Crear Insumo"):
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO insumos (nombre, categoria, unidad, costo_unidad, stock_actual, stock_minimo, proveedor, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (n_nom, n_cat, n_uni, n_costo, n_stock, n_min, n_prov, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("¡Insumo creado con éxito!")
            st.rerun()

    conn.close()

# ----------------------------------------------------
# 3. PRODUCTOS Y RECETAS (CON EDICIÓN Y ELIMINACIÓN)
# ----------------------------------------------------
elif menu == "🍔 Productos y Recetas":
    st.markdown('<p class="main-header">🍔 Catálogo de Productos, Recetas y Costos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Edita precios, descripciones o elimina productos libremente</p>', unsafe_allow_html=True)

    conn = get_connection()
    productos_list = conn.execute("SELECT * FROM productos").fetchall()

    for prod in productos_list:
        with st.expander(f"🥤 {prod['nombre']} - Venta: ${prod['precio_venta']:.2f} (Costo: ${prod['costo_calculado']:.2f})"):
            with st.form(f"form_edit_prod_{prod['id']}"):
                p_nom = st.text_input("Nombre del Producto", value=prod['nombre'], key=f"pn_{prod['id']}")
                p_cat = st.text_input("Categoría", value=prod['categoria'], key=f"pc_{prod['id']}")
                p_precio = st.number_input("Precio de Venta ($)", value=float(prod['precio_venta']), key=f"pp_{prod['id']}")
                p_desc = st.text_area("Descripción", value=str(prod['descripcion'] or ''), key=f"pd_{prod['id']}")

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    b_save = st.form_submit_button("💾 Guardar Producto")
                with col_p2:
                    b_del = st.form_submit_button("❌ Eliminar Producto")

                if b_save:
                    cursor = conn.cursor()
                    cursor.execute("""
                    UPDATE productos SET nombre = ?, categoria = ?, precio_venta = ?, descripcion = ? WHERE id = ?
                    """, (p_nom, p_cat, p_precio, p_desc, prod['id']))
                    conn.commit()
                    conn.close()
                    st.success("¡Producto actualizado!")
                    st.rerun()

                if b_del:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM productos WHERE id = ?", (prod['id'],))
                    cursor.execute("DELETE FROM recetas WHERE producto_id = ?", (prod['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Producto eliminado.")
                    st.rerun()

    st.markdown("---")
    st.subheader("➕ Crear Nuevo Producto")
    with st.form("nuevo_prod_form"):
        np_nom = st.text_input("Nombre del Producto / Bebida")
        np_cat = st.text_input("Categoría", value="Bebidas")
        np_precio = st.number_input("Precio de Venta ($)", min_value=1.0, value=70.0)
        np_desc = st.text_area("Descripción de preparación")

        if st.form_submit_button("Crear Producto Base"):
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO productos (nombre, categoria, precio_venta, descripcion, activo)
            VALUES (?, ?, ?, ?, 1)
            """, (np_nom, np_cat, np_precio, np_desc))
            conn.commit()
            conn.close()
            st.success("¡Producto creado con éxito!")
            st.rerun()

    conn.close()

# ----------------------------------------------------
# 4. COMBOS Y PAQUETES
# ----------------------------------------------------
elif menu == "🎁 Combos y Paquetes":
    st.markdown('<p class="main-header">🎁 Combos y Paquetes Estratégicos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Gestión de paquetes promocionales</p>', unsafe_allow_html=True)

    conn = get_connection()
    combos = conn.execute("SELECT * FROM combos").fetchall()

    for combo in combos:
        with st.expander(f"📦 {combo['nombre']} - Precio Combo: ${combo['precio_combo']:.2f}"):
            with st.form(f"form_combo_{combo['id']}"):
                c_nom = st.text_input("Nombre del Combo", value=combo['nombre'], key=f"cn_{combo['id']}")
                c_desc = st.text_input("Descripción", value=combo['descripcion'], key=f"cd_{combo['id']}")
                c_reg = st.number_input("Precio Regular ($)", value=float(combo['precio_regular']), key=f"cr_{combo['id']}")
                c_com = st.number_input("Precio Combo ($)", value=float(combo['precio_combo']), key=f"cc_{combo['id']}")

                b_sc = st.form_submit_button("💾 Actualizar Combo")
                b_dc = st.form_submit_button("❌ Eliminar Combo")

                if b_sc:
                    desc_p = ((c_reg - c_com) / c_reg) * 100 if c_reg > 0 else 0
                    cursor = conn.cursor()
                    cursor.execute("""
                    UPDATE combos SET nombre = ?, descripcion = ?, precio_regular = ?, precio_combo = ?, descuento_porcentaje = ? WHERE id = ?
                    """, (c_nom, c_desc, c_reg, c_com, desc_p, combo['id']))
                    conn.commit()
                    conn.close()
                    st.success("¡Combo actualizado!")
                    st.rerun()

                if b_dc:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM combos WHERE id = ?", (combo['id'],))
                    cursor.execute("DELETE FROM combo_items WHERE combo_id = ?", (combo['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Combo eliminado.")
                    st.rerun()

    conn.close()

# ----------------------------------------------------
# 5. VENTAS Y FINANZAS
# ----------------------------------------------------
elif menu == "💰 Ventas y Finanzas":
    st.markdown('<p class="main-header">💰 Reporte de Ventas y Utilidades</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Historial de tickets cobrados y opción de eliminar tickets erróneos</p>', unsafe_allow_html=True)

    conn = get_connection()
    ventas = pd.read_sql("SELECT * FROM ventas ORDER BY fecha_hora DESC", conn)

    if len(ventas) > 0:
        t_ingresos = ventas['total_venta'].sum()
        t_costos = ventas['costo_total'].sum()
        t_utilidad = ventas['utilidad_neta'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Ingresos Totales", f"${t_ingresos:.2f}")
        col2.metric("Costo de Venta Total", f"${t_costos:.2f}")
        col3.metric("Utilidad Neta Acumulada", f"${t_utilidad:.2f}")

        st.markdown("---")
        st.subheader("📋 Historial y Cancelación de Tickets")
        ventas_raw = conn.execute("SELECT * FROM ventas ORDER BY fecha_hora DESC").fetchall()
        for v in ventas_raw:
            with st.expander(f"🎫 Folio: {v['folio']} | Fecha: {v['fecha_hora']} | Total: ${v['total_venta']:.2f}"):
                st.write(f"**Método de Pago:** {v['metodo_pago']} | **Notas:** {v['notas']}")
                st.write(f"**Costo:** ${v['costo_total']:.2f} | **Utilidad:** ${v['utilidad_neta']:.2f}")
                
                if st.button(f"❌ Cancelar / Eliminar Venta {v['folio']}", key=f"del_v_{v['id']}"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM ventas WHERE id = ?", (v['id'],))
                    cursor.execute("DELETE FROM venta_detalles WHERE venta_id = ?", (v['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Venta eliminada del historial.")
                    st.rerun()
    else:
        st.info("Aún no hay ventas registradas.")

    conn.close()

# ----------------------------------------------------
# 6. INVERSIONES Y GASTOS
# ----------------------------------------------------
elif menu == "📊 Inversiones y Gastos":
    st.markdown('<p class="main-header">📊 Inversión Inicial y Gastos Operativos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Control de capital invertido</p>', unsafe_allow_html=True)

    conn = get_connection()
    inversiones = pd.read_sql("SELECT * FROM inversiones", conn)
    
    if len(inversiones) > 0:
        total_inversion = inversiones['monto'].sum()
        st.metric("Inversión Total Inicial", f"${total_inversion:.2f}")
        
        for inv in conn.execute("SELECT * FROM inversiones").fetchall():
            with st.expander(f"💡 {inv['concepto']} - ${inv['monto']:.2f} ({inv['fecha']})"):
                if st.button(f"❌ Eliminar Inversión #{inv['id']}", key=f"del_inv_{inv['id']}"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM inversiones WHERE id = ?", (inv['id'],))
                    conn.commit()
                    conn.close()
                    st.warning("Inversión eliminada.")
                    st.rerun()

    conn.close()
