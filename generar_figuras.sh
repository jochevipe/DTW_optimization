#!/bin/bash
# ==============================================================================
# generar_figuras.sh — Generación de Boxplots para el Paper (MKP 27 instancias)
# ==============================================================================
# Genera las figuras comparativas de las 4 versiones en alta resolución (PDF + PNG)
# para las subsecciones de cada problema mknapcb1..9 (instancias 0, 15 y 29).
# ==============================================================================

source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate DTW_optimization

echo "=========================================================="
echo "Generando boxplots de publicación para el Paper..."
echo "=========================================================="

python -m analisis.generar_figuras --dpi 300 

echo ""
echo "=========================================================="
echo "Figuras generadas exitosamente en results/figuras/:"
echo "  - Paneles por problema (grid 3x4): results/figuras/mknapcb{1..9}_boxplot.pdf"
echo "  - Figuras individuales (grid 1x4): results/figuras/individuales/mknapcb{1..9}_inst{0,15,29}_boxplot.pdf"
echo "=========================================================="
