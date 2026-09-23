# Controladores DDTW para el problema de la mochila multidimensional

Este repositorio estudia el cambio adaptativo entre exploración y explotación en cuatro
metaheurísticas binarias (PSO, GA, GWO y DE) para el *Multidimensional Knapsack Problem*
(MKP). Un monitor DDTW observa las trayectorias de mejor fitness acumulado y alimenta tres
controladores de cambio de modo. Los experimentos usan las instancias Chu–Beasley de
`instances/mknapcb{1..9}.txt` y respaldan un artículo en revisión; las observaciones de la
primera ronda están en [`contexto/Round-1/`](contexto/Round-1/).

> **Estado: campaña nueva post-OAT.** Se eliminaron deliberadamente los resultados de
> campañas anteriores (1456 archivos; recuperables desde el historial de git, commit
> `fe12f2f`). `results/` es la ruta activa de salida y se crea al ejecutar; no hay resultados
> históricos que reutilizar allí. El catálogo de campañas anteriores se incorpora en
> [`contexto/historico/campanas_previas.md`](contexto/historico/campanas_previas.md) durante
> esta limpieza. Los [hallazgos OAT](contexto/Round-1/HALLAZGOS_OAT.md) son la base para
> definir los parámetros de la próxima campaña, no evidencia de que una configuración sea
> óptima en todas las instancias.

## Estrategias registradas

| Clave / nombre | Papel | Regla de cambio de modo |
|---|---|---|
| `binary_simple` / Binary-Simple | Controlador estudiado | Dispara exploración cuando `D2 ≤ θc` (distancia a la trayectoria constante por debajo del umbral). |
| `binary_patient` / Binary-Patient | Controlador estudiado | Entra en exploración tras `patience` disparos consecutivos de `D2 ≤ θc`; vuelve a explotación al detectar una mejora. |
| `binary_complex` / Binary-Complex | Controlador estudiado | Entra en exploración con el disparo A4 sostenido (meseta, D2 y rampa/delta); vuelve a explotación con una mejora. |
| `vanilla_exploracion` / Vanilla-Exploration | Baseline | Permanece en exploración; no cambia de modo por DDTW. |
| `vanilla_explotacion` / Vanilla-Exploitation | Baseline | Permanece en explotación; no cambia de modo por DDTW. |

Son las cinco entradas de `run_all.py` y `run_all_hpc.py`. `vanilla/` es el paquete de ejecución compartido que reutilizan las variantes vanilla; **no** es una sexta estrategia registrada.

## Parámetros y precondición experimental

Valores **actuales del código** en [`mkp_common/config.py`](mkp_common/config.py), frente a los usados en el artículo:

| Parámetro | Código actual | Artículo |
|---|---:|---:|
| Iteraciones (`T`) | 2000 | 2000 |
| Épocas / semillas (`R`, 1..31) | 31 | 31 |
| Población | 20 | 20 |
| Ventana (`W`) | 100 | 200 |
| Banda Sakoe–Chiba | 2 | 2 |
| Pendiente mínima (`min_slope`) | 2.0 | 2.0 |
| DDTW | Activado | Activado |
| Umbrales adaptativos | Activados | Activados |
| Percentil bajo (`p_low`) | 20 | 40 |
| Percentil alto (`p_high`) | 80 | 60 |
| Meseta máxima (`plateau_max`) | 5 | 5 |
| Paciencia (`patience`) | 3 | 3 |

**Antes de lanzar una campaña:** acordar los valores definitivos post-OAT a partir de
[`HALLAZGOS_OAT.md`](contexto/Round-1/HALLAZGOS_OAT.md), fijarlos en `mkp_common/config.py`
y registrar esa configuración con los resultados. No hay aquí una selección definitiva
inventada: el OAT varió seis parámetros de uno en uno alrededor de la configuración del
artículo, en 19 configuraciones por controlador (`binary_simple` y `binary_complex`), con
`mknapcb1[0,15,29]` y 31 épocas. La configuración del artículo no fue superior en todos los
casos; en Binary-Complex, por ejemplo, paciencia 1 dio Δ=−3.970 y paciencia 5, Δ=+2.038
frente a la base (descriptivo, no prueba de significancia).

## Protocolo oficial de instancias

La campaña de ampliación usa muestreo con semilla: **tres índices por cada uno de los nueve archivos**, 27 instancias en total. Incluye el índice 0 y muestrea los otros dos sin reposición. La [tabla oficial de índices](odd/tasks/frente2-multi-instancia.md) fija la selección (0/15/29 fue un protocolo anterior, no el vigente).

```bash
# Desde la raíz del repositorio; lista predeterminada completa mknapcb1..9.
python run_benchmark_hpc.py --k 3 --sample-seed 1000 --cpus 40 --epochs 31

# Equivalente con la lista explícita de los nueve archivos, en el mismo orden.
python run_benchmark_hpc.py --instancias instances/mknapcb1.txt instances/mknapcb2.txt instances/mknapcb3.txt instances/mknapcb4.txt instances/mknapcb5.txt instances/mknapcb6.txt instances/mknapcb7.txt instances/mknapcb8.txt instances/mknapcb9.txt --k 3 --sample-seed 1000 --cpus 40 --epochs 31
```

