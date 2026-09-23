# Especificación de Extracción de Datos, Tablas LaTeX y Gráficos

> **Estado: especificación de un pipeline futuro; NO implementado.** Los campos, tablas y gráficos pedidos abajo describen salidas deseadas, no el esquema JSON disponible hoy. El análisis estadístico implementado usa **Wilcoxon signed-rank pareado** por semilla contra Vanilla-Exploration (`vanilla_exploracion`), **no** Wilcoxon rank-sum; la propuesta de rank-sum de la sección 3 no describe el análisis actual. `state_history` y las métricas DTW por iteración no se persisten hoy en los JSON: `historial_dtw` y `historial_modos` existen en memoria durante cada corrida. Tampoco hay resultados de campañas previas en `results/` tras la limpieza.

Este documento define la estructura requerida para los scripts de procesamiento de datos y generación de salidas (tablas LaTeX y figuras en formato PDF/PNG) a partir de los archivos `.json` de resultados.

---

## 1. Estructura de Datos de Entrada (Archivos JSON)

Cada archivo de resultado por corrida o consolidado debe contener la información correspondiente a:

- **9 instancias**: $n \in \{100, 250, 500\}$, $m \in \{5, 10, 30\}$
- **4 metaheurísticas**: BPSO, GA, BGWO, BDE
- **31 corridas independientes**: $R = 31$
- **Estrategias evaluadas**: Base/Explotación pura, Binary-Simple, Binary-Hysteresis

### Campos requeridos por registro/corrida

| Campo | Descripción |
|---|---|
| `instance` | Identificador de la instancia (ej. `mknapcb1`, ..., `mknapcb9`) |
| `known_optimum` | Valor del óptimo global conocido ($f^*$) |
| `algorithm` | Metaheurística utilizada (BPSO, GA, BGWO, BDE) |
| `strategy` | Estrategia de control (Default/Sin DTW, Binary-Simple, Binary-Hysteresis) |
| `run_id` / `seed` | Identificador de la corrida ($1 \dots 31$) |
| `best_fitness` | Mejor valor de función objetivo alcanzado al final de la corrida ($f_{\text{run}}$) |
| `execution_time_sec` | Tiempo total de ejecución en segundos |
| `convergence_history` | Vector de longitud $T = 2000$ con el mejor fitness acumulado $f^*_t$ por iteración |
| `state_history` | Vector binario de longitud $T$ con el estado de control $s_t \in \{0, 1\}$ ($0$: Explotación, $1$: Exploración) |
| `dtw_metrics` (opcional por iteración) | Valores de $D_1, D_2, \Delta, \theta_c, \theta_r, \theta_\Delta$ |

---

## 2. Definición de Métricas Matemáticas

**Mejor Fitness Global** ($f_{\max}$):

$$f_{\max} = \max_{r=1 \dots R} f_{\text{run}}^{(r)}$$

**Fitness Promedio** ($f_{\text{avg}}$) **y Desviación Estándar** ($\sigma$):

$$f_{\text{avg}} = \frac{1}{R} \sum_{r=1}^R f_{\text{run}}^{(r)}, \quad \sigma = \sqrt{\frac{1}{R-1} \sum_{r=1}^R \left(f_{\text{run}}^{(r)} - f_{\text{avg}}\right)^2}$$

**Desviación Porcentual Relativa del Mejor** (RPD):

$$\text{RPD} = \frac{f^* - f_{\max}}{f^*} \times 100\%$$

**Gap Promedio respecto al Óptimo** ($\text{Gap}_{\text{mean}}$):

$$\text{Gap}_{\text{mean}} = \frac{f^* - f_{\text{avg}}}{f^*} \times 100\%$$

**Tasa de Exploración / Duty Cycle** ($DC$):

$$DC = \frac{1}{T - W} \sum_{t = W + 1}^T s_t \times 100\%$$

---

## 3. Tablas LaTeX Requeridas

