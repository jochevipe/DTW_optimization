# Contexto del Proyecto: MKP Solver con DTW Auto-Adaptativo

## Objetivo del Proyecto

Framework modular en Python para resolver el **Multidimensional Knapsack Problem (MKP)** usando metaheurísticas poblacionales (PSO, GA, GWO) con un monitor de estancamiento basado en **Dynamic Time Warping (DTW)** que actúa como sistema auto-adaptativo.

El DTW mide la curva de convergencia contra patrones de referencia (rampa ideal vs meseta) y dispara cambios de parámetros cuando detecta estancamiento, alternando entre modos EXPLOIT y EXPLORE.

**Contexto académico**: Investigación universitaria. El objetivo final es un paper comparando enfoques de auto-adaptación con DTW.

---

## Estructura del Proyecto

```
LB2_mkp/
├── run.py                  # Entry point — CONFIG CENTRAL (todos los scripts importan de acá)
├── resultados.py           # Script maestro: corre TODAS las MHs, genera plots y JSONs
├── plot_experiment.py      # Plot individual de 1 MH (importa config de run.py)
│
├── mkp_solver/             # Paquete principal
│   ├── __init__.py         # Exports: BinaryPSO, GeneticAlgorithm, BinaryGWO, cargar_instancia, etc.
│   ├── problem.py          # Carga instancias OR-Library + tabla óptimos Chu & Beasley + reparación greedy
│   ├── monitor.py          # StagnationMonitor: DTW, DDTW, baselines, lógica de 3 condiciones + fire
│   ├── base.py             # BaseMH: interfaz abstracta (initialize, step, adapt, get_best)
│   ├── runner.py           # Orquestador MH-agnostico: run_experiment() y run_epochs()
│   ├── results.py          # Utilidades: diagnóstico, plots, save/load JSON
│   └── mh/                 # Subpaquete de metaheurísticas
│       ├── __init__.py     # Exports: BinaryPSO, GeneticAlgorithm, BinaryGWO
│       ├── pso.py          # Binary PSO (Kennedy & Eberhart 1997, sigmoid)
│       ├── ga.py           # GA (torneo, crossover uniforme, bit-flip)
│       └── gwo.py          # Binary GWO (Mirjalili 2014, alpha/beta/delta, sigmoid)
│
├── instances/              # Archivos de instancias OR-Library
│   ├── mknapcb1.txt        # 5 constraints, 100 items, 30 instancias
│   ├── mknapcb4.txt        # 10 constraints, 100 items, 30 instancias
│   └── ...                 # Otros archivos cb
│
├── results/                # Salida: JSONs y PNGs
│   ├── BinaryPSO_mknapcb4_0.json
│   ├── GA_mknapcb4_0.json
│   ├── GWO_mknapcb4_0.json
│   └── comparacion_mhs.png
│
├── contexto/               # Documentos de contexto
│   └── enfoques_adaptacion_dtw.md  # Comparación de 3 enfoques de adaptación
│
└── antiguo/                # Scripts originales (monolítico, referencia)
    └── pso_dtw_mkp.py
```

---

## Arquitectura del Sistema

### Flujo de Ejecución

```
run.py (config) → cargar_instancia() → run_epochs()
                                           │
                                           ├── Para cada epoch (semilla diferente):
                                           │   ├── mh.initialize()
                                           │   ├── Para cada iteración:
                                           │   │   ├── fitness = mh.step()
                                           │   │   ├── status = monitor.update(fitness)
                                           │   │   ├── if status["fire"]: mh.adapt(True)  → EXPLORE
                                           │   │   └── if mejora:         mh.adapt(False) → EXPLOIT
                                           │   └── Retorna resultado del epoch
                                           └── Retorna lista de resultados
```

### Interfaz BaseMH

Toda MH debe heredar de `BaseMH` e implementar:

| Método | Descripción |
|--------|-------------|
| `initialize()` | Crear población, evaluar, definir gbest |
| `step() → float` | Ejecutar 1 iteración, retornar gbest_fitness |
| `adapt(fire: bool)` | Cambiar parámetros: fire=True→EXPLORE, fire=False→EXPLOIT |
| `get_best() → (array, float)` | Retornar mejor solución y fitness |

