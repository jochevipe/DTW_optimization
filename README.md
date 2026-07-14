# DTW Optimization — MKP

Comparación de adaptaciones DTW (Dynamic Time Warping) para la optimización del **Multidimensional Knapsack Problem (MKP)** usando metaheurísticas binarias.

## Estructura del proyecto

```text
DTW_optimization/
├── mkp_common/          # Código compartido: problemas, MHs, runner, estadísticas
│   ├── mh/              # Metaheurísticas: BinaryPSO, GA, BinaryGWO, BinaryDE
│   ├── config.py        # Configuración central (población, iteraciones, epochs)
│   ├── problem.py       # Carga de instancias OR-Library + reparación greedy
│   ├── runner.py        # Loop genérico de experimento con DTW
│   ├── stats.py         # Wilcoxon + Holm-Bonferroni + tablas
│   └── results.py       # Guardado/carga de resultados JSON
├── vanilla/               # Línea base sin DTW (exploit por defecto)
├── vanilla_explotacion/   # Variante: MHs forzadas a modo exploit puro
├── vanilla_exploracion/   # Variante: MHs forzadas a modo explore puro
├── fire_binario/          # Estrategia A4: fire binario con 3 condiciones
├── fire_d2/             # Estrategia A3: decisión pura por D2
├── sigmoid_delta/       # Estrategia B1: intensidad continua con sigmoide
├── b3_d2/               # Estrategia B3: intensidad continua directa de D2
├── analisis/            # Análisis estadístico y boxplots
├── run_all.py           # Ejecución secuencial de todas las estrategias
├── run_all_hpc.py       # Ejecución paralela para HPC/SLURM
└── run_dtw.sh           # Script de envío a SLURM
```

## Requisitos

```bash
pip install numpy scipy matplotlib tqdm
```

> En el HPC Océano se usa un entorno Conda llamado `DTW_optimization`.

## Configuración central

Edita `mkp_common/config.py` para cambiar la instancia, población, iteraciones y epochs:

```python
RUTA_INSTANCIA = "instances/mknapcb4.txt"   # instancia por defecto
INDICE_INSTANCIA = 0                         # índice dentro del archivo
NUM_PARTICULAS = 20
NUM_ITERACIONES = 200
EPOCHS = 20
```

También puedes sobreescribirlo por variable de entorno antes de ejecutar:

```bash
export MKP_INSTANCIA=instances/mknapcb1.txt
export MKP_INDICE=2
```

## Comandos básicos

### 1. Ejecutar una sola estrategia

```bash
# Líneas base vanilla (sin DTW)
python -m vanilla.resultados
python -m vanilla_explotacion.resultados
python -m vanilla_exploracion.resultados

# Estrategias DTW
python -m fire_binario.resultados
python -m fire_d2.resultados
python -m sigmoid_delta.resultados
python -m b3_d2.resultados
```

Cada comando guarda resultados en `results/{strategy}/todos/{instancia}_{indice}/comparacion_mhs_{timestamp}/`.

### 2. Ejecutar todas las estrategias secuencialmente

```bash
python run_all.py
python run_all.py --instancia instances/mknapcb1.txt
python run_all.py --instancia instances/mknapcb1.txt --indice 2
```

### 3. Ejecutar en HPC con paralelismo total (estrategia × MH × epoch)

```bash
python run_all_hpc.py
python run_all_hpc.py --instancia instances/mknapcb1.txt --indice 0
python run_all_hpc.py --cpus 40 --epochs 30
```

### 4. Enviar a SLURM (HPC Océano)

```bash
sbatch run_dtw.sh
```

Ejemplo de `run_dtw.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=dtw_mkp
#SBATCH --partition=CPU
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH --time=24:00:00
#SBATCH --output=dtw_%j.out

source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate DTW_optimization

cd /work/jose.villamayor/DTW_optimization
python run_all_hpc.py --cpus $SLURM_CPUS_PER_TASK
```

## Análisis estadístico

Una vez generados los resultados, compara todas las versiones contra Vanilla con Wilcoxon + Holm-Bonferroni:

```bash
# Usa los resultados más recientes de cualquier instancia
python -m analisis.estadistico

# Filtra por instancia específica
python -m analisis.estadistico --instancia instances/mknapcb4.txt
python -m analisis.estadistico --instancia instances/mknapcb4.txt --indice 0

# Test one-sided: versión > vanilla
python -m analisis.estadistico --one-sided
```

Salidas en `results/estadistico/{instancia}_{indice}/`:

- `tabla_estadistica_{timestamp}.txt`
- `tabla_matematica_{timestamp}.txt`
- `comparacion_{timestamp}.png`  ← boxplot con línea verde punteada del óptimo conocido

## Estructura de resultados

```text
results/
├── vanilla/
│   └── todos/
│       └── mknapcb4_0/
│           └── comparacion_mhs_20250710_120000/
│               ├── PSO_mknapcb4_0.json
│               ├── GA_mknapcb4_0.json
│               ├── GWO_mknapcb4_0.json
│               ├── DE_mknapcb4_0.json
│               └── vanilla_mknapcb4_0.png
├── fire_binario/
├── fire_d2/
├── sigmoid_delta/
├── b3_d2/
└── estadistico/
    └── mknapcb4_0/
        ├── tabla_estadistica_*.txt
        ├── tabla_matematica_*.txt
        └── comparacion_*.png
```

Cada JSON contiene:

- `fitness`: lista de fitness por epoch
- `fire_counts`: cantidad de fires DTW por epoch
- `tiempos`: tiempo de ejecución por epoch
- `optimo_conocido`: valor óptimo teórico de la instancia
- `stats`: mejor, promedio, peor, std y gap al óptimo
- `info`: metadatos del experimento

## Notas de uso

- El análisis estadístico empareja resultados por **semilla/epoch** (mismo orden), por lo que todos los experimentos deben usar el mismo número de epochs.
- La línea horizontal verde en el boxplot representa el **óptimo conocido** de la instancia.
- Si una metaheurística repite exactamente el mismo fitness en muchas epochs (por ejemplo GA + `fire_binario` en instancias difíciles), eso indica **convergencia prematura**: la población perdió diversidad y el operador de reparación determinístico `reparar()` no genera suficiente variación. Esto no es un bug del código, sino un comportamiento conocido del GA binario con reparación greedy sobre MKP. Para mitigarlo se puede aumentar `NUM_PARTICULAS`, aumentar la tasa de mutación en modo explore, o probar una inicialización más diversa.
