# -*- coding: utf-8 -*-
"""
Streamlit v1
═══════════════════════════════════════════════════════════════════════
Interfaz gráfica para la API de predicción inmobiliaria.
Captura los datos de una propiedad y consulta la API v1 (GET).

¿Qué hace esta app?
  1. Muestra un formulario con los 9 campos que espera el modelo.
  2. Al hacer clic en "Estimar precio", llama a GET /predict de la API v1.
  3. Muestra el precio estimado en USD.

Cómo ejecutar:
  streamlit run streamlit_v1.py

Requisitos:
  - La API v1 debe estar corriendo: python api_v1.py
  - Instalar: pip install streamlit requests
"""

# ── 1. IMPORTACIONES ────────────────────────────────────────────────────
import streamlit as st
# streamlit: librería para crear aplicaciones web interactivas de datos.
#            Permite construir dashboards y formularios sin escribir HTML/CSS/JS.
#            Cada vez que el usuario interactúa, Streamlit re-ejecuta el script
#            completo de arriba a abajo (modelo de ejecución reactivo).

import requests
# requests: librería HTTP para hacer peticiones a APIs.
#           Más simple que urllib. Usamos requests.get() para llamar a la API.


# ── 2. CONFIGURACIÓN DE LA PÁGINA ───────────────────────────────────────
# st.set_page_config() DEBE ser la primera llamada a Streamlit en el script.
# Configura el título, icono y layout de la pestaña del navegador.

st.set_page_config(
    page_title="Evaluar propiedad — v1",
    
    page_icon="🏠",
    # Emoji que aparece en la pestaña del navegador.

    layout="centered",
    # "centered": contenido centrado (más legible en pantallas anchas).
    # "wide": ocupa todo el ancho (mejor para dashboards con muchas columnas).
)

# ── 3. URL DE LA API ─────────────────────────────────────────────────────
# Hardcodeada en v1. En v2 y v3 será configurable.

API_URL = "http://localhost:8000"
# Puerto 8000: el default de FastAPI/uvicorn.
# Si cambiaste el puerto en api_v1_minima.py, actualizalo aquí.


# ── 4. TÍTULO Y DESCRIPCIÓN ─────────────────────────────────────────────
st.markdown("<h2 style='text-align: center;'>🏠 Estimador de Precios Inmobiliarios 🏢</h2>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Proyecto final de diplomado</h2>", unsafe_allow_html=True)
st.caption("Fausto Yugcha")

st.caption("Versión 1 | API v1 (GET)")
# st.caption(): texto pequeño en gris, ideal para subtítulos o notas.

st.markdown("""
Ingresar los datos de la propiedad y obtener un precio estimado de la 
propiedad basado en un modelo de **Random Forest** entrenado con datos reales
de Ecuador (Quito, Guayaquil, Manta).
""")
# st.markdown(): renderiza texto en formato Markdown (negritas, listas, etc.).

st.divider()
# st.divider(): línea horizontal separadora.


# ── 5. FORMULARIO DE ENTRADA ─────────────────────────────────────────────
# st.form() agrupa varios widgets. El form NO se re-ejecuta con cada cambio
# de un campo individual; solo se ejecuta al hacer clic en el botón submit.
# Esto evita que la API sea llamada constantemente mientras el usuario escribe.

