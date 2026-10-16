# Etapa 6 — Incendios históricos de prueba: fichas, condiciones iniciales y datos preparados

Fecha: 2026-10-14. Configuraciones reproducibles en `config/eventos/*.yaml`; productos en `data/derivados/eventos/<id>/`, `indices/<id>/`, `combustibles/<id>/`, `meteo/`; focos de calor en `data/catalogo/hotspots/`.

## 1. Selección y papel de cada evento

| Evento | Rol | Polígono MapBiomas | Referencia espacial usada | Inicio / fin (SNMF) | Confianza temporal |
|---|---|---|---|---|---|
| `SL-2024-LASLAGUNAS` | **Calibración** | 2024_41914 (40.048 ha, 100 % en el dominio) | polígono completo rasterizado: 40.052 ha | 18/09/2024 → extinguido 09/10/2024 (contenido 28/09) | alta (día); hora acotada por VIIRS |
| `SL-2022-RENCA` | **Validación** | 2022_43667 (4.270 ha) | píxeles del polígono quemados en **septiembre** según el raster mensual: 3.798 ha (el polígono fusiona un evento de agosto de 424 ha: Piscu Yacu / Ruta 40, 27–31/08) | 06/09/2022 (MODIS; SNMF 07/09) → extinguido 11/09 (contenido 08/09) | media |
| `SL-2022-PUERTAS` | **Validación** (verano) | 2021_46201 (2.103 ha) | píxeles quemados en **enero de 2022**: 2.062 ha | 12/01/2022 → extinguido 16/01 | media |
| `SL-2024-MESILLA` (incorporado 2026-10-15) | **Validación** (pequeña escala, misma estación que la calibración) | 2024_41892 (181 ha, 100 % en el dominio, 13 partes) | polígono completo rasterizado: 182 ha (el raster mensual lo reparte entre agosto, 96 ha, y septiembre, 85 ha, pero SNMF y dNBR del compilador indican un único evento) | 02/09/2024 → extinguido 09/09 (contenido 03/09, reactivado 04–06/09) | media |

Descartados: `2024_41959` Paso Grande (84 % fuera del dominio), `2023_26601` Las Chacras (superficie SNMF 73 ha vs 1.336 ha MapBiomas, inconsistente), polígonos < 500 ha sin registro SNMF (solo prueba espacial, sin fechas).

## 2. Fichas

### 2.1 SL-2024-LASLAGUNAS (Las Lagunas – Potrerillos, Libertador General San Martín)
- **Ignición:** dos focos SNMF, Las Lagunas (−65,5477, −32,6367; celda de bosque abierto) y Potrerillos (−65,6232, −32,6422; celda de bosque cerrado). Hora no documentada. Primera detección VIIRS NOAA-20 el 18/09 a las 17:26 UTC con 393 detecciones ese día en una banda E–O de 12 km (−65,70 a −65,58). Hipótesis de hora: 10:00, **12:00** (usada) y 14:00 local; el barrido de la Etapa 7 mostró que la hora es irrelevante para el resultado (diferencias de IoU < 0,005).
- **Progresión observada (VIIRS SNPP + NOAA-20, 9.333 detecciones):** 18/09 banda inicial; 19/09 1.913 detecciones, expansión S (lat −32,77) y E; **20/09 5.037 detecciones (54 %), expansión N hasta −32,41 y O hasta −65,77**; 21/09 1.152 (O hasta −65,82); 22–24/09 residuales; 26/09 4 detecciones. El 87 % de las detecciones ocurre hasta el 20/09 inclusive. MODIS (1 km): 1.210 detecciones, misma secuencia.
- **Meteorología (IFS 9 km):** 19–20/09 HR mínima 5–10 %, viento 6–8 m/s; humedad del combustible muerto fino 4–8 %. Vientos: 18/09 del SO (225°), 19/09 del O (263°), 20/09 del S (184° mediana) girando a N al final del día, 21/09 del N (348°, 8,5 m/s).
- **Índices:** mediana S2 30/07–17/09, 40 escenas, NDVI 0,24, NDMI −0,21.
- **Instantes de evaluación:** fin del 20/09 local (21/09 03 UTC; fase explosiva), fin del 21/09, 25/09 (fin de propagación principal), 28/09 (contenido), 10/10 (extinguido).
- **Limitaciones:** combate desde el día 1 (bomberos, SNMF); bordes rectos de la cicatriz al E y S (x ≈ 3.550 km, y ≈ 6.376 km) sugieren líneas de contención o límites de parcelas; superficies informadas 48.226 (SNMF) vs 40.048 (MapBiomas).

