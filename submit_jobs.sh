#!/bin/bash
# ==============================================================================
# submit_jobs.sh — Envío simultáneo de los 3 trabajos al cluster SLURM
# ==============================================================================
# Cada trabajo procesa 3 problemas con 3 instancias cada uno (9 instancias c/u)
# Total en paralelo: 27 instancias sobre 3 nodos de 40 CPUs.
# ==============================================================================

echo "=========================================================="
echo "Encolando 3 trabajos paralelos en SLURM (3 problemas c/u)"
echo "=========================================================="

echo "-> Enviando Trabajo 1 (mknapcb1..3, m=5)..."
sbatch run_dtw1.sh

echo "-> Enviando Trabajo 2 (mknapcb4..6, m=10)..."
sbatch run_dtw2.sh

echo "-> Enviando Trabajo 3 (mknapcb7..9, m=30)..."
sbatch run_dtw3.sh

echo "=========================================================="
echo "¡Los 3 trabajos fueron enviados exitosamente!"
echo "Consulta la cola con: squeue -u \$USER"
echo "=========================================================="