### MHs Implementadas

| MH | Param EXPLOIT | Param EXPLORE |
|----|--------------|---------------|
| **BinaryPSO** | w=0.729, c1=1.49, c2=1.49 | w=0.9, c1=2.5, c2=0.5 |
| **GA** | cx_rate=0.9, mut_rate=0.01 | cx_rate=0.6, mut_rate=0.15 |
| **BinaryGWO** | a=0.5 (converger) | a=2.0 (divergir) |

---

## Monitor DTW (StagnationMonitor)

### Métricas

- **D1**: Distancia DTW entre la ventana de fitness y una rampa ideal (progreso constante)
- **D2**: Distancia DTW entre la ventana de fitness y una meseta (estancamiento total)
- **delta = D1 - D2**: Positivo = más cerca de meseta = estancamiento

### Lógica de Fire (3 condiciones simultáneas)

```
fire = True  cuando  trigger_streak >= patience  Y las 3 condiciones:
  1. cond_plateau:  no_improve_len >= plateau_max
  2. cond_constant: D2 <= theta_c     (curva se parece a meseta)
  3. cond_ramp:     D1 >= theta_r  OR  delta >= theta_delta
```

### Umbrales adaptativos

Con `adapt_thresholds=True`, theta_c, theta_r, theta_delta se calculan como percentiles móviles del historial de D1, D2, delta (p_low=30, p_high=70).

### Configuración actual (run.py)

```python
DTW_CFG = StagnationConfig(
    window=15,        # Ventana de observación
    band=2,           # Banda Sakoe-Chiba
    plateau_max=10,   # Iteraciones sin mejora para considerar plateau
    patience=2,       # Confirmaciones consecutivas para fire
    min_slope=2.0,    # Pendiente mínima de la rampa
    use_ddtw=True,    # Usar Derivative DTW (más robusto)
    adapt_thresholds=True,  # Umbrales adaptativos via percentiles
)
```

---

## Instancias

### Formato

Archivos OR-Library (Chu & Beasley 1998). Cada archivo contiene 30 instancias agrupadas por tightness ratio:
- Instancias 0-9: ratio 0.25 (más restrictiva)
- Instancias 10-19: ratio 0.50
- Instancias 20-29: ratio 0.75 (más holgada)

### Naming

| Archivo | Constraints (m) | Items (n) |
|---------|----------------|-----------|
| mknapcb1 | 5 | 100 |
| mknapcb2 | 5 | 250 |
| mknapcb3 | 5 | 500 |
| mknapcb4 | 10 | 100 |
| mknapcb5 | 10 | 250 |
| mknapcb6 | 10 | 500 |
| mknapcb7 | 30 | 100 |
| mknapcb8 | 30 | 250 |
| mknapcb9 | 30 | 500 |

### Óptimos conocidos

Los archivos tienen `optimo=0`. El sistema tiene una tabla interna (`_OPTIMOS_CB` en `problem.py`) con los 270 valores óptimos de la literatura (Chu & Beasley, OR-Library mkcbres). Se buscan automáticamente por nombre de archivo + índice.

---

## Scripts de Ejecución

### `run.py` — Entry point y CONFIG CENTRAL

**IMPORTANTE**: Todos los demás scripts (`resultados.py`, `plot_experiment.py`) importan la configuración de `run.py`. Cambiar parámetros acá afecta todo.

Variables exportadas: `RUTA_INSTANCIA`, `INDICE_INSTANCIA`, `NUM_PARTICULAS`, `NUM_ITERACIONES`, `EPOCHS`, `VERBOSE`, `MH_CLASS`, `DTW_CFG`.

### `resultados.py` — Script maestro

1. Corre TODAS las MHs definidas en `MHS = {"BinaryPSO": ..., "GA": ..., "GWO": ...}`
2. Imprime en consola: fitness + DTW params (D1, D2, delta, thetas) por epoch
3. Guarda JSONs individuales por MH con `optimo_conocido` y `gap_al_optimo`
4. Genera gráfico de 2 paneles:
   - **Panel 1**: Fitness de todas las MHs superpuestas (línea sólida=exploit, punteada=explore)
   - **Panel 2**: Delta de cada MH con theta_delta como referencia