### 2.2 SL-2022-RENCA (Renca – San Felipe, Chacabuco)
- **Ignición:** punto SNMF (−65,4565, −32,7924). Fecha: MODIS detecta 88 píxeles el 06/09 (lat −32,83 a −32,71) y el SNMF registra inicio 07/09 con primer reporte el 08/09; se adopta **06/09** con hipótesis de hora 13:00 (usada), 10:00 y 07/09 10:00 local.
- **Progresión:** MODIS 06/09 (88 px), 07/09 (12), 08/09 (31, ya con otros focos). Sin VIIRS en GEE para 2022 → validación temporal con tolerancia 1 km.
- **Meteorología:** 06–07/09 HR mín 14 %, viento del NNO 5 m/s (máx 7); 08/09 cambio a S con 8,5 m/s medios y máx 9,9; sin lluvia; humedad 1 h 6–10 %.
- **Índices:** mediana S2 20/07–05/09, 32 escenas, NDVI 0,26, NDMI −0,20 (igual de seco que 2024).
- **Evaluación:** 09/09 03 UTC (contenido) y 12/09 03 UTC (extinguido).

### 2.3 SL-2022-PUERTAS (Paraje Puertas Coloradas, Chacabuco; verano)
- **Ignición:** punto SNMF (−65,3995, −32,5344) a 922 m del polígono; el cargador lo desplaza a la celda combustible quemada más cercana (**hipótesis documentada**, distancia registrada en el log). Fecha 12/01/2022 (SNMF y MODIS, 12 px). Hipótesis de hora: 13:00 (usada), 10:00, 16:00 local.
- **Progresión:** MODIS 12/01 (12 px), 13/01 (59), 14/01 (110, extensión máxima −65,46…−65,33 / −32,69…−32,56), 15/01 (9).
- **Meteorología:** ola de calor: T máx 35–37 °C, HR mín 14–19 %, viento 4–8 m/s de dirección variable (S, NO, NE); humedad 1 h 4–6 %; lluvia 1,3–1,7 mm los días 15–16.
- **Índices:** mediana S2 25/11/2021–11/01/2022, 32 escenas, NDVI 0,44, NDMI −0,10 (vegetación verde de verano: prueba del curado y la humedad viva).
- **Evaluación:** 15/01 03 UTC y 17/01 03 UTC.

### 2.4 SL-2024-MESILLA (Mesilla del Cura, Libertador General San Martín; incorporado el 2026-10-15)
- **Selección:** de los candidatos con polígono MapBiomas 100 % dentro del dominio y reporte SNMF a < 2 km (Las Chilcas 2022, Las Chacras 2023, Rincón del Carmen 2023, La Aguada 2023, La Pampita 2022, Piscu Yacu 2022), es el de mejor documentación: 8 reportes diarios, superficie satelital del compilador (196,9 ha) coherente con MapBiomas (181 ha), año con VIIRS en GEE y misma estación seca que el evento de calibración.
- **Ignición:** punto SNMF (−65,8132, −32,5466) en celda de arbustal abierto, **1,4 km al SE del polígono** (no se desplaza porque es combustible). Fecha 02/09/2024 (SNMF), coherente con la meteorología: primer día seco y ventoso (HR mín 28 %, viento NO 5–7 m/s) tras lloviznas del 30–31/08. Hora desconocida; hipótesis 13:00 (usada), 10:00 y 15:00 local. Hipótesis alternativas de lugar: `alt0` extremo NO de la cicatriz (barlovento del 02/09) y `alt1` extremo S (la cicatriz es alargada N–S, 3,4 km, y el 03/09 el viento fue del S a 9,6 m/s).
- **Progresión (SNMF):** activo 02/09, contenido 03/09, activo de nuevo 04–06/09, extinguido 07–09/09. Combate desde el primer día (11 bomberos de policía y cuarteles de 8 localidades).
- **Progresión (VIIRS SNPP + NOAA-20, `scripts/obtener_focos.py`, radio 3 km a la cicatriz):** 02/09 **50 detecciones** (NOAA-20 desde las 17:28 UTC, SNPP 18:43 UTC) ya sobre la **mitad sur** de la cicatriz (lat −32,536 a −32,520; FRP máx 14 MW); 03/09 17 detecciones en el sector SE; 04/09 23 detecciones en la **mitad norte** (lat −32,526 a −32,516); sin detecciones posteriores. MODIS: 9 (03/09) y 17 (04/09). La extracción completa del dominio (488 VIIRS) incluye el incendio simultáneo de Paso Grande (borde SE, 03–06/09), excluido por el filtro.
- **Meteorología (IFS 9 km, 16 puntos):** 02/09 T máx 21 °C, HR mín 28 %, viento NO 6–7 m/s entre 15 y 18 UTC; 03/09 HR mín 19 %, viento S 9,6 m/s; 05/09 viento N 9,7 m/s; sin lluvia del 01 al 09/09.
- **Índices:** compuesto propio S2 (mediana 15/07–01/09/2024, 40 escenas, Cloud Score+ ≥ 0,6): NDVI medio 0,26, NDMI −0,19 (igual de seco que el compuesto de Las Lagunas). Unas corridas preliminares de la mañana del 2026-10-15 usaron el compuesto de `SL-2024-LASLAGUNAS` como respaldo (`indices.respaldo_evento`, GEE sin proyecto configurado); las métricas espaciales cambiaron < 0,01 de IoU al reemplazarlo. Composición de clases idéntica a 2024 (cobertura 2023).
- **Evaluación:** fin del 02/09 local (03/09 03 UTC, antes del "Contenido"), fin del 03/09, fin del 06/09 (último "Activo"), 10/09 (extinción). Focos VIIRS (90) con tolerancia 375 m.
- **Resultados v1 sin mitigación (k calibrados, WAF 1,0; índices propios y focos, 2026-10-15):**

