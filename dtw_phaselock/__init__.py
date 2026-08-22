"""
DTW-PhaseLock — base EXPLOIT con explore sostenido solo ante estancamiento
profundo confirmado (D2 <= theta_c y no_improve_len >= plateau_min).
Vuelve a exploit ante mejora fresca o alta actividad (D2 > 2.5*theta_c).
Desviación del doc 06: el dead-band P80 no existe en el monitor; la banda se
implementa como multiplicadores de theta_c.
"""
