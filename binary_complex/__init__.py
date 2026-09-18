"""
Binary-Complex (A9) — Control con histéresis asimétrica sobre la señal A4 del monitor
=====================================================================================
Entra a explore cuando el trigger A4 sostenido del monitor dispara
(meseta + constante + rampa/delta durante `patience` iteraciones).
Sale de explore ante la primera mejora (no_improve_len == 0).
La asimetría entrada/salida evita flickering entre modos.
"""
