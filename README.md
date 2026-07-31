> 📚 Documentación Completa del Proyecto — Predicción Inmobiliaria
> Predicción de precios de casas Aplicación desarrollada en el Diplomado de Python Fullstack. 
> Repositorio GitHub: https://github.com/faustoyg/Inmueble
> Flujo: Web scraping → CSV → Modelo PKL → FastAPI → Streamlit
> **Objetivo:** Predecir el precio de venta de inmuebles en Ecuador usando Machine Learning  
> **Fecha:** Julio 2026

---

## 1. Arquitectura General del Proyecto

```
Inmueble/
│
├── plusvalia_filtered.csv       ← Datos previos a proceso
├── plusvalia_procesado.csv      ← Datos limpios: 7,459 inmuebles
├── modelo_inmobiliario.pkl      ← Modelo entrenado 
│
├── Entrenamiento_modelo.ipynb   ← Script de entrenamiento (Google Colab)
│                                 Manejo de datos → Random Forest → exportación
│
├── webscrapping.py             ← Codigo para webscraping de plusvalia.com 
├── api_v1.py                   ← FastAPI versión 1
└── streamlit_v1.py             ← Streamlit 
```

**Flujo de datos:**

```
[plusvalia_filtered.csv]
         │
         ▼
[Entrenamiento_modelo.ipynb]  ── limpieza, EDA, preprocesamiento ──►  [plusvalia_procesado.csv]
         │                                                          │
         │  train_test_split + entrenamiento                        │
         ▼                                                          │
[RandomForestRegressor]                                             │
         │                                                          │
         ▼                                                          │
[modelo_inmobiliario.pkl] ◄─── (carga) ─── [api_v*.py] ───►  API REST
                                                      POST /predict
                                                      ───►  precio_usd
```

---

## 2. `plusvalia_procesado.csv` — Dataset Procesado

### 📊 Estadísticas Generales

| Métrica               | Valor                          |
|-----------------------|--------------------------------|
| Filas                 | 7,459                          |
| Columnas              | 10                             |
| Sin valores nulos ni duplicados                        |

### 📋 Diccionario de Columnas

| # | Columna                | Tipo    | Descripción |
|---|------------------------|---------|-------------|
| 1 | `PRICE_USD`           | float   | **Variable objetivo** — Precio en USD (ya limpio) |
| 2 | `BEDROOMS`            | int     | Número de habitaciones |
| 3 | `BATHROOMS`           | int     | Número de baños |
| 4 | `PARKING_SPOTS`       | int     | Plazas de estacionamiento |
| 5 | `CONSTRUCTION_AREA_SQM` | float | Área construida en m² |
| 6 | `LATITUDE`            | float   | Latitud (coordenada geográfica) |
| 7 | `LONGITUDE`           | float   | Longitud (coordenada geográfica) |
| 8 | `CITY_Guayaquil`      | int     | 1 = Guayaquil, 0 = no (One-Hot Encoding) |
| 9 | `CITY_Manta`          | int     | 1 = Manta, 0 = no |
|10 | `CITY_Quito`          | int     | 1 = Quito, 0 = no |


### 🔄 Preprocesamiento Aplicado

1. **Eliminación de columnas irrelevantes:** `ID`, `LINK` (identificadores sin valor predictivo)
2. **Eliminación de filas duplicadas**
3. **Filtrado de precios irreales:** PRICE_USD < 100 USD eliminados
4. **Capping (Winsorización) al percentil 99:** Los valores extremos de `PRICE_USD`, `BEDROOMS`, `BATHROOMS`, `PARKING_SPOTS` y `CONSTRUCTION_AREA_SQM` se limitan al valor del percentil 99
5. **One-Hot Encoding:** La columna `CITY` (con valores "Quito", "Guayaquil", "Manta") se convierte en 3 columnas binarias

---

## 3. `modelo_inmobiliario.pkl` — Modelo Entrenado

### 🧠 Ficha Técnica

| Característica        | Valor                                |
|-----------------------|--------------------------------------|
| Algoritmo             | `RandomForestRegressor` (scikit-learn) |
| `n_estimators`        | 100 árboles                          |
| `random_state`        | 42 (reproducible)                    |
| Características       | 9 features                           |
| Entrenado con         | 100% del dataset (7,459 registros)   |
| Lenguaje              | Python + joblib (serialización)      |

| Concepto | Definición | Dónde se aplica |
|----------|-----------|-----------------|
| **Random Forest** | Ensemble de árboles de decisión. Cada árbol vota y se promedia. | `modelo_inmobiliario.pkl` |
| **n_estimators** | Número de árboles en el bosque. Más árboles = más robusto pero más lento. | `RandomForestRegressor(n_estimators=100)` |

### 🧪 Celda de Prueba Final

El script incluye una celda de validación con una propiedad de ejemplo en Quito:

| Atributo | Valor |
|----------|-------|
| Habitaciones | 3 |
| Baños | 2 |
| Parqueaderos | 2 |
| Área | 200 m² |
| Coordenadas | Lat -0.18, Lon -78.48 (Quito centro) |

> El modelo entrega una predicción en USD para esta propiedad.


## 4. `api_v1.py` — API Versión 1

### 📐 Arquitectura

```
api_v1.py
│
├── joblib.load("modelo_inmobiliario.pkl")   ← Carga síncrona al arrancar
│
├── GET /                                     ← {"mensaje": "...", "estado": "activa"}
├── GET /health                               ← {"status": "ok"}
└── GET /predict?bedrooms=3&bathrooms=2&...   ← {"precio_usd": 123456.78}
```

### Ejecución

1. Abrir un CMD en windows
2. Dirigirse al directorio en donde esta carpeta del proyecto
 cd .....\Inmueble
3. Activar un entorno virtual
    venv\Scripts\activate
4. Ejecutar api_v1
    python api_v1.py
5. Verificar si esta levantado servidor de FastAPI
    http://localhost:8000/docs#

### Nota importante en v1

| Limitación             | Consecuencia |
|------------------------|--------------|
| Sin validación         | El usuario puede enviar `bedrooms=9999` sin errores |
| Sin manejo de errores  | Si falla el modelo, el error es un traceback dificil|
| Sin logging            | No sabes cuántas peticiones llegan ni cuándo fallan |
| GET con query params   | Expuesto en la URL (mala práctica para datos sensibles) |

## 5. `streamlit_v1.py` — API Versión 1

### Ejecución

1. Abrir un nuevo CMD en windows
2. Dirigirse al directorio en donde esta carpeta del proyecto
 cd .....\Inmueble
3. Instalar librerias si no se lo ha hecho
# ── Interfaz gráfica (Streamlit) ──────────────────────────────────────────────
streamlit==1.44.1       # Framework para apps web interactivas de datos
requests==2.32.4        # Cliente HTTP para consumir la API desde Streamlit
4. Ejecutar streamlit_v1
    streamlit run streamlit_v1.py
5. Se puede observar desde el navegador. Por ejemplo:
    Local URL: http://localhost:8501
