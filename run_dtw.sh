#!/bin/bash
#SBATCH --job-name=dtw_array        # Nombre que verás en la cola
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=40          # 40 CPUs por trabajo
#SBATCH --mem=32G                  # 32 GB de RAM por trabajo
#SBATCH --output=./logs/dtw_array_%A_%a.log # %A: ID maestro, %a: índice (1, 2, 3)
#SBATCH --error=./errors/dtw_array_%A_%a.error
#SBATCH --qos=normal               # QOS de HPC
#SBATCH --array=1-3%3              # 3 trabajos en paralelo simultáneo (3 problemas cada uno)

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

# 1. Cargar el entorno (OBLIGATORIO)
source $HOME/miniconda3/etc/profile.d/conda.sh

# 2. Activar entorno virtual
conda activate DTW_optimization

# 3. Determinar CPUs disponibles (SLURM o fallback)
CPUS=${SLURM_CPUS_PER_TASK:-40}

# 4. Asignar rango de problemas según la tarea (1, 2 o 3)
TASK_ID=${SLURM_ARRAY_TASK_ID:-${1:-1}}

case $TASK_ID in
    1)
        DESDE=1
        HASTA=3
        GRUPO="mknapcb1 a mknapcb3 (m=5, 9 instancias)"
        ;;
    2)
        DESDE=4
        HASTA=6
        GRUPO="mknapcb4 a mknapcb6 (m=10, 9 instancias)"
        ;;
    3)
        DESDE=7
        HASTA=9
        GRUPO="mknapcb7 a mknapcb9 (m=30, 9 instancias)"
        ;;
    *)
        echo "Error: ID de tarea inválido: $TASK_ID (debe ser 1, 2 o 3)"
        exit 1
        ;;
esac

echo "=========================================================="
echo "Ejecutando Trabajo $TASK_ID/3: $GRUPO"
echo "Nodo: $SLURMD_NODENAME | CPUs: $CPUS | ID: $SLURM_JOB_ID"
echo "=========================================================="

python run_benchmark_hpc.py --desde $DESDE --hasta $HASTA --indices 0 15 29 --cpus $CPUS --epochs 31

echo "<<Trabajo $TASK_ID ($GRUPO) terminado exitosamente>>"
