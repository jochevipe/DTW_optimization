#!/bin/bash
#SBATCH --job-name=dtw_opt1   # Nombre que verás en la cola
#SBATCH --partition=CPU
#SBATCH --cpus-per-task=40           # 4 CPUs para procesar datos (cargar imágenes)
#SBATCH --mem=32G                   # 16 GB de RAM del sistema (no de video)
#SBATCH --output=./logs/dtw_opt1%j.log   # Archivo donde se guardará lo que imprima el script (%j es el ID del trabajo)
#SBATCH --error=./errors/dtw_opt1%j.error        # Archivo donde se guardarán los errores si falla
#SBATCH --qos=normal               #QOS de HPC

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1



# 1. Cargar el entorno (OBLIGATORIO)
# Primero cargamos el módulo de conda si es necesario (a veces no hace falta si ya está en .bashrc, pero es buena práctica)
source $HOME/miniconda3/etc/profile.d/conda.sh

echo "Iniciando trabajo en el nodo: $SLURMD_NODENAME"
echo "CPUs asignadas por SLURM: $SLURM_CPUS_PER_TASK"
echo "Variables de hilos configuradas a: $OMP_NUM_THREADS"


# 2. Activar tu entorno virtual
conda activate DTW_optimization

# 4. Ejecutar el benchmark completo sobre las 9 instancias en paralelo
python run_benchmark_hpc.py --cpus $SLURM_CPUS_PER_TASK

echo "<<Script de Trabajo terminado>>"
