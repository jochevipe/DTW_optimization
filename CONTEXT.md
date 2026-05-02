# LB2 MKP — Contexto del Proyecto

> **Última actualización:** 2026-05-02
> **Estado:** Framework `lb2/` implementado — Core, PSO, Monitoring, Strategies, Engine ✅

---

## ¿Qué es este proyecto?

Un **framework extensible de metaheurísticas** para resolver el **Multidimensional Knapsack Problem (MKP)** con detección automática de estancamiento basada en **DTW (Dynamic Time Warping)** y autoconfiguración de parámetros.

### Origen

El proyecto nace de un notebook Jupyter (`Advance_of_LB2_para_MKP (1).ipynb`) que implementaba PSO binario con el framework de binarización LB2 y 8 variantes de respuesta al estancamiento. Ese notebook tiene ~15,000 líneas y fue refactorizado en un paquete Python modular (`lb2/`).

---

## Conceptos Clave

### MKP (Multidimensional Knapsack Problem)
Problema de optimización combinatoria: dados `n` items con valores y `m` mochilas con restricciones de capacidad, maximizar el valor total sin exceder ninguna capacidad.

### PSO (Particle Swarm Optimization)
Metaheurística poblacional donde partículas buscan en el espacio de soluciones guiadas por su mejor experiencia personal y la mejor del grupo. Actualiza velocidad y posición en cada iteración.

### LB2 (Framework de Binarización)
Convierte el PSO continuo en binario usando **dos funciones de transferencia complementarias** (L1 y L2) que generan dos candidatos por iteración. Parámetros G1, G2, G3 evolucionan linealmente durante la ejecución.

### DTW (Dynamic Time Warping)
Mide similaridad entre series temporales "estirándolas" para alinearlas. En este proyecto se usa para comparar la curva de convergencia contra baselines (rampa = progreso ideal, constante = estancamiento total) y detectar cuándo el algoritmo se estancó.

### StagnationMonitor
Componente que evalúa el historial de mejores valores usando DTW. Cuando la curva se parece más a una constante que a una rampa durante suficientes iteraciones, dispara `fire=True` → activa la estrategia de respuesta.

---

## Arquitectura Implementada

```
LB2_mkp/
├── lb2/                          # Paquete principal (21 archivos)
│   ├── __init__.py               # v0.1.0
│   ├── core/                     # Problem, Solution, repair()
│   │   ├── problem.py            # MKPInstance dataclass
│   │   ├── solution.py           # Solution dataclass
│   │   └── repair.py             # repair_solution() — BUGFIX incluido
│   ├── metaheuristics/           # Metaheuristic ABC → BinaryPSO
│   │   ├── base.py               # ABC con set_params() e inject_solution()
│   │   └── pso.py                # BinaryPSO con LB2 binarization
│   ├── monitoring/               # StagnationMonitor (DTW) + ParameterController
│   │   ├── dtw.py                # StagnationMonitor, StagnationConfig
│   │   └── controller.py         # ParameterController → HOLD/EXPLORE/EXPLOIT/INTERVENE
│   ├── strategies/               # StagnationStrategy ABC + 4 implementaciones
│   │   ├── base.py               # ABC con apply()
│   │   ├── intensification.py    # V1: 1-flip y 2-flip local search
│   │   ├── ruin_recreate.py      # V8: destruye + reconstruye greedy (MEJOR)
│   │   ├── tabu.py               # V7: búsqueda tabú
│   │   └── lp_relaxation.py      # V6: relajación LP + fallback greedy
│   ├── instances/                # Carga de instancias MKP
│   │   └── orlib.py              # Parser OR-Library Chu & Beasley
│   └── engine/                   # Orquestador
│       └── optimizer.py          # OptimizationEngine, RunConfig, RunResult
├── notebooks/
│   └── benchmark.ipynb           # (PENDIENTE) Notebook para experimentación
├── tests/                        # (PENDIENTE) Tests unitarios
├── CONTEXT.md                    # ← Este archivo
└── Advance_of_LB2_para_MKP (1).ipynb  # Notebook original (NO TOCAR, referencia)
```

### Interfaces Principales

```python
# Cualquier metaheurística implementa esto:
class Metaheuristic(ABC):
    def initialize(problem, seed=None) → None
    def step(iteration, total_iterations) → float   # Una iteración, retorna best fitness
    def get_best() → Solution
    def get_params() → dict
    def set_params(params) → None                    # Para autoconfiguración
    def inject_solution(solution, fraction) → None   # Para inyección desde strategies

# Cualquier estrategia de respuesta implementa esto:
class StagnationStrategy(ABC):
    def apply(best, problem) → Solution
```

### Estado de Implementación

