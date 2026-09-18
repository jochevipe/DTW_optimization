# Síntesis Round 1 — MDPI Major Revision

Paper: DDTW-based adaptive configuration control para MKP (`contexto/latex/template.tex`).
Estrategias del paper: Vanilla-Exploitation, Vanilla-Exploration, Binary-Simple, Binary-Complex.

> **Mapeo verificado**: `Binary-Complex` del paper = `binary_complex` del código actual (antes `binary_hysteresis`).
> La estrategia (A9) usa el disparo A4 sostenido del monitor (meseta ∧ D2≤θc ∧ (D1≥θr ∨ δ≥θδ) durante `patience`
> iteraciones) para ENTRAR a explore, y mejora real (`no_improve_len == 0`) para SALIR.
> Coincide exactamente con la Eq. (26) del paper (entrada con persistencia τ_pat, salida asimétrica ante mejora).

## 1. Calificaciones generales

| Revisor | Tono | Comentarios |
|---|---|---|
| R1 | El más amable: intro/diseño/métodos/figuras OK; resultados y conclusiones "Can be improved" | 5 |
| R2 | Todo "Can be improved" salvo figuras | 6 |
| R3 | El más exigente: todo "Can be improved", incluso figuras | 8 |

## 2. Temas agrupados (repeticiones entre revisores)

### 🔴 A. Evidencia estadística de la contribución — EXISTENCIAL
- **R1.1** — Friedman global NO significativo (χ²=4.13, p=0.2474). El ranking (2.22 vs 2.83) es solo "tendencia favorable". R1: *"the greatest weakness... directly contradicts the selling point"*.
- **R2.2** — Falta un **ablation study** que demuestre que el DDTW es responsable de las mejoras.

### 🔴 B. Comparación con el estado del arte adaptativo — REPETIDO POR LOS 3
- **R1.2** — "No comparison with existing adaptive control systems."
- **R2.4** — Incluir métodos adaptativos SOTA como baselines adicionales.
- **R3.1** — Definir research gap vs. adaptive parameter-control e hyper-heuristics.
- **R3.2** — Reforzar literatura: adaptive parameter control, RL, fuzzy control, trajectory-based analysis.

### 🔴 C. Sensibilidad y justificación de hiperparámetros — REPETIDO POR LOS 3
- **R1.4** — Estudio de sensibilidad: W=200, banda Sakoe-Chiba, percentiles 40/60, τ_pat=3, π_max=5.
- **R2.3** — Justificar por qué rampa lineal + constante (pendiente fija) caracterizan bien las dinámicas de las 4 MH.
- **R3.5** — Cómo se eligieron los valores explore/exploit y si fueron tuneados para las instancias evaluadas.

### 🟠 D. Amplitud experimental y consistencia por algoritmo
- **R1.3** — Solo el primer problema de cada grupo Chu–Beasley.
- **R1.5 + R3.7** (repetido entre sí) — Efectos inconsistentes: BDE y GA se benefician; BPSO y BGWO no. Analizar por qué (dinámica poblacional, sensibilidad de parámetros, reparación, mecanismos de exploración).

### 🟡 E. Claridad metodológica — bajo costo, alto retorno
- **R3.3** — Definición matemática completa de DDTW (derivada, normalización, boundary handling).
- **R3.6** — Pseudocódigo completo (el paper ya tiene el Algorithm 1; ampliarlo).
- **R3.4 + R3.8** — Plots: trayectoria best-so-far, referencias rampa/plateau, D_R(t), D_C(t), Δ(t), estado del controlador, cambios de parámetros.
- **R2.5** — Código público para reproducibilidad.

### ⚪ F. Escritura/organización
- **R2.1** — Hoja de ruta al final de la Sección 1.
- **R2.6** — Corregir el abstract desde la primera oración.

## 3. Primordiales (top 5)

1. **Evidencia**: responder al Friedman no significativo + ablation del DDTW (A).
2. **Baselines adaptativos externos** (B) — lo piden los 3, innegociable.
3. **Sensibilidad/justificación de diseño** (C) — lo piden los 3.
4. **Análisis por algoritmo + más instancias** (D) — R1 y R3 coinciden.
5. **Claridad metodológica** (E) — barato y exigido explícitamente por R3.

## 4. Foco acordado para esta etapa (3 frentes)

