# -*- coding: utf-8 -*-
# ^^^ Declara la codificación UTF-8 para caracteres como tildes y la ñ.

"""
API v1 — Implementación Mínima
═══════════════════════════════════════════════════════════════════════

¿Qué hace esta API?
  1. Carga un modelo Random Forest desde un archivo .pkl
  2. Expone un endpoint GET /predict que recibe 9 parámetros por URL
  3. Devuelve un JSON con el precio estimado en USD

Cómo ejecutar:
  python api_v1_minima.py

"""

# ── 1. IMPORTACIÓN DE LIBRERÍAS ─────────────────────────────────────────

import joblib
#joblib: librería para guardar/cargar objetos Python en archivos binarios Utilizado para leer el modelo entrenado
#(modelo_inmobiliario.pkl).


import pandas as pd
# pandas: librería de manipulación de datos tabulares.

from fastapi import FastAPI, Query
# FastAPI: la clase principal para crear la aplicación web.
# Query:   declara que un parámetro se recibe desde la URL (query string).

from fastapi.responses import JSONResponse
# JSONResponse: clase para devolver respuestas JSON explícitamente. No usada directamente


# ── 2. CARGA DEL MODELO ─────────────────────────────────────────────────
model = joblib.load("modelo_inmobiliario.pkl")
# joblib.load() lee el archivo binario .pkl y reconstruye el objeto Python


FEATURES = [
    "BEDROOMS", "BATHROOMS", "PARKING_SPOTS", "CONSTRUCTION_AREA_SQM",
    "LATITUDE", "LONGITUDE",
    "CITY_Guayaquil", "CITY_Manta", "CITY_Quito",
]
# Lista con los nombres de las 9 columnas que el modelo espera como entrada.



# ── 3. CREACIÓN DE LA APLICACIÓN FASTAPI ────────────────────────────────
app = FastAPI(title="API Inmobiliaria v1")
# FastAPI() crea una instancia de la aplicación web.



# ── 4. ENDPOINTS (RUTAS) ────────────────────────────────────────────────

@app.get("/")

def root():
    return {"mensaje": "API Inmobiliaria — v1", "estado": "activa"}



@app.get("/health")

def health():
    return {"status": "ok"}


@app.get("/predict")

def predict(
    # ── PARÁMETROS DE ENTRADA ────────────────────────────────────────────
    # Cada línea declara un parámetro que el usuario DEBE enviar en la URL.

    bedrooms: int = Query(..., description="Número de habitaciones"),
    # bedrooms: nombre del parámetro (aparece como ?bedrooms=3 en la URL).
    # int:      tipo de dato esperado. 
    # Query():  indica que este parámetro viene de la query string.
 

    bathrooms: int = Query(..., description="Número de baños"),
    # Misma estructura: obligatorio, entero, documentado.

    parking_spots: int = Query(..., description="Plazas de estacionamiento"),

    construction_area_sqm: float = Query(..., alias="area_m2", description="Área de construcción en m²"),
    # alias="area_m2": el usuario escribe ?area_m2=200 en la URL,
    # float: el área puede tener decimales (ej: 200.5 m²).

    latitude: float = Query(..., alias="lat", description="Latitud"),
    # alias="lat": el usuario escribe ?lat=-0.18.

    longitude: float = Query(..., alias="lon", description="Longitud"),
    # alias="lon": el usuario escribe ?lon=-78.48.

    city_guayaquil: int = Query(0, alias="city_guayaquil", description="1 si es Guayaquil, 0 si no"),
    # Query(0): el 0 es el VALOR POR DEFECTO. Si el usuario no envía
    #           ?city_guayaquil=..., se asume 0 (no es Guayaquil).
    city_manta: int = Query(0, alias="city_manta", description="1 si es Manta, 0 si no"),
    city_quito: int = Query(0, alias="city_quito", description="1 si es Quito, 0 si no"),
):
    """Predice el precio de una propiedad en USD."""
    # ── 5. CONSTRUCCIÓN DEL DATAFRAME DE ENTRADA ────────────────────────


    data = pd.DataFrame([[

        bedrooms, bathrooms, parking_spots, construction_area_sqm,
        latitude, longitude,
        city_guayaquil, city_manta, city_quito,
    ]], columns=FEATURES)


    # ── 6. PREDICCIÓN ────────────────────────────────────────────────────
    precio = float(model.predict(data)[0])
   

    return {"precio_usd": round(precio, 2)}



# ── 7. PUNTO DE ENTRADA ─────────────────────────────────────────────────
if __name__ == "__main__":

    import uvicorn


    uvicorn.run(app, host="0.0.0.0", port=8000)