### Tabla 1: Tabla Maestra de Calidad de Solución

Consolida el rendimiento de todas las metaheurísticas y estrategias a lo largo de las 9 instancias.

**Estructura de columnas:**

1. Instancia ($m, n$)
2. Óptimo ($f^*$)
3. Algoritmo / Variante
4. Best ($f_{\max}$)
5. Mean ($f_{\text{avg}}$)
6. Std ($\sigma$)
7. RPD (%)
8. Gap (%)

**Formato:** Los mejores valores promedio por bloque de instancia deben formatearse automáticamente con `\textbf{...}`.

### Tabla 2: Validación Estadística No Paramétrica

**Test de Wilcoxon Rank-Sum (Pairwise):**

Comparación entre la variante propuesta (Binary-Hysteresis) frente a Binary-Simple y frente a la versión base (sin DTW) sobre las $R = 31$ corridas con nivel de significancia $\alpha = 0.05$.

**Símbolos de veredicto:**

| Símbolo | Significado |
|---|---|
| `+` | Diferencia estadísticamente significativa a favor de Binary-Hysteresis ($p < 0.05$ y mediana superior) |
| `≈` | Sin diferencia significativa ($p \ge 0.05$) |
| `-` | Variante comparada estadísticamente superior a Binary-Hysteresis ($p < 0.05$ y mediana inferior) |

**Test de Friedman (Global):**

Ranking promedio de cada método a través de todas las instancias evaluadas.

### Tabla 3: Costo Computacional (CPU Time)

**Estructura de columnas:**

- Instancia
- Tiempo promedio (segundos) y desviación por cada combinación de MH y estrategia
- Métrica de sobrecosto relativo ($\Delta t_{\%}$) para cuantificar el impacto del cálculo de DTW respecto a la ejecución base

---

## 4. Gráficos y Visualizaciones Requeridas

### Figura 1: Distribución de Soluciones (Grid de Boxplots 3×3)

- **Layout:** Entorno `figure*` de LaTeX con grilla de 3 filas × 3 columnas (una subfigura por cada una de las 9 instancias `mknapcb1` a `mknapcb9`).
- **Eje Y:** Fitness alcanzado en las 31 corridas (o Gap respecto al óptimo para unificar escala).
- **Eje X:** Metaheurísticas agrupadas por estrategia de control.
- **Línea de referencia:** Línea horizontal punteada roja indicando el valor del óptimo conocido ($f^*$).

### Figura 2: Dinámica de Conmutación y Convergencia DTW

- **Instancias representativas:** Seleccionar una instancia mediana (`mknapcb5`, $m=10, n=250$) y una de alta dimensionalidad (`mknapcb9`, $m=30, n=500$).
- **Curva principal:** Trayectoria de $f^*_t$ a lo largo de las $T = 2000$ iteraciones.
- **Capa de estado:** Sombreado de fondo o línea inferior indicando los períodos donde el controlador DTW activó el modo de exploración ($s_t = 1$) vs explotación ($s_t = 0$).
- **Marcador de Warm-up:** Línea vertical en $t = W$ indicando el inicio del monitoreo activo.

---

## 5. Pipeline de Procesamiento Recomendado (Python)

```
[Archivos JSON de Resultados]
             │
             ▼
   [Script de Procesamiento]
   ├── 1. Parser y Consolidación (pandas DataFrame)
   ├── 2. Cálculo de Métricas (Best, Mean, Std, RPD, Gap, DC)
   ├── 3. Tests Estadísticos (scipy.stats.wilcoxon, scipy.stats.friedmanchisquare)
   └── 4. Generación de Salidas
             ├─► tabla_master_rendimiento.tex
             ├─► tabla_estadistica_wilcoxon.tex
             ├─► tabla_tiempos_computacionales.tex
             ├─► fig_boxplots_grid.pdf
             └─► fig_dtw_switching_dynamics.pdf
```
