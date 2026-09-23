# Selección de instancias — Campaña de revisión (Round 1)

Responde a **R1.3**: el paper evaluó solo la primera instancia (idx=0) de cada archivo Chu–Beasley. La nueva campaña post-OAT amplía la evaluación a **27 instancias** (9 archivos × 3 índices).

## Criterio de selección oficial

Cada `instances/mknapcb{i}.txt` contiene 30 instancias (idx 0..29). Se conserva idx=0 por comparabilidad con el paper y se muestrean otros 2 índices sin reposición de [1,29]. Para cada archivo `i` de 1 a 9, la tabla se obtuvo con `numpy.random.default_rng(1000 + i)`, `k=3` y `seed_base=1000`. Así se mantiene la grilla de tamaños m∈{5,10,30} × n∈{100,250,500} con tres instancias por par (m, n).

| Archivo | m × n (restricciones × ítems) | Índices seleccionados |
|---|---|---|
| mknapcb1 | 5 × 100 | 0, 18, 26 |
| mknapcb2 | 5 × 250 | 0, 12, 17 |
| mknapcb3 | 5 × 500 | 0, 6, 9 |
| mknapcb4 | 10 × 100 | 0, 1, 21 |
| mknapcb5 | 10 × 250 | 0, 3, 13 |
| mknapcb6 | 10 × 500 | 0, 10, 15 |
| mknapcb7 | 30 × 100 | 0, 2, 3 |
| mknapcb8 | 30 × 250 | 0, 5, 10 |
| mknapcb9 | 30 × 500 | 0, 2, 21 |

**Total: 27 instancias.**

## Ejecución y reproducción (HPC Oceano PUCV)

Campaña completa con 31 epochs y 40 CPUs:

```bash
python run_benchmark_hpc.py --desde 1 --hasta 9 --k 3 --sample-seed 1000 --cpus 40 --epochs 31
```

`--k` es obligatorio para activar el muestreo: `--sample-seed` por sí solo no lo activa. La selección tiene precedencia `--indices` → `--k` → `--indice` (por defecto 0); no combinar `--indices` con este comando si se busca reproducir la tabla. En la CLI, la semilla de cada archivo se deriva de `seed_base + posición en la lista de archivos seleccionados`, **no** del número `i` del nombre. La fórmula `1000 + i` de la tabla coincide al ejecutar la lista completa y ordenada de archivos 1..9; un rango parcial no reproduce estos índices para esos mismos archivos.

## Trazabilidad

- Manifiesto de selección por campaña: `results/campaign_<id>/instance_selection.json` (modo, k, semilla, tabla y total).
- Resultados: `results/<strategy>/todos/<instance_stem>_<index>/comparacion_mhs_<timestamp>/`; el análisis estadístico se ejecuta automáticamente por par (archivo, índice).
- Particularidad conocida: cada proceso hijo HPC reemplaza el identificador de campaña por su propio timestamp. No asumir que el nombre de su directorio de resultados coincide con `<id>` del manifiesto.

## Protocolo histórico

La selección fija **0/15/29** se utilizó en las campañas de sensibilidad OAT (ver [Hallazgos OAT](HALLAZGOS_OAT.md)) y en los planes anteriores. Por decisión del usuario del **2026-09-23**, queda reemplazada por el muestreo con semilla de la tabla anterior para la nueva campaña post-OAT; sus resultados históricos no se eliminan ni se reinterpretan como muestreados.
