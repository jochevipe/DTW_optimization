#!/bin/bash
#SBATCH --job-name=dtw_pt2         # Nombre en la cola (Trabajo 2/3)
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=40           # 40 CPUs para paralelismo masivo
#SBATCH --mem=32G                   # 32 GB de RAM del sistema
#SBATCH --output=./logs/dtw_p2_%j.log # Archivo de log (%j es el ID del trabajo)
#SBATCH --error=./errors/dtw_p2_%j.error # Archivo de errores si falla
#SBATCH --qos=normal                # QOS de HPC

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

# 1. Cargar el entorno (OBLIGATORIO)
source $HOME/miniconda3/etc/profile.d/conda.sh

echo "=========================================================="
echo "Iniciando Trabajo 2/3: Problemas mknapcb4 a mknapcb6 (m=10)"
echo "Nodo: $SLURMD_NODENAME | CPUs: ${SLURM_CPUS_PER_TASK:-40}"
echo "=========================================================="

# 2. Activar entorno virtual
conda activate DTW_optimization

# 3. Determinar CPUs disponibles (SLURM o fallback)
CPUS=${SLURM_CPUS_PER_TASK:-40}

# 4. Ejecutar instancias 0, 15 y 29 de los problemas 4 a 6 (9 instancias en total)
python run_benchmark_hpc.py --desde 4 --hasta 6 --indices 0 15 29 --cpus $CPUS --epochs 31

echo "<<Trabajo 2 terminado exitosamente>>"
