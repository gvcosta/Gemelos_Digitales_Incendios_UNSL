#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descargar_firms_sanluis.py

Descarga detecciones satelitales de focos de calor (VIIRS, satélite Suomi-NPP)
de la API de NASA FIRMS (Fire Information for Resource Management System) para
un rectángulo que cubre la provincia de San Luis, Argentina, y guarda todo en
un CSV consolidado.

Requisitos:
    pip install requests python-dotenv

Configuración:
    Se necesita una MAP_KEY gratuita de NASA FIRMS:
    https://firms.modaps.eosdis.nasa.gov/api/map_key/

    La clave se lee de la variable de entorno FIRMS_MAP_KEY, cargada desde el
    archivo .env.

Uso:
    python descargar_firms_sanluis.py

Para cambiar el rango de fechas o el rectángulo geográfico, editar la sección
CONFIGURACIÓN más abajo.
"""

import csv
import os
import sys
import time
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

# =============================================================================
# CONFIGURACIÓN (parámetros ajustables)
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
FIRMS_MAP_KEY = os.environ.get("FIRMS_MAP_KEY", "").strip()

# Rectángulo (west, south, east, north) que cubre la provincia de San Luis con
# margen. Es un rectángulo, NO el límite real de la provincia -- va a incluir
# detecciones de bordes de Mendoza, San Juan, Córdoba y La Pampa. El recorte al
# límite real (polígono IGN/CONAE de los 9 departamentos) se hace después.
#
BBOX_SAN_LUIS = (-67.8, -36.0, -64.3, -31.4)  # west, south, east, north

# VIIRS/Suomi-NPP: producto de ciencia (SP) desde 2012-01-20, con calidad
# revisada pero ~2 meses de demora en publicarse. El producto casi-en-tiempo-real
# (NRT) cubre los últimos ~2 meses hasta hoy, pero sin la revisión de calidad
# del SP. Se usa SP para todo lo "viejo" y NRT solo para lo reciente que SP
# todavía no publicó.
FECHA_INICIO = date(2012, 1, 20)
FECHA_FIN = date.today()
DIAS_MARGEN_SP = 90  # ventanas que terminan a menos de N días de hoy usan NRT en vez de SP

SOURCE_SP = "VIIRS_SNPP_SP"
SOURCE_NRT = "VIIRS_SNPP_NRT"

DAY_RANGE = 5  # máximo permitido por la API de área para VIIRS, por request (verificado empíricamente)

DIRECTORIO_SALIDA = SCRIPT_DIR
CSV_SALIDA = os.path.join(DIRECTORIO_SALIDA, "viirs_snpp_san_luis.csv")
ARCHIVO_LOG = os.path.join(DIRECTORIO_SALIDA, "log_consola.txt")

TIMEOUT_REQUEST = 60
REINTENTOS = 3
ESPERA_ENTRE_REINTENTOS = 5
ESPERA_ENTRE_REQUESTS = 1.0  # segundos, para no saturar la API

URL_STATUS = "https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={map_key}"
URL_AREA = (
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/{source}/"
    "{west},{south},{east},{north}/{day_range}/{fecha}"
)

COLUMNAS_ESPERADAS_FIRMS = {"latitude", "longitude", "acq_date", "acq_time", "confidence"}


# =============================================================================
# LOGGING A ARCHIVO .txt (además de la consola)
# =============================================================================

class _Tee(object):
    def __init__(self, consola_original, archivo):
        self.consola_original = consola_original
        self.archivo = archivo

    def write(self, texto):
        self.consola_original.write(texto)
        self.archivo.write(texto)
        self.archivo.flush()

    def flush(self):
        self.consola_original.flush()
        self.archivo.flush()


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def verificar_map_key(session):
    """
    Consulta el estado de la MAP_KEY (transacciones usadas/disponibles) antes
    de arrancar. Si la key es inválida, corta la ejecución con un mensaje
    claro en vez de dejar que cientos de requests fallen uno por uno.
    """
    if not FIRMS_MAP_KEY:
        print("ERROR: no se encontró FIRMS_MAP_KEY. Completar el archivo .env "
              "(ver .env.example) con una clave obtenida en "
              "https://firms.modaps.eosdis.nasa.gov/api/map_key/")
        sys.exit(1)

    try:
        resp = session.get(URL_STATUS.format(map_key=FIRMS_MAP_KEY), timeout=TIMEOUT_REQUEST)
    except requests.exceptions.RequestException as e:
        print(f"AVISO: no se pudo verificar la MAP_KEY ({e}). Se continúa de todas formas.")
        return

    print("Estado de la MAP_KEY:")
    print(f"  {resp.text.strip()}")
    if resp.status_code != 200 or "invalid" in resp.text.lower():
        print("ERROR: la MAP_KEY parece inválida. Revisar el archivo .env.")
        sys.exit(1)


def generar_ventanas(inicio, fin, dia_range):
    """
    Genera fechas de fin de ventana, de a saltos de `dia_range` días, desde
    `inicio` hasta `fin` (inclusive). Cada ventana cubre
    [fecha_ventana - (dia_range - 1), fecha_ventana].
    """
    actual = inicio + timedelta(days=dia_range - 1)
    while actual <= fin:
        yield actual
        actual += timedelta(days=dia_range)
    if actual - timedelta(days=dia_range) < fin:
        yield fin  # última ventana parcial, para no dejar afuera los días finales


def elegir_fuente(fecha_fin_ventana, hoy):
    """SP para ventanas viejas (ya publicadas con calidad revisada), NRT para
    las últimas DIAS_MARGEN_SP jornadas, que SP todavía no cubre."""
    if (hoy - fecha_fin_ventana).days < DIAS_MARGEN_SP:
        return SOURCE_NRT
    return SOURCE_SP


def descargar_ventana(session, fecha_fin_ventana, fuente):
    """
    Descarga una ventana de hasta DAY_RANGE días de detecciones FIRMS.
    Devuelve una lista de dicts (una fila por detección) o None si, tras los
    reintentos, no se pudo obtener una respuesta válida.
    """
    west, south, east, north = BBOX_SAN_LUIS
    url = URL_AREA.format(
        map_key=FIRMS_MAP_KEY,
        source=fuente,
        west=west, south=south, east=east, north=north,
        day_range=DAY_RANGE,
        fecha=fecha_fin_ventana.isoformat(),
    )

    for intento in range(1, REINTENTOS + 1):
        try:
            resp = session.get(url, timeout=TIMEOUT_REQUEST)
        except requests.exceptions.RequestException as e:
            print(f"    [intento {intento}/{REINTENTOS}] Error de red: {e}")
            time.sleep(ESPERA_ENTRE_REINTENTOS)
            continue

        if resp.status_code != 200:
            print(f"    HTTP {resp.status_code} para {fuente} / {fecha_fin_ventana.isoformat()}")
            time.sleep(ESPERA_ENTRE_REINTENTOS)
            continue

        texto = resp.text.strip()
        if not texto:
            return []  # sin detecciones en esta ventana: respuesta válida, vacía

        lector = csv.DictReader(texto.splitlines())
        columnas = set(c.strip().lower() for c in (lector.fieldnames or []))
        if not COLUMNAS_ESPERADAS_FIRMS.issubset(columnas):
            # La API devuelve un mensaje de error (ej. "Invalid MAP_KEY", clave
            # sin transacciones restantes, fuente no disponible para esa fecha)
            # como texto plano en vez de CSV. Se trata como error, no como datos.
            print(f"    Respuesta inesperada (no es CSV de FIRMS): {texto[:200]!r}")
            time.sleep(ESPERA_ENTRE_REINTENTOS)
            continue

        filas = list(lector)
        for fila in filas:
            fila["fuente_sensor"] = fuente
        return filas

    print(f"    Se agotaron los reintentos para {fuente} / {fecha_fin_ventana.isoformat()}. Se omite esta ventana.")
    return None


def clave_deteccion(fila):
    """
    Identifica una detección de forma única, para poder descartar duplicados.
    Las ventanas de descarga se solapan unos días cuando el rango total no es
    múltiplo exacto de DAY_RANGE (para no dejar días finales sin cubrir), así
    que la misma detección puede volver a aparecer en dos ventanas consecutivas.
    lat/lon/fecha/hora/satélite identifican un pasaje puntual del satélite de
    forma inequívoca.
    """
    return (
        fila.get("latitude"), fila.get("longitude"),
        fila.get("acq_date"), fila.get("acq_time"), fila.get("satellite"),
    )


def escribir_csv(filas, ruta_csv):
    if not filas:
        return
    carpeta = os.path.dirname(ruta_csv)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    columnas = list(filas[0].keys())
    for fila in filas[1:]:
        for clave in fila.keys():
            if clave not in columnas:
                columnas.append(clave)

    with open(ruta_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for fila in filas:
            writer.writerow(fila)


# =============================================================================
# PROGRAMA PRINCIPAL
# =============================================================================

def main():
    os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)

    consola_original = sys.stdout
    archivo_log = open(ARCHIVO_LOG, "w", encoding="utf-8")
    sys.stdout = _Tee(consola_original, archivo_log)

    session = requests.Session()
    verificar_map_key(session)

    print("=" * 70)
    print(f"Descargando detecciones FIRMS (VIIRS/Suomi-NPP) para San Luis")
    print(f"Rango: {FECHA_INICIO} a {FECHA_FIN}")
    print(f"BBOX (west, south, east, north): {BBOX_SAN_LUIS}")
    print("=" * 70)

    hoy = date.today()
    todas_las_filas = []
    claves_vistas = set()
    duplicados_descartados = 0
    ventanas_ok = 0
    ventanas_vacias = 0
    ventanas_con_error = 0
    total_ventanas = 0

    for fecha_fin_ventana in generar_ventanas(FECHA_INICIO, FECHA_FIN, DAY_RANGE):
        total_ventanas += 1
        fuente = elegir_fuente(fecha_fin_ventana, hoy)
        print(f"[{fecha_fin_ventana.isoformat()}] ventana de {DAY_RANGE} días, fuente={fuente}...")

        filas = descargar_ventana(session, fecha_fin_ventana, fuente)

        if filas is None:
            ventanas_con_error += 1
        elif len(filas) == 0:
            ventanas_vacias += 1
        else:
            filas_nuevas = []
            for fila in filas:
                clave = clave_deteccion(fila)
                if clave in claves_vistas:
                    duplicados_descartados += 1
                    continue
                claves_vistas.add(clave)
                filas_nuevas.append(fila)

            print(f"    OK. {len(filas)} detecciones ({len(filas_nuevas)} nuevas, "
                  f"{len(filas) - len(filas_nuevas)} ya vistas en una ventana solapada).")
            todas_las_filas.extend(filas_nuevas)
            ventanas_ok += 1
            # Guardado incremental: así no se pierde nada si el script se corta a mitad de camino.
            escribir_csv(todas_las_filas, CSV_SALIDA)

        time.sleep(ESPERA_ENTRE_REQUESTS)

    print("=" * 70)
    print("RESUMEN")
    print(f"  Ventanas totales: {total_ventanas}")
    print(f"  Ventanas con detecciones: {ventanas_ok}")
    print(f"  Ventanas vacías (sin detecciones): {ventanas_vacias}")
    print(f"  Ventanas con error (omitidas, revisar log): {ventanas_con_error}")
    print(f"  Duplicados descartados (ventanas solapadas): {duplicados_descartados}")
    print(f"  Total de detecciones únicas guardadas: {len(todas_las_filas)}")
    print(f"  CSV final guardado en: {os.path.abspath(CSV_SALIDA)}")
    print("=" * 70)

    if ventanas_con_error:
        print(f"AVISO: {ventanas_con_error} ventanas quedaron sin datos por error. "
              f"Revisar {ARCHIVO_LOG} y volver a correr el script si hace falta "
              f"completar esos huecos (no se inventan datos para reemplazarlos).")

    sys.stdout = consola_original
    archivo_log.close()


if __name__ == "__main__":
    main()