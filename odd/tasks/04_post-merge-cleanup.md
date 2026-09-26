# Feature: Limpieza post-merge — documentación, estructura y radiadores

Fecha de creación: 2026-09-23 · Rama: `dtw_discreto`
Origen: solicitud del usuario tras el merge con la rama `OAT` (análisis de sensibilidad de parámetros). Objetivo: dejar el repo limpio en información y estructura de archivos `.md`, con radiadores de información consistentes.

## Decisiones del usuario (autoridad para este cambio)

0. **Alcance ampliado (decisión posterior)**: «limpiar todo» — el repo queda en cero para los experimentos nuevos basados en los parámetros del OAT. Se autoriza borrar lo obsoleto (queda en la historia de git).
1. **Alcance**: documentación + archivado/etiquetado de artefactos + bajas de lo obsoleto autorizadas.
2. **Protocolo oficial de instancias**: muestreo **seed**, **3 instancias por archivo** de problema (27 en total), para responder a la petición de más experimentos de los revisores. La tabla de `02_frente2-multi-instancia.md` (mknapcb1: 0,18,26 …) es la autoridad; `INSTANCIAS_SELECCIONADAS.md` se reconcilia hacia ella.
3. **Código legacy**: limpiarlo; quedan en pie las estrategias importantes `binary_simple`, `binary_patient`, `binary_complex` (más las bases vanilla: `vanilla/` es runner compartido re-exportado por `vanilla_explotacion`; la baseline del análisis estadístico es `vanilla_exploracion` / Vanilla-Exploration).
4. **`results*`**: el usuario los borró a mano. Se registra la baja en git (sin recuperar), queda `results/` como output activo y un catálogo de las campañas que hubo.

## Tareas

1. [x] Verificación de suelo falso (read-only): deps, registros, config, stats e headers verificados (gentle-ai-verify).
2. [x] Registrar la baja de los 1456 archivos `results*` en git (catálogo → tarea 7).
3. [x] Operaciones git de estructura: baja de `binary_hysteresis/` y `contexto/miscelaneo/`, renombrados y notebook → `contexto/historico/`.
4. [x] Reescritura de la navegación: `README.md` y `contexto/README.md`.
5. [x] Consolidación de docs de estrategia: `01_binary_simple_fire_d2.md` (config versionada: paper vs vigente), `02_binary_complex_a9.md` (rename + nota legacy), enlace a A10 en vez de copiar.
6. [x] Reconciliación de instancias y parámetros: `INSTANCIAS_SELECCIONADAS.md` → seed 3/file con la tabla oficial; `instancias_mkp.md` → tabla corregida desde los headers de los archivos de datos.
7. [x] Actualización de docs de revisión Round-1: `PREGUNTAS_Y_RESPUESTAS_REVISORES.md` (R1.4 → evidencia OAT), `SINTESIS_REVIEWS.md`, `HALLAZGOS_OAT.md` (referencia a `SENSIBILIDAD_OAT.md` etiquetada como rama `OAT`), `especificacion_extraccion_datos.md` etiquetada como especificación futura.
8. [x] Cierre de ledgers `odd/tasks/`: `01_binary-patient-a10.md` y `02_frente2-multi-instancia.md` reconciliados con el estado real; tareas verificadas marcadas.
9. [x] Verificación final (read-only): verificador independiente + remediación de sus 3 hallazgos.

## Pendientes para el usuario (post-limpieza)

- Fijar el set definitivo de parámetros post-OAT en `mkp_common/config.py` (hoy: W=100, p_low=20, p_high=80; paper: 200, 40/60) según `HALLAZGOS_OAT.md` y el análisis pareado aún pendiente.
- Análisis pareado base–alternativa del OAT (dispersión) pendiente antes de responder R1.4.
- Baseline no-DTW (stagnation-switching) pendiente: R2.2.

## No-goals

- No se cambia comportamiento de código de las estrategias ni de `run_all*.py` (salvo bajas de legacy no referenciado).
- No se fijan nuevos valores de parámetros en `mkp_common/config.py` en esta feature: la documentación declara el baseline post-OAT (paper vs actual vs alternativas OAT) y la decisión final de valores queda marcada para el usuario.
- No se ejecutan campañas HPC ni se regeneran resultados.
- No se restauran los `results*` borrados por el usuario.
- No se traducen las cartas de revisores ni se altera su contenido (solo se renombran archivos).

## Evidencia de commits

- `fe12f2f` — chore: drop pre-OAT result sets and legacy binary_hysteresis module (1456 archivos de results* + `binary_hysteresis/` + extracción de clase malformada).
- `bcd02f3` — chore: normalize doc filenames and archive legacy notebook (`REVIEWER_1..3.md`, `02_binary_complex_a9.md`, notebook → `contexto/historico/`).
- `8fcedd2` — docs: rebuild navigation README and context index for the post-OAT campaign.
- `d179f8b` — docs(odd): track post-merge cleanup feature.
- `c8eea5b` — docs: consolidate strategy docs for Binary-Simple and Binary-Complex.
- `685778f` — docs: adopt seeded 3-per-file instance protocol as official.
- `40920b8` — docs(round-1): refresh review record for the post-OAT state.
- `52300e3` — docs(odd): close ledgers and catalog the removed pre-OAT campaigns.
- Commit final de remediación de la verificación independiente (este documento lo contiene).

## Resolución TDD y RDD (por delegación)

- **TDD**: desactivado. Fuente: no existe configuración TDD en proyecto/sesión (verificado en `.pi/` y `.atl/`) y el repo no tiene runner de tests (unidad solo-documentación). Runner: no aplica; check funcional = validación de links/paths.
- **RDD**: activo (global). `gentle_review assess` sobre `08c2f29..HEAD` devolvió riesgo `unassessable` (fallos nativos: raíz de trabajo, stop por no-trackeados, `schema-incompatible`) → tratado como high según contrato: autoverificación del escritor + verificador independiente al cierre del rango. Outcome por tarea: `unavailable`.

## Verificación independiente (plan de riesgo RDD)

Verificador independiente (`gentle-ai-verify`) sobre `08c2f29..52300e3`: 82/82 links relativos OK; nombres obsoletos OK; tablas numéricas consistentes y confirmadas contra los headers de los datos; sin claims de Holm-Bonferroni ni baseline errónea en docs del repo; honestidad de estados OK (R1.4 y R2.2 siguen pendientes). Hallazgos remediados en el commit final: (a) dos estados desactualizados en `contexto/README.md`, (b) redacción de este doc que confundía `vanilla/` con la baseline estadística, (c) `__pycache__` residual de `binary_hysteresis/` fuera de git. Ausencias citadas (artefactos OAT en su rama, `results*` borrados, salidas generadas) quedan documentadas: no son defectos.