### `plot_experiment.py` — Plot individual

Visualiza 1 corrida de la MH configurada en `run.py` con 3 paneles: convergencia, D1/D2, delta.

---

## Formato JSON de Resultados

```json
{
  "mh": "GA",
  "epochs": 10,
  "optimo_conocido": 23064.0,
  "fitness": [22713.0, ...],
  "fire_counts": [1, 2, ...],
  "ganancias": [98.47, ...],
  "tiempos": [0.64, ...],
  "stats": {
    "mejor": 22850.0,
    "promedio": 22729.3,
    "peor": 22479.0,
    "std": 107.01,
    "gap_al_optimo": 0.9279
  },
  "info": {
    "instancia": "instances/mknapcb4.txt",
    "idx": 0,
    "poblacion": 20,
    "iteraciones": 100,
    "dtw_window": 15,
    "dtw_patience": 2
  }
}
```

---

## Resultados Actuales (mknapcb4[0], óptimo=23064, pop=20, 100 iter, 10 epochs)

| MH | Mejor | Gap | Promedio | Std | Fires promedio |
|----|-------|-----|----------|-----|----------------|
| GA | 22850 | 0.93% | 22729 | 107 | 1-3 |
| PSO | 22720 | 1.49% | 22584 | 85 | 2-3 |
| GWO | 22579 | 2.10% | 22421 | 99 | 1-2 |

---

## Enfoques de Auto-Adaptación (Investigación)

Se documentaron 3 enfoques posibles en `contexto/enfoques_adaptacion_dtw.md`:

### A. Fire Binario (implementado actualmente)
- 3 condiciones + patience → switch binario entre 2 sets fijos de params
- Reactivo, pierde info continua del DTW

### B. Multi-Estado (enfoque anterior del investigador)
- Usa rangos de delta directamente → 4+ estados discretos
- Más granular y reactivo que Fire, pero sigue siendo discreto

### C. Adaptación Proporcional (propuesta para paper)
- Normalizar delta a score [0,1] → interpolar parámetros continuamente
- Usa TODA la información del DTW, proactivo, menos hiperparámetros
- **Contribución más fuerte para el paper**

---

## Dependencias

- **Python 3.11+**
- **numpy** — cálculos numéricos, DTW, operaciones vectoriales
- **matplotlib** — visualización (opcional, el core funciona sin ella)

No se usa ninguna otra librería. El DTW está implementado desde cero (no usa librería externa).

---

## Cómo agregar una nueva MH

1. Crear `mkp_solver/mh/nueva_mh.py`
2. Heredar de `BaseMH`, implementar `initialize()`, `step()`, `adapt()`, `get_best()`
3. Agregar import en `mkp_solver/mh/__init__.py`
4. Agregar import en `mkp_solver/__init__.py`
5. Agregar entrada en `MHS` dict de `resultados.py`
6. Agregar color en `MH_COLORS` de `resultados.py`

---

## Gotchas y notas técnicas

- **Windows cp1252**: La consola de Windows no soporta caracteres Unicode como θ, ─. Usar ASCII alternatives.
- **Óptimos en 0**: Los archivos de instancia CB tienen optimo=0. Se resuelve con la tabla `_OPTIMOS_CB`.
- **Reproducibilidad**: Cada epoch usa `numpy.random.default_rng(seed)` con semillas incrementales (1, 2, 3...) para reproducibilidad exacta.
- **GWO con poca población**: Con pop=20, GWO rinde peor porque alpha/beta/delta necesitan más diversidad. Con 40-50 mejora significativamente.
- **DDTW**: `use_ddtw=True` es más robusto que DTW estándar para detectar estancamiento porque mide la forma de la curva (derivadas) en vez de valores absolutos.
- **np.clip en sigmoid**: En GWO, se clipea la entrada del sigmoid a [-10, 10] para evitar overflow warnings.