`--sample-seed` **no activa** el muestreo por sí solo: se necesita `--k` (o bien `--indices`
para una selección explícita). Sin `--k` ni `--indices`, el driver usa un único `--indice 0`
por archivo. La semilla de cada archivo es `sample-seed + posición en la lista seleccionada`
(desde 1): para reproducir la tabla oficial hay que usar la lista completa de `mknapcb1` a
`mknapcb9` en ese orden; ejecutar solo un subconjunto cambia los índices muestreados. La
selección queda registrada en `results/campaign_<id>/instance_selection.json`.

## Ejecución y análisis

Las invocaciones siguientes presuponen parámetros fijados y entorno Python con las dependencias del proyecto. No envíes la campaña SLURM predeterminada como sustituto del comando oficial de 27 instancias.

```bash
# Una instancia, cinco estrategias en secuencia (flags: --instancia, --indice).
python run_all.py --instancia instances/mknapcb1.txt --indice 0

# Una instancia, ejecución paralela (también: --cpus, --epochs, --skip).
python run_all_hpc.py --instancia instances/mknapcb1.txt --indice 0 --cpus 40 --epochs 31

# Driver de campaña: archivos secuenciales; paralelismo dentro de cada instancia.
python run_benchmark_hpc.py --k 3 --sample-seed 1000 --cpus 40 --epochs 31
```

`run_benchmark_hpc.py` admite `--instancias` o `--desde`/`--hasta` para elegir archivos;
`--indice`, `--indices` o `--k` para elegir índices; `--sample-seed`,
`--include-zero`/`--no-include-zero`, `--cpus`, `--epochs`, `--skip` y `--stop-on-error`.
`run_all_hpc.py` admite `--instancia`, `--indice`, `--cpus`, `--epochs` y `--skip`;
`run_all.py`, solo `--instancia` y `--indice`.

```bash
# SLURM: solo análisis estadístico de mknapcb1[0], 10 CPU; requiere resultados previos.
sbatch run_dtw.sh

# SLURM: campaña de 40 CPU; predeterminado: nueve archivos, solo índice 0.
sbatch run_dtw1.sh

# Análisis local tras generar las cinco estrategias y las cuatro MH.
python -m analisis.estadistico --instancia instances/mknapcb1.txt --indice 0
# Opcional: --one-sided (versión > baseline); por defecto, bilateral.
```

Para la campaña oficial de 27 instancias, enviá al planificador un job que invoque el comando de `run_benchmark_hpc.py` **con `--k 3 --sample-seed 1000`**; `run_dtw1.sh` sin cambios no lo hace.

## Salidas y estadística

`results/` es salida generada, no un archivo de evidencia histórica. El driver crea además el manifiesto de selección de cada campaña. Por estrategia y par archivo/índice se guardan los JSON de las cuatro MH y gráficos PNG/PDF del lote; el análisis crea tablas y gráficos separados:

```text
results/
├── campaign_<id>/instance_selection.json
├── <strategy>/todos/<instance_stem>_<index>/comparacion_mhs_<timestamp>/
│   ├── <MH>_<instance_stem>_<index>.json
│   └── ... gráficos PNG/PDF del lote
└── estadistico/<instance_stem>_<index>/comparacion_<timestamp>/
    ├── tabla_estadistica.txt
    ├── tabla_matematica.txt
    ├── tabla_tiempos.txt
    ├── comparacion.pdf
    └── comparacion.png
```

`analisis/estadistico.py` y `mkp_common/stats.py` comparan cada estrategia con
**Vanilla-Exploration**, emparejando las épocas/semillas y exigiendo las cuatro MH (PSO, GA,
GWO, DE) con presupuestos coincidentes. Aplican Wilcoxon de rangos con signo pareado
(`zero_method="zsplit"`), bilateral por defecto con α=0.05 (opción unilateral `--one-sided`),
y Shapiro–Wilk sobre las diferencias pareadas. **No aplican corrección por comparaciones
múltiples.** La prueba de suma de rangos mencionada en
[`contexto/especificacion_extraccion_datos.md`](contexto/especificacion_extraccion_datos.md)
es una especificación futura, no parte del análisis implementado.

## Mapa del repositorio

```text
mkp_common/              Configuración, monitor DDTW, MH, runner y estadística compartidos
binary_simple/            Controlador D2 (A3)
binary_patient/           Controlador D2 con paciencia (A10)
binary_complex/           Controlador A4 sostenido con histéresis asimétrica
vanilla/                  Runner compartido de las dos variantes vanilla
vanilla_exploracion/      Baseline de exploración
vanilla_explotacion/      Baseline de explotación
instances/                Archivos Chu–Beasley mknapcb1..9
analisis/                 Comparación estadística y figuras
contexto/                 Teoría, revisión Round-1, OAT y archivo histórico
odd/tasks/                Decisiones y seguimiento de tareas experimentales
results/                  Salida generada de la nueva campaña (puede no existir aún)
run_all.py                 Ejecución local de una instancia
run_all_hpc.py             Ejecución paralela de una instancia
run_benchmark_hpc.py       Orquestación secuencial de archivos e índices
run_dtw.sh, run_dtw1.sh    Jobs SLURM de análisis y campaña, respectivamente
```

Consultá el [índice de contexto](contexto/README.md) para distinguir teoría, estado actual y material histórico, y [`odd/tasks/`](odd/tasks/) para el protocolo y las decisiones de campaña.
