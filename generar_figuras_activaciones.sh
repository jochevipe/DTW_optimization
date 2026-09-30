#!/bin/bash
# ==============================================================================
# generar_figuras_activaciones.sh — Generación de Figuras de Activaciones DTW
# ==============================================================================
# Genera las figuras comparativas de activaciones de DTW (s_t = 1) en alta resolución
# (PDF vectorial + PNG 300 DPI) para los 9 problemas (mknapcb1..9) y sus instancias
# (0, 15, 29) replicando y extendiendo la figura de results_old.
# ==============================================================================

source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate DTW_optimization

echo "=========================================================="
echo "Generando figuras de activaciones DTW para el Paper..."
echo "=========================================================="

python -m analisis.generar_figura_activaciones --dpi 300 "$@"

echo ""
echo "=========================================================="
echo "Figuras generadas exitosamente en results/figuras/activaciones/:"
echo "  - Panel principal (grid 2x2): fig_dtw_activations_grid.pdf"
echo "  - Paneles por instancia: fig_dtw_activations_inst{0,15,29}.pdf"
echo "  - Desglose 27 instancias: fig_dtw_activations_all_instances.pdf"
echo "  - Figuras individuales por problema: individuales/mknapcb{1..9}_activations.pdf"
echo "  - Tablas: tabla_activaciones_dtw.tex y tabla_activaciones_dtw.csv"
echo "=========================================================="
