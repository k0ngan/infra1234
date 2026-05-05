# Resumen de la Actividad 03

## Objetivo
Comparar paralelismo local y procesamiento distribuido local para determinar cuándo conviene vectorizar, paralelizar o distribuir cargas de trabajo.

## Enfoque aplicado
- Carga numérica intensiva en tres estilos: Python puro, NumPy y `multiprocessing`.
- Workloads CPU-bound e I/O-bound sobre `ThreadPoolExecutor` y `ProcessPoolExecutor`.
- Comparativa Pandas vs Dask local sobre datos repartidos en `4`, `16` y `64` particiones.

## Hallazgos de la última corrida
- Mejor speedup vectorizado: `10.69x` con tamaño `4000000`.
- Mejor configuración CPU-bound con procesos: `4` workers, chunk `large`, speedup `3.04x`.
- Mejor configuración I/O-bound con hilos: `8` workers, chunk `small`, speedup `3.67x`.
- Mejor corrida de Dask: `16` particiones en `2.95s`.
- El mayor overhead de coordinación observado aparece cerca de `8` workers.

## Recomendaciones por escenario
- Servidor único: preferir NumPy vectorizado cuando el dataset cabe en memoria y la operación es numérica.
- Múltiples fuentes: usar hilos para I/O-bound y Dask local cuando ya existen particiones o archivos independientes.
- Escenario cloud: escalar hacia un motor distribuido solo si el costo de particionar y coordinar se compensa con más volumen y consultas repetidas.

## Complejidad adicional incorporada
Se superpuso el speedup observado con curvas tipo Amdahl y Gustafson para mostrar explícitamente por qué el crecimiento deja de ser lineal al aumentar workers.
