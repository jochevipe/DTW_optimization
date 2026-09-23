# Hallazgos OAT — sensibilidad de parámetros DDTW (Round 1)

**Decisión de trabajo:** no repetir por ahora estas campañas de sensibilidad. Están completas en su alcance; usar sus resultados como evidencia **descriptiva y acotada**, no como prueba de robustez estadística/general. Continuar con experimentos de más instancias y ablación sin DDTW por separado. Este documento es el traslado documental durable a `dtw_discreto`: el diseño `SENSIBILIDAD_OAT.md`, el módulo `sensibilidad/` y los JSON primarios permanecen solo en la rama OAT. Los árboles locales `results*` anteriores al OAT se retiraron de esta rama en el commit `fe12f2f`; este registro no implica que los artefactos primarios estén disponibles aquí.

## Alcance y trazabilidad

La observación literal R1.4 del Revisor 1 solicita examinar el efecto de variar la ventana W=200, la banda Sakoe–Chiba, los percentiles 40/60, τ_pat=3 y π_max=5 (carta [`REVIEWER_1.md`](REVIEWER_1.md) en `dtw_discreto`). El estudio cambia **un factor a la vez**: seis parámetros, tres valores alternativos por parámetro y una configuración base, para 19 configuraciones por estrategia. `min_slope=2.0` permanece fijo. El diseño está descrito en `SENSIBILIDAD_OAT.md` de la rama OAT (archivo ausente en esta rama).

| Campaña | Estrategia | Cobertura | Archivos y épocas auditados |
|---|---|---|---|
| `20260921_102530` | `binary_complex` | `mknapcb1[0,15,29]`, PSO/GA/GWO/DE, 31 semillas/épocas | 19/19 configuraciones; 228/228 JSON con 31 valores `fitness` finitos: 7068/7068 |
| `20260922_174725` | `binary_simple` | Los mismos índices, MH y número de épocas; **estrategia distinta** | 19/19 configuraciones; 228/228 JSON con 31 valores `fitness` finitos: 7068/7068 |

La auditoría de lectura verificó nombres esperados y metadatos de campaña/estrategia/instancia/índice/MH/épocas en todos los archivos; no detectó faltantes ni nombres alternativos en los directorios esperados. `info.config_id` e `info.config_index` no figuran dentro de cada JSON: la relación configuración–resultado se comprobó por el manifiesto, la ruta y `info.campaign_id`. No se volvieron a ejecutar experimentos. Fuentes primarias (solo rama OAT): `results/sensibilidad/campaign_<id>/configs.json`, `tabla_oat.md` y los JSON de `results/<estrategia>/todos/mknapcb1_<índice>/comparacion_mhs_<id>_<config>/`; esos resultados locales **no forman parte de este traslado documental**.

## Resultado observado

La siguiente columna resume el mínimo y máximo de `Δ vs base` entre los **tres valores alternativos** de cada parámetro, en unidades absolutas de fitness. En las tablas originales, `Δ vs base` es el promedio **con signo** de las diferencias entre las medias de las cuatro MH; positivo significa fitness mayor. No es un intervalo de confianza ni una medida de variabilidad. Se promedian resultados de MH e índices distintos, por lo que las diferencias opuestas pueden cancelarse.

| Parámetro (valor base) | Alternativas | Binary-Complex: rango Δ | Binary-Simple: rango Δ |
|---|---|---:|---:|
| Ventana W (200) | 50, 100, 400 | −2.780 a −0.484 | −2.132 a +4.801 |
| Banda (2) | 1, 4, 8 | −0.737 a +0.113 | 0.000 |
| Percentil bajo (40) | 20, 30, 50 | −0.008 a +2.777 | −0.599 a +4.180 |
| Percentil alto (60) | 50, 70, 80 | −1.183 a +1.419 | 0.000 |
| Límite de meseta π_max (5) | 3, 8, 12 | −0.129 a +0.304 | 0.000 |
| Paciencia τ_pat (3) | 1, 2, 5 | −3.970 a +2.038 | 0.000 |

En Binary-Complex, el signo cambia para varios parámetros: la configuración del paper **no es la mejor en todas las combinaciones**. Por ejemplo, paciencia 1 da Δ=−3.970 y paciencia 5 da Δ=+2.038; a nivel MH, las variaciones pueden tener signos opuestos. En Binary-Simple, banda, percentil alto, límite de meseta y paciencia producen filas idénticas a la base; esto es compatible con su regla de disparo basada en D2 contra la constante, **no** demuestra insensibilidad del controlador Binary-Complex. Binary-Simple no es una segunda réplica independiente de la campaña Binary-Complex.

## Qué se puede responder y qué falta

- **R1.4, evidencia disponible:** se variaron los seis parámetros pedidos con una base fija y 31 épocas sobre tres índices de `mknapcb1`, sin faltantes en las salidas esperadas. Presentar los efectos separados por estrategia, MH e índice; evitar afirmar superioridad universal o que los valores del paper son óptimos.
- **Análisis pendiente antes de cerrar la respuesta:** calcular diferencias *pareadas* base–alternativa por misma estrategia, MH, índice y semilla/época, con denominadores y dispersión (por ejemplo, mediana e intervalo descriptivo). Las tablas actuales solo informan medias agregadas; no aportan pruebas, intervalos ni corrección por comparaciones múltiples. No inventar significancia ni interpretar cambios pequeños como significativos.
- **Límite de alcance:** OAT sobre tres índices de un solo grupo (`mknapcb1`) no prueba sensibilidad entre los otros ocho grupos ni resuelve R1.3 (amplitud de instancias), R2.2 (ablación sin DDTW) o R2.3 (justificación de las referencias lineal/constante y la pendiente fija). Tampoco varía `min_slope` ni estudia interacciones entre parámetros, límites propios de un diseño OAT.
- **Próximos experimentos:** priorizar la campaña multi-instancia planificada y una ablación/baseline no DDTW; ampliar OAT a otros problemas solo si el análisis pareado revela una interacción relevante o la respuesta al revisor requiere explícitamente generalizar la sensibilidad entre grupos. El usuario es quien envía cualquier job Slurm; este informe no ejecuta ni autoriza envíos.