### Frente 1 — Otro approach adaptativo para comparar
- Idea del usuario: variante D1-only (¿qué tan cerca del progreso constante?) y/o simple con capa de patience.
- ⚠️ Ojo: una variante D1-only sigue siendo DDTW propio. Los revisores piden comparación contra approaches EXISTENTES (literatura). Recomendación: implementar también un **controlador de contador/patience SIN DTW** (clásico stagnation-switching: k iteraciones sin mejora → explore; mejora → exploit). Ese es el baseline natural de la literatura y a la vez el ablation que pide R2.2.
- **Estado (18/09)**: ✅ variante DTW nueva implementada — **A10 Binary-Patient** (`binary_patient/`): entrada `D2 ≤ θc` sostenido `patience` iteraciones, salida con mejora. Ver `ESTRATEGIA_A10_BINARY_PATIENT.md`. ⏳ Pendiente: el controlador contador/patience SIN DTW (baseline externo + ablation R2.2).

### Frente 2 — Más instancias por grupo
- Estructura real: 9 archivos mknapcb (m ∈ {5,10,30} × n ∈ {100,250,500}), **30 instancias cada uno** (idx 0..29). El paper solo usó idx=0.
- Idea del usuario: 3 chicas / 3 medianas / 3 grandes por grupo. Recomendación: mantener los 9 grupos (ya cubren chicas/medianas/grandes) y muestrear K índices por grupo (ej. K=3 → 27 instancias) con índices fijos y documentados.

### Frente 3 — Sensibilidad de hiperparámetros
- Parámetros del paper (Tabla 4): W=200, banda=2, s_min=2.0, p_low=40, p_high=60, π_max=5, τ_pat=3, T=2000, R=31, N=20.
- **Sistema OAT listo** (rama `OAT`, `sensibilidad/`): grid de 6 parámetros × 4 valores centrados en el paper → **19 configuraciones** (1 base + 3 off-base por parámetro). Alcance = exactamente los parámetros citados por R1.4: W, banda Sakoe-Chiba, percentiles (p_low/p_high), π_max, τ_pat. `s_min` queda fijo en 2.0.
- Instancias del OAT: `mknapcb1[0,15,29]` (estrategia Binary-Complex, 31 epochs × 2000 iteraciones).
- Comandos HPC: `python -m sensibilidad.run_sensitivity --cpus 40 --epochs 31` (+ `--campaign <id>` para resume) y `python -m sensibilidad.analizar --campaign <id>` para la tabla OAT.
- Los plots de señales para R3.4/R3.8 (trayectoria best-so-far, D_R(t), D_C(t), Δ(t), estado del controlador) ya se generan por corrida con los plotters de cada estrategia y con `binary_complex/run.py` (análisis individual).

## 5. Configuración para re-experimentos (valores del paper)

| Parámetro | Paper | Código actual (`mkp_common/config.py`) |
|---|---|---|
| Iteraciones T | 2000 | 20 (comentado `#1000`) |
| Epochs R | 31 | 2 (comentado `#31`) |
| Ventana W | 200 | 20 |
| p_low / p_high | 40 / 60 | 30 / 70 (defaults de `StagnationConfig`) |
| plateau_max (π_max) | 5 | 4 |
| patience (τ_pat) | 3 | 2 |

⚠️ Antes de correr cualquier campaña de revisión hay que alinear `mkp_common/config.py` a los valores del paper.

## 6. Criterios de respuesta por comentario (cómo contestar)

| Comentario | Respuesta planificada |
|---|---|
| R1.1 / R2.2 | Reforzar evidencia: Wilcoxon por instancia/MH ya existente + ablation con controlador contador sin DTW + reencuadrar el claim como "ganancia por condición", no superioridad universal. |
| R1.2 / R2.4 / R3.1 / R3.2 | Agregar baseline adaptativo externo (contador/patience) + literatura de APC/fuzzy/RL en Related Work + research gap explícito. |
| R1.4 / R2.3 / R3.5 | Tabla de sensibilidad OAT (one-factor-at-a-time) sobre W, banda, s_min, percentiles, π_max, τ_pat + justificación: valores elegidos por el estudio, sin tuning por instancia. |
| R1.3 | Extender evaluación a múltiples instancias por grupo (ej. 3 índices fijos por archivo). |
| R1.5 / R3.7 | Subsección de análisis por algoritmo: por qué BDE/GA responden mejor que BPSO/BGWO. |
| R3.3 / R3.6 / R3.4 / R3.8 | Definición completa DDTW + pseudocódigo ampliado + figuras de trayectorias/señales/estados (los datos ya se registran en `historial_dtw`/`historial_modos`). |
| R2.5 | Publicar código en GitHub (repo ya existe). |
| R2.1 / R2.6 | Roadmap en Sec. 1 + corregir abstract. |
