# Flujo de trabajo del simulador v2.0

Hay tres cosas distintas que se "corren", y conviene no mezclarlas.

## 1. Pruebas automáticas (`test/v2.0`)
Verifican que el código esté sano. Corren sobre grillas sintéticas de 50 × 50 celdas: no descargan nada, no leen
`datos/`, tardan 10 segundos. Se ejecutan a mano (`python -m pytest -q` desde `src/v2.0`) y solas en GitHub
Actions en cada push. Si una falla, se rompió el código, no los datos.

## 2. Preparación de datos (`preparar_evento.py`) — una vez por evento
Es el único momento en que se descargan fuentes externas:

| Paso | Fuente | Requiere | Tiempo | Deja en |
| --- | --- | --- | --- | --- |
| DEM, pendiente, orientación | Copernicus GLO-30 vía Google Earth Engine | cuenta GEE | minutos | `inputSimulacion/dem/` |
| Biblioteca de viento (72 direcciones) | WindNinja local | WindNinja + 16 GB RAM | 45 min, una vez por dominio | `inputSimulacion/viento/` |
| NDVI/NDMI previos al evento | Sentinel-2 vía GEE | cuenta GEE | 20 min por evento | `procesados/indices/` → `inputSimulacion/combustibles/<evento>/` |
| Meteorología horaria | Open-Meteo (archivo ECMWF IFS) | internet | segundos | `inputSimulacion/meteo/` |
| Cicatriz de referencia, humedad del combustible | `datos/crudos/` + meteo | — | segundos | `inputSimulacion/eventos/<evento>/` |
| Focos VIIRS/MODIS | FIRMS vía GEE | cuenta GEE | minutos | `inputSimulacion/catalogo/hotspots/` |

Para los cuatro eventos actuales esto ya está hecho: los productos están en el repo y no hay que repetirlo.
Solo se corre al agregar un evento o un dominio nuevo.

## 3. Correr un escenario (`correr_escenario.py`) — tantas veces como se quiera
```bash
cd src/v2.0
python scripts/correr_escenario.py --escenario calibracion_2024
```
Lee `escenarios/v2.0/corridas/calibracion_2024.yaml`, carga los datos del evento desde `inputSimulacion/`,
simula (2 minutos para 21 días a 30 m), valida si el YAML lo pide y escribe
`resultados/v2.0/calibracion_2024_<fecha>/` con el resumen estadístico.

El código de simulación es siempre el mismo (`src/incendios_sl/simulation/`); lo que cambia entre corridas es
el escenario. Para cambiar una "prueba":
- otra hipótesis de ignición, otros k, menos horas → editar el YAML o copiarlo con otro nombre;
- otro incendio ya preparado → cambiar `evento:` por `SL-2022-PUERTAS`, `SL-2022-RENCA`, `SL-2024-MESILLA`;
- un incendio nuevo → ficha en `escenarios/v2.0/eventos/`, luego el paso 2, luego el escenario;
- otro juego de parámetros físicos → copiar `escenarios/v2.0/modelos/modelo_v1.yaml` y referenciarlo
  (hoy `cargar_modelo()` toma `modelo_v1`; un campo `modelo:` en el escenario está previsto para la Fase 1).

## Resumen
```
pytest (10 s, sin datos)  →  ¿el código funciona?
preparar_evento (1 vez)   →  ¿tengo los datos del evento?      descarga GEE / Open-Meteo / WindNinja
correr_escenario (n veces)→  ¿qué pasa con esta configuración?  lee inputSimulacion, escribe resultados/v2.0
```
