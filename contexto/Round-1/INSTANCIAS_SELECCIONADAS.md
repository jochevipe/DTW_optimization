# Selección de instancias — Campaña de revisión (Round 1)

Responde a **R1.3**: el paper evaluó solo el primer problema (idx=0) de cada grupo Chu–Beasley.
La campaña de re-experimentos extiende la evaluación a **3 instancias fijas por archivo**:
**27 instancias en total** (9 archivos × 3 índices).

## Criterio de selección

1. **idx=0 siempre incluido**: conserva comparabilidad directa con todos los resultados
   ya reportados en el paper (todas las tablas actuales usan idx=0).
2. Los **k−1 índices restantes** se muestrean sin reposición del rango [1, 29] con
   `numpy.random.default_rng(seed_base + nº_archivo)`, donde `seed_base = 1000`.
   La semilla es pública y la tabla queda fija: cualquier persona puede reproducirla
   exactamente con `python run_benchmark_hpc.py --k 3 --sample-seed 1000`.
3. La grilla (m × n) ya está balanceada a nivel archivo: cada `mknapcb{i}.txt` contiene
   30 instancias de un único par (m, n) — m∈{5,10,30}, n∈{100,250,500} —, así que
   muestrear 3 índices por archivo conserva el balance por tamaño.

## Tabla oficial de índices

| Archivo | m × n | Índices seleccionados |
|---|---|---|
| mknapcb1 | 5 × 100  | 0, 18, 26 |
| mknapcb2 | 5 × 250  | 0, 12, 17 |
| mknapcb3 | 5 × 500  | 0, 6, 9 |
| mknapcb4 | 10 × 100 | 0, 1, 21 |
| mknapcb5 | 10 × 250 | 0, 3, 13 |
| mknapcb6 | 10 × 500 | 0, 10, 15 |
| mknapcb7 | 30 × 100 | 0, 2, 3 |
| mknapcb8 | 30 × 250 | 0, 5, 10 |
| mknapcb9 | 30 × 500 | 0, 2, 21 |

Total: **27 instancias** (9 archivos × 3 índices).

## Comandos de ejecución (HPC Oceano PUCV)

Campaña completa con los parámetros del paper (31 epochs × 2000 iteraciones, 40 CPUs por instancia):

```bash
python run_benchmark_hpc.py --k 3 --sample-seed 1000 --cpus 40 --epochs 31
```

Modos alternativos:

```bash
# Lista explícita de índices aplicada a todos los archivos
python run_benchmark_hpc.py --indices 0 5 10 --cpus 40

# Solo algunos archivos (misma semilla → misma tabla para esos archivos)
python run_benchmark_hpc.py --desde 1 --hasta 3 --k 3 --cpus 40

# Muestreo puro sin forzar idx=0
python run_benchmark_hpc.py --k 3 --no-include-zero --cpus 40
```

## Trazabilidad

- Cada ejecución multi-índice guarda el manifiesto de selección en
  `results/campaign_<id>/instance_selection.json` (semilla, k, tabla y total).
- Los resultados se guardan por instancia e índice en la estructura existente:
  `results/<estrategia>/todos/mknapcb{i}_{idx}/comparacion_mhs_<run_id>/`,
  y el análisis estadístico (`analisis.estadistico.py`) se ejecuta automáticamente
  por cada (archivo, índice).