with st.form("formulario_propiedad"):
    # with st.form("nombre"): todo lo indentado pertenece al formulario.

    # ── 5a. Características de la propiedad ──────────────────────────────
    st.subheader("📐 Características de la propiedad")
    # st.subheader(): encabezado de segundo nivel.

    # usamos columnas para organizar los campos en filas de 3.
    col1, col2, col3 = st.columns(3)
    # st.columns(3): crea 3 columnas de igual ancho.
    # col1, col2, col3 son objetos "columna" donde podemos poner widgets.

    with col1:
        bedrooms = st.number_input(
            "Habitaciones",
            # Etiqueta del campo.

            min_value=1,
            # Valor mínimo permitido en el spinner.

            max_value=20,
            # Valor máximo.

            value=3,
            # Valor por defecto.

            step=1,
            # Incremento al usar las flechas ↑↓.

            help="Número de dormitorios (1-20)",
            # Tooltip que aparece al pasar el mouse.
        )

    with col2:
        bathrooms = st.number_input(
            "Baños",
            min_value=1,
            max_value=20,
            value=2,
            step=1,
            help="Número de baños completos (1-20)",
        )

    with col3:
        parking_spots = st.number_input(
            "Estacionamientos",
            min_value=0,
            # 0 permitido: hay propiedades sin estacionamiento.

            max_value=20,
            value=2,
            step=1,
            help="Plazas de parqueadero (0-20)",
        )

    # ── 5b. Área ─────────────────────────────────────────────────────────
    construction_area = st.number_input(
        "Área de construcción (m²)",
        min_value=10.0,
        # float: permite decimales.

        max_value=10000.0,
        value=200.0,
        step=10.0,
        # Incremento de 10 en 10 m².

        format="%.1f",
        # Muestra 1 decimal en el campo.

        help="Metros cuadrados construidos (10-10,000)",
    )

    # ── 5c. Ubicación ────────────────────────────────────────────────────
    st.subheader("📍 Ubicación")

    col4, col5 = st.columns(2)
    # 2 columnas para latitud y longitud.

    with col4:
        latitude = st.number_input(
            "Latitud",
            min_value=-90.0,
            max_value=90.0,
            value=-0.18,
            # Default: Quito centro.

            step=0.01,
            format="%.4f",
            help="Coordenada de latitud (ej: Quito ≈ -0.18)",
        )

    with col5:
        longitude = st.number_input(
            "Longitud",
            min_value=-180.0,
            max_value=180.0,
            value=-78.48,
            # Default: Quito centro.

            step=0.01,
            format="%.4f",
            help="Coordenada de longitud (ej: Quito ≈ -78.48)",
        )

    # ── 5d. Ciudad ───────────────────────────────────────────────────────
    st.subheader("🏙️ Ciudad")

    # st.radio(): botones de opción mutuamente excluyentes.
    # Solo una opción puede estar seleccionada a la vez.
    ciudad = st.radio(
        "Seleccioná la ciudad donde está la propiedad:",
        options=["Quito", "Guayaquil", "Manta"],
        # Lista de opciones. El valor seleccionado es el string.

        index=0,
        # Índice de la opción seleccionada por defecto (0 = Quito).

        horizontal=True,
        # Muestra las opciones en fila en vez de columna.
    )

    # Convertir la opción seleccionada a variables one-hot (0/1).
    # El modelo espera 3 columnas binarias, no un string.
    city_guayaquil = 1 if ciudad == "Guayaquil" else 0
    city_manta = 1 if ciudad == "Manta" else 0
    city_quito = 1 if ciudad == "Quito" else 0

    # ── 5e. Botón de envío ───────────────────────────────────────────────
    st.divider()
    enviar = st.form_submit_button(
        "💰 Estimar precio",
        # Texto del botón.

        type="primary",
        # "primary": botón azul con énfasis.
        # "secondary": botón gris neutro.

        use_container_width=True,
        # El botón ocupa todo el ancho del formulario.
    )
    # enviar será True cuando el usuario haga clic en el botón.
    # Mientras no se presione, enviar = False y el código debajo del form
    # NO se ejecuta.


# ── 6. LLAMADA A LA API Y RESULTADO ─────────────────────────────────────
# Este bloque está FUERA del form. Se ejecuta CADA VEZ que el usuario
# presiona "Estimar precio" (porque Streamlit re-ejecuta todo el script).

if enviar:
    # Solo entramos si el botón fue presionado.

    # ── 6a. Construir la URL con query parameters ────────────────────────
    # La API v1 usa GET con todos los parámetros en la URL.
    # Ejemplo: /predict?bedrooms=3&bathrooms=2&area_m2=200&...

    params = {
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "parking_spots": parking_spots,
        "area_m2": construction_area,
        # "area_m2": la API v1 usa alias "area_m2" para construction_area_sqm.

        "lat": latitude,
        "lon": longitude,
        # "lat" y "lon": alias definidos en la API.

        "city_guayaquil": city_guayaquil,
        "city_manta": city_manta,
        "city_quito": city_quito,
    }

    # ── 6b. Hacer la petición GET ────────────────────────────────────────
    try:
        # st.spinner(): muestra un spinner animado mientras se ejecuta el bloque.
        with st.spinner("Consultando al modelo..."):
            respuesta = requests.get(
                f"{API_URL}/predict",
                # URL completa del endpoint.

                params=params,
                # params: requests convierte el diccionario en query string.
                # Ej: ?bedrooms=3&bathrooms=2&area_m2=200...

                timeout=10,
                # timeout: máximo 10 segundos de espera.
                # Si la API no responde, lanza requests.exceptions.Timeout.
            )

        # ── 6c. Procesar la respuesta ────────────────────────────────────
        if respuesta.status_code == 200:
            # 200 OK: la API respondió correctamente.

            datos = respuesta.json()
            # .json(): convierte el body JSON de la respuesta a diccionario Python.
            # Ej: {"precio_usd": 287452.63}

            precio = datos["precio_usd"]
            # Extraemos el precio del diccionario.

            # ── Mostrar resultado ────────────────────────────────────────
            st.success(f"### 💵 Precio estimado: **${precio:,.2f} USD**")
            # st.success(): recuadro verde con el mensaje.
            # :,.2f formatea con separadores de miles y 2 decimales.
            # Ej: $287,452.63 USD

            st.caption("Predicción generada por Random Forest (100 árboles).")

        else:
            # La API respondió pero con error (422, 500, etc.).
            st.error(f"❌ Error de la API (código {respuesta.status_code})")
            # st.error(): recuadro rojo.
            st.json(respuesta.json())
            # st.json(): muestra el JSON de error formateado.

    except requests.exceptions.ConnectionError:
        # ConnectionError: la API no está corriendo o la URL es incorrecta.
        st.error(
            "❌ No se pudo conectar con la API.\n\n"
            "Asegurate de que el servidor esté corriendo:\n"
            "```bash\npython api_v1_minima.py\n```"
        )

    except requests.exceptions.Timeout:
        # Timeout: la API tardó más de 10 segundos en responder.
        st.error("❌ La API tardó demasiado en responder (timeout).")

    except Exception as e:
        # Cualquier otro error inesperado.
        st.error(f"❌ Error inesperado: {str(e)}")