| Componente | Estado | Notas |
|---|---|---|
| Core (Problem, Solution, Repair) | ✅ Implementado | Bug de repair corregido |
| StagnationMonitor (DTW) | ✅ Implementado | Extraído del notebook |
| ParameterController | ✅ Implementado | Absorbe V2-V4 |
| BinaryPSO + LB2 | ✅ Implementado | Extraído del notebook |
| IntensificationStrategy (V1) | ✅ Implementado | 1-flip + 2-flip |
| RuinRecreateStrategy (V8) | ✅ Implementado | Mejor rendimiento |
| TabuSearchStrategy (V7) | ✅ Implementado | Lista tabú |
| LPRelaxationStrategy (V6) | ✅ Implementado | scipy + greedy fallback |
| OptimizationEngine | ✅ Implementado | Multi-epoch + seed management |
| Grey Wolf Optimizer (GWO) | 🔲 Futuro | Nueva metaheurística |
| Whale Optimization Algorithm (WOA) | 🔲 Futuro | Nueva metaheurística |
| Benchmark Notebook | 🔲 Pendiente | Validación vs baselines |
| Tests unitarios | 🔲 Pendiente | — |

### Versiones DESCARTADAS del notebook original

V2 (Ajuste Cíclico), V3 (Exploración adaptativa), V4 (Ajuste dinámico no lineal) — solo ajustan parámetros del PSO sin búsqueda local. Mejora marginal (~185 pts). Su funcionalidad se absorbió en el `ParameterController`.

---

## Decisiones de Diseño

1. **Strategy Pattern**: Las respuestas al estancamiento son intercambiables. Se pueden combinar, secuenciar o elegir dinámicamente.

2. **ParameterController**: Interpreta señales DTW y decide: HOLD (normal), EXPLORE (más dispersión), EXPLOIT (más convergencia), INTERVENE (activar strategy).

3. **inject_solution()**: Las strategies que mejoran la solución la inyectan al enjambre. Puente entre búsqueda local y metaheurística poblacional.

4. **Notebook original se PRESERVA**: No se toca. Queda como referencia histórica.

5. **Reproducibilidad**: Semillas de random obligatorias. Se incrementan por epoch.

---

## Bugs Corregidos

1. **✅ CORREGIDO — `reparar_solucion`** (era 🔴 CRÍTICO): En el notebook original, ambas ramas del if/else hacían `solucion = aux`. Ahora la fase DROP correctamente: remueve items no factibles (continúa), y cuando logra factibilidad acepta y TERMINA. Archivo: `lb2/core/repair.py`.

2. **✅ CORREGIDO — Variable global `indices_ascendentes`**: Ahora `density_order` es un atributo de `MKPInstance`, precomputado en `__post_init__`.

## Bugs Pendientes

1. **🔴 `valor_optimo` siempre `0.0`**: Las instancias `mknapcb` no traen el óptimo embebido. Hay que buscarlo en archivos separados (el parser ahora lee el campo pero depende del formato del archivo).

---

## Resultados de Referencia (del notebook original)

Instancia: `mknapcb1`, índice 9, 10 epochs × 100 iteraciones, 20 partículas

| Versión | Media | Desviación |
|---|---|---|
| Original (sin respuesta) | 22,693 | — |
| V1 (Intensificación) | 22,973 | — |
| V5 (Heurística) | 23,083 | 222 |
| V7 (Tabú) | 23,500 | 285 |
| V6 (LP Relax) | 23,572 | 256 |
| **V8 (Ruin & Recreate)** | **23,805** | **225** |

Estos valores sirven como **baseline** para validar que el refactor no pierde calidad.

---

## Dependencias

- `numpy` — operaciones vectoriales
- `matplotlib` — visualización
- `scipy` — `linprog` para relajación LP (usado en LPRelaxationStrategy)
- `requests` — descarga de instancias de OR-Library

---

## Uso Rápido

```python
from lb2.instances import load_mkp_instances
from lb2.metaheuristics import BinaryPSO
from lb2.strategies import RuinRecreateStrategy
from lb2.engine import OptimizationEngine, RunConfig
from lb2.monitoring import StagnationConfig

# Cargar instancias
instances = load_mkp_instances("mknapcb1")
problem = instances[9]  # Instancia de referencia

# Configurar engine
engine = OptimizationEngine(
    metaheuristic=BinaryPSO(num_particles=20),
    strategies=[RuinRecreateStrategy(ruin_rate=0.3)],
)

# Ejecutar
result = engine.run(
    problem,
    RunConfig(
        epochs=10,
        iterations_per_epoch=100,
        seed=42,
    ),
)

print(f"Best: {result.best_fitness}")
```

---

## Próximos Pasos

1. **Notebook de benchmarks** (`notebooks/benchmark.ipynb`) para validar resultados vs baselines
2. **Tests unitarios** en `tests/`
3. **GWO y WOA** como nuevas implementaciones de `Metaheuristic`
4. **Mejorar ParameterController** con adaptación más granular
5. **Parser de archivos .opt** para valores óptimos de OR-Library

---

## Para el Agente de IA

Si estás leyendo esto como contexto para continuar el trabajo:

1. **Lee este archivo** y busca en engram: `architecture/lb2-framework` en proyecto `lb2_mkp`
2. **No toques** el notebook original (`Advance_of_LB2_para_MKP (1).ipynb`)
3. **El código nuevo va en `lb2/`** — estructura de paquete Python
4. **Las interfaces base** (`Metaheuristic`, `StagnationStrategy`) son el contrato que NO debe cambiar sin consultar al usuario
5. **Validá contra los baselines** de la tabla de resultados
6. **El usuario habla en español rioplatense** — respondé en español si te escribe en español
