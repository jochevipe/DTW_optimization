# Índice de `contexto/`

Material conceptual y evidencia para el estudio de controladores DDTW sobre MKP. Para **estrategias activas, parámetros que ejecuta el código y comandos**, empezá por el [README principal](../README.md) y [`mkp_common/config.py`](../mkp_common/config.py). Los valores de documentos de teoría o campañas anteriores no sustituyen la configuración vigente.

## Teoría y referencias (`oficial/`)

| Documento | Uso y vigencia |
|---|---|
| [`oficial/01_binary_simple_fire_d2.md`](oficial/01_binary_simple_fire_d2.md) | Regla conceptual D2/umbral del controlador **Binary-Simple** activo. Las cifras de configuración que incluya pueden corresponder al artículo o a una etapa anterior; contrastalas con el código. |
| [`oficial/02_binary_complex_a9.md`](oficial/02_binary_complex_a9.md) | Documento renombrado desde `02_binary_hysteresis_a4.md` para **Binary-Complex**. Contiene valores y explicaciones heredados; su actualización de contenido está pendiente. Para la regla actual, consultá [`binary_complex/config.py`](../binary_complex/config.py). |
| [`oficial/09_dtw_fundamentos.md`](oficial/09_dtw_fundamentos.md) | Fundamentos del DTW/DDTW, banda, señales y umbrales; referencia teórica, no configuración ejecutable. |
| [`oficial/mhs/05_mh_pso.md`](oficial/mhs/05_mh_pso.md) | PSO binario: representación y modos. |
| [`oficial/mhs/06_mh_ga.md`](oficial/mhs/06_mh_ga.md) | Algoritmo genético binario. |
| [`oficial/mhs/07_mh_gwo.md`](oficial/mhs/07_mh_gwo.md) | GWO binario. |
| [`oficial/mhs/08_mh_de.md`](oficial/mhs/08_mh_de.md) | DE binario. |

Los documentos de `oficial/` explican el modelo y las cuatro MH, pero **no certifican los parámetros de la próxima campaña**. Para los controladores actuales consultá también [`binary_simple/config.py`](../binary_simple/config.py), [`binary_patient/config.py`](../binary_patient/config.py) y [`binary_complex/config.py`](../binary_complex/config.py). No hay una estrategia activa adicional llamada `binary_hysteresis`.

## Glosario y benchmark

| Ruta | Contenido |
|---|---|
| [`info_dtw/explicacion_params_dtw.md`](info_dtw/explicacion_params_dtw.md) | Glosario de parámetros del monitor; las cifras ejecutadas se leen en `mkp_common/config.py`. |
| [`params_instancias/instancias_mkp.md`](params_instancias/instancias_mkp.md) | Tabla descriptiva de los archivos Chu–Beasley; usá [`odd/tasks/frente2-multi-instancia.md`](../odd/tasks/frente2-multi-instancia.md) para los índices oficiales de la próxima campaña. |

## Primera ronda de revisión (`Round-1/`)

| Documento | Uso y vigencia |
|---|---|
| [`REVIEWER_1.md`](Round-1/REVIEWER_1.md), [`REVIEWER_2.md`](Round-1/REVIEWER_2.md), [`REVIEWER_3.md`](Round-1/REVIEWER_3.md) | Cartas de los revisores: contexto de las solicitudes, no instrucciones de ejecución. |
| [`SINTESIS_REVIEWS.md`](Round-1/SINTESIS_REVIEWS.md) | Síntesis y frentes de respuesta. |
| [`PREGUNTAS_Y_RESPUESTAS_REVISORES.md`](Round-1/PREGUNTAS_Y_RESPUESTAS_REVISORES.md) | Hoja de preguntas y respuestas en elaboración. |
| [`INSTANCIAS_SELECCIONADAS.md`](Round-1/INSTANCIAS_SELECCIONADAS.md) | Documento de selección en reconciliación; la tabla oficial vigente está en [`odd/tasks/frente2-multi-instancia.md`](../odd/tasks/frente2-multi-instancia.md): muestreo con semilla, 3 por archivo, 27 instancias. |
| [`HALLAZGOS_OAT.md`](Round-1/HALLAZGOS_OAT.md) | Resultados descriptivos del OAT, 19 configuraciones de Binary-Simple y Binary-Complex sobre tres índices de `mknapcb1` con 31 épocas. Base para decidir parámetros nuevos, **no** selección definitiva ni generalización a las nueve familias. |
| [`ESTRATEGIA_A10_BINARY_PATIENT.md`](Round-1/ESTRATEGIA_A10_BINARY_PATIENT.md) | Diseño del controlador Binary-Patient; verificá comportamiento ejecutable en [`binary_patient/config.py`](../binary_patient/config.py). |

El OAT usó `mknapcb1[0,15,29]`, **distinto** del protocolo oficial nuevo de 27 instancias. El primer paso previo a ejecutarlo es fijar los valores definitivos en `mkp_common/config.py` a partir de los hallazgos; no se eligen aquí por inferencia.

## Especificaciones y archivo

- [`especificacion_extraccion_datos.md`](especificacion_extraccion_datos.md): especificación **futura** de extracción/análisis (incluida una prueba de suma de rangos); no describe una implementación existente. El análisis actual usa Wilcoxon pareado y Vanilla-Exploration como referencia; véanse [`analisis/estadistico.py`](../analisis/estadistico.py) y [`mkp_common/stats.py`](../mkp_common/stats.py).
- [`historico/advance_LB2_MKP.ipynb`](historico/advance_LB2_MKP.ipynb): notebook archivado; material histórico, no guía de ejecución vigente.
- [`historico/campanas_previas.md`](historico/campanas_previas.md): catálogo de resultados anteriores retirados de `results/` (se incorpora en esta limpieza; los archivos son recuperables desde git). No confundas campañas previas con la salida de la campaña post-OAT.

Para la secuencia de tareas y decisiones de esta limpieza, consultá [`odd/tasks/post-merge-cleanup.md`](../odd/tasks/post-merge-cleanup.md).