| Corrida | Ignición | Fin del 02/09: sim / omisión / IoU | Fin del 03/09: sim / omisión | Focos capturados al fin del día / desfase mediano | Extinción (10/09): sim |
|---|---|---|---|---|---|
| `SL-2024-MESILLA_validacion_h0` | SNMF, 13:00 | 268 ha / 1,00 / 0,00 | 1.442 ha / 0,24 | 0,69 / +6,1 h | 65.200 ha |
| `SL-2024-MESILLA_validacion_h1` | SNMF, 10:00 | ≈ h0 | ≈ h0 | ≈ h0 | ≈ h0 |
| `SL-2024-MESILLA_validacion_alt0` | extremo NO, 13:00 | 433 ha / 0,80 / 0,06 | 1.512 ha / 0,73 | 0,22 / +47,8 h | 55.894 ha |
| `SL-2024-MESILLA_validacion_alt1` | extremo S, 13:00 | **516 ha / 0,45 / 0,17** | 1.941 ha / **0,00** | **0,99 / −1,5 h** | 63.116 ha |
| `SL-2024-MESILLA_validacion_alt1_h2` | extremo S, 08:00 | 778 ha / 0,44 / 0,12 | 2.434 ha / 0,00 | 1,00 / −6,5 h | 65.898 ha |

- **Lectura:** (i) desde el punto SNMF el fuego del primer día corre hacia el SE (viento NO) sin tocar la cicatriz ni los 50 focos del 02/09; recién el viento S del 03/09 lo lleva sobre ella (desfase +6 h) → el punto SNMF no es el origen, es una referencia administrativa; (ii) la hipótesis `alt1` (extremo S, 13:00 local) es la más compatible con la forma N–S de la cicatriz y con los focos: captura el 99 % al fin del día de detección con un desfase mediano de −1,5 h, y la totalidad de la cicatriz al fin del 03/09; adelantar la ignición a las 08:00 la hace llegar 6,5 h antes que los focos, por lo que la hora sí es discriminable aquí gracias a VIIRS (a diferencia de 2024); (iii) sin mitigación el modelo sobreestima por dos órdenes de magnitud a partir del segundo día: el incendio fue contenido a las 24 h por el combate, de modo que **sólo el primer día es evaluable** con el modelo v1. Un incendio de este tamaño es, por tanto, un caso de prueba para el módulo de mitigación (pendiente), no para la propagación libre.

## 3. Condiciones iniciales y parámetros comunes
- Dominio, grilla y DEM Copernicus (Etapa 3); cobertura del año anterior al evento (2023 para 2024; 2021 para ambos de 2022); clases de combustible v1 por evento (con los índices pre-incendio del propio evento); humedad muerta por FFMC inicializado 24 h antes; biblioteca de viento compartida (100 m, `brush`).
- Composición de clases (porcentaje de la grilla): 2024: pastizal 16,8, pastura/cultivo 12,8, arbustal abierto 20,7, bosque abierto 30,6, bosque cerrado 17,6. 2022 (cobertura 2021): pastizal 16,0, pastura/cultivo 11,9–13,0, arbustal abierto 23,0, arbustal cerrado 1,4, bosque abierto 27,7, bosque cerrado 18,1.
- Sin mitigación en todos los casos; fin de simulación en la fecha de extinción SNMF (00:00 local del día siguiente).

## 4. Incertidumbres registradas
Ignición (lugar informado ≠ origen; hora desconocida); fechas SNMF a nivel de día; meteorología de modelo a 9 km; cicatriz anual/mensual de MapBiomas (sin exactitud local conocida; separación por mes para 2022); focos MODIS de 1 km para 2022; clasificación de combustibles por analogía; FFMC no calibrado; WindNinja neutral con vegetación única.
