# Feature: Limpieza post-merge — documentación, estructura y radiadores

Fecha de creación: 2026-09-23 · Rama: `dtw_discreto`
Origen: solicitud del usuario tras el merge con la rama `OAT` (análisis de sensibilidad de parámetros). Objetivo: dejar el repo limpio en información y estructura de archivos `.md`, con radiadores de información consistentes.

## Decisiones del usuario (autoridad para este cambio)

0. **Alcance ampliado (decisión posterior)**: «limpiar todo» — el repo queda en cero para los experimentos nuevos basados en los parámetros del OAT. Se autoriza borrar lo obsoleto (queda en la historia de git).
1. **Alcance**: documentación + archivado/etiquetado de artefactos + bajas de lo obsoleto autorizadas.
2. **Protocolo oficial de instancias**: muestreo **seed**, **3 instancias por archivo** de problema (27 en total), para responder a la petición de más experimentos de los revisores. La tabla de `frente2-multi-instancia.md` (mknapcb1: 0,18,26 …) es la autoridad; `INSTANCIAS_SELECCIONADAS.md` se reconcilia hacia ella.
3. **Código legacy**: limpiarlo; quedan en pie las estrategias importantes `binary_simple`, `binary_patient`, `binary_complex` (más las bases vanilla: `vanilla/` es dependencia de `vanilla_explotacion` y baseline del análisis, no se toca).
4. **`results*`**: el usuario los borró a mano. Se registra la baja en git (sin recuperar), queda `results/` como output activo y un catálogo de las campañas que hubo.

## Tareas

1. [ ] Verificación de suelo falso (read-only): dependencias reales de `vanilla/` y `binary_hysteresis/`, estrategias registradas en `run_all.py`/`run_all_hpc.py`, valores vigentes de config, método y baseline de `analisis/estadistico.py`, headers reales de los 9 `instances/mknapcb*.txt`.
2. [ ] Registrar la baja de los 1456 archivos `results*` en git y crear el catálogo de campañas históricas (radiador).
3. [ ] Operaciones git de estructura: baja del código legacy (`binary_hysteresis/`) y renombrado de archivos con espacios/paréntesis (`Reviewer N.md`, `OII464__calse_3 (1).md`, `02_binary_hysteresis_a4.md` → `02_binary_complex_a9.md`).
4. [ ] Reescritura de la navegación: `README.md` raíz y `contexto/README.md` como autoridad única (estrategias reales, comandos reales, resultados, método estadístico real).
5. [ ] Consolidación de docs de estrategia: `01_binary_simple_fire_d2.md` (config versionada: paper vs vigente), `02_binary_complex_a9.md` (rename + nota legacy), enlace a A10 en vez de copiar.
6. [ ] Reconciliación de instancias y parámetros: `INSTANCIAS_SELECCIONADAS.md` → seed 3/file con la tabla oficial; `instancias_mkp.md` → tabla corregida desde los headers de los archivos de datos.
7. [ ] Actualización de docs de revisión Round-1: `PREGUNTAS_Y_RESPUESTAS_REVISORES.md` (R1.4 → evidencia OAT), `SINTESIS_REVIEWS.md`, `HALLAZGOS_OAT.md` (referencia a `SENSIBILIDAD_OAT.md` etiquetada como rama `OAT`), `especificacion_extraccion_datos.md` etiquetada como especificación futura.
8. [ ] Cierre de ledgers `odd/tasks/`: `binary-patient-a10.md` y `frente2-multi-instancia.md` reconciliados con el estado real; tareas verificadas marcadas.
9. [ ] Verificación final (read-only): referencias y enlaces entre `.md`, consistencia de nombres, `git status` limpio; reporte de pendientes.

## No-goals

- No se cambia comportamiento de código de las estrategias ni de `run_all*.py` (salvo bajas de legacy no referenciado).
- No se fijan nuevos valores de parámetros en `mkp_common/config.py` en esta feature: la documentación declara el baseline post-OAT (paper vs actual vs alternativas OAT) y la decisión final de valores queda marcada para el usuario.
- No se ejecutan campañas HPC ni se regeneran resultados.
- No se restauran los `results*` borrados por el usuario.
- No se traducen las cartas de revisores ni se altera su contenido (solo se renombran archivos).

## Evidencia de commits

(pendiente)
