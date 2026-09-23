# Selección de instancias — Campaña de revisión (Round 1)

Responde a **R1.3**: el paper evaluó solo el primer problema (idx=0) de cada grupo Chu–Beasley.
La campaña de re-experimentos extiende la evaluación a **3 instancias fijas por archivo**:
**27 instancias en total** (9 archivos × 3 índices).

## Criterio de selección

**Muestreo sistemático**: `idx ∈ {0, 15, 29}` — la primera, la media y la última instancia
de cada archivo.

Justificación:

1. Cada archivo `mknapcb{i}.txt` contiene 30 instancias independientes del mismo par (m, n)
   generadas con el mismo procedimiento de Chu & Beasley (1998). Ningún índice tiene un
   valor particular: no hay estructura por bloques ni drift conocido dentro del archivo.
2. Los índices fijos 0/15/29 cubren todo el rango del archivo con una regla trivial de
   explicar y reproducir ("first, middle and last instance of each benchmark file"),
   sin depender de semillas de muestreo.
3. **idx=0 se conserva** por comparabilidad directa con todos los resultados ya reportados
   en el paper (todas las tablas actuales usan idx=0).
4. La grilla (m × n) ya está balanceada a nivel archivo: cada `mknapcb{i}.txt` es un único
   par (m, n) — m∈{5,10,30}, n∈{100,250,500} —, así que 3 índices por archivo conservan
   el balance por tamaño.

## Tabla oficial de índices

| Archivo | m × n | Índices seleccionados |
|---|---|---|
| mknapcb1 | 5 × 100  | 0, 15, 29 |
| mknapcb2 | 5 × 250  | 0, 15, 29 |
| mknapcb3 | 5 × 500  | 0, 15, 29 |
| mknapcb4 | 10 × 100 | 0, 15, 29 |
| mknapcb5 | 10 × 250 | 0, 15, 29 |
| mknapcb6 | 10 × 500 | 0, 15, 29 |
| mknapcb7 | 30 × 100 | 0, 15, 29 |
| mknapcb8 | 30 × 250 | 0, 15, 29 |
| mknapcb9 | 30 × 500 | 0, 15, 29 |

Total: **27 instancias** (9 archivos × 3 índices).

## Comandos de ejecución (HPC Oceano PUCV)

Campaña completa con los parámetros del paper (31 epochs × 2000 iteraciones, 40 CPUs por instancia):

```bash
python run_benchmark_hpc.py --indices 0 15 29 --cpus 40 --epochs 31
```

Modos alternativos:

```bash
# Solo algunos archivos
python run_benchmark_hpc.py --desde 1 --hasta 3 --indices 0 15 29 --cpus 40

# Muestreo aleatorio con semilla (alternativa documentada, no la oficial)
python run_benchmark_hpc.py --k 3 --sample-seed 1000 --cpus 40

# Índice único (comportamiento legacy)
python run_benchmark_hpc.py --indice 0 --cpus 40
```

## Trazabilidad

- Cada ejecución multi-índice guarda el manifiesto de selección en
  `results/campaign_<id>/instance_selection.json` (modo, k, semilla, tabla y total).
- Los resultados se guardan por instancia e índice en la estructura existente:
  `results/<estrategia>/todos/mknapcb{i}_{idx}/comparacion_mhs_<run_id>/`,
  y el análisis estadístico (`analisis.estadistico.py`) se ejecuta automáticamente
  por cada (archivo, índice).
