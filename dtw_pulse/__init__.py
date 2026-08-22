"""
DTW-Pulse — base EXPLORE con pulsos acotados de EXPLOIT (target: BinaryPSO).
Entra a exploit ante mejora fresca o alta actividad (D2 > 2*theta_c).
Sale de exploit cuando la curva se aplana sin mejora nueva o al alcanzar
el largo máximo de pulso (evita quedar atrapado en exploit, ya que ninguna
MH resetea el estado de población al cambiar de modo).
"""
