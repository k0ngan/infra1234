# Actividad 03: Paralelismo local y procesamiento distribuido

## Objetivo
Comparar enfoques secuenciales, vectorizados, paralelos y distribuidos para cargas típicas de ciencia de datos, cuantificando speedup, eficiencia y overhead.

## Marco Teórico

- **Global Interpreter Lock (GIL) de CPython:** El GIL impide que múltiples hilos ejecuten bytecode Python simultáneamente. Para cargas CPU-bound, `ThreadPoolExecutor` no produce speedup real; `ProcessPoolExecutor` sí, porque cada proceso tiene su propio intérprete y su propio espacio de memoria.
- **Ley de Amdahl:** El speedup máximo alcanzable con `p` procesadores es `S = 1 / ((1 − F) + F/p)`, donde `F` es la fracción paralelizable del trabajo. Una fracción serial del 10 % limita el speedup a ×10 independientemente del número de cores disponibles.
- **Ley de Gustafson:** A diferencia de Amdahl, Gustafson asume que el tamaño del problema crece con los recursos disponibles: `S = p − (1 − F)(p − 1)`. Captura mejor los escenarios donde se procesan más datos al agregar workers, en lugar de resolver el mismo problema más rápido.
- **Overhead de coordinación:** La serialización de datos entre procesos, la creación y destrucción de workers y la sincronización de resultados parciales añaden latencia. El experimento D mide cuantitativamente la diferencia entre el speedup teórico y el observado.
- **Dask local:** Dask divide DataFrames en particiones y construye un grafo de computación diferida. Con `LocalCluster`, los workers se comunican en memoria sin red, reduciendo el overhead frente a un cluster distribuido real y haciendo viable la comparación en un entorno de desarrollo.

## Estructura
- `src/main.py`: genera datos, ejecuta los experimentos A-D y actualiza `resumen.md`.
- `data/partitioned/`: datos tabulares repartidos en 4, 16 y 64 particiones para Pandas y Dask.
- `data/io_chunks/`: insumos para el experimento I/O-bound con ejecutores.
- `results/*.csv`: tablas de rendimiento.
- `results/*.png`: visualizaciones comparativas y curvas teóricas.

## Ejecución
Desde la raíz:

```bash
docker compose run --rm actividad03
```

Desde esta carpeta:

```bash
docker build -t actividad03 .
docker run --rm -v ${PWD}:/workspace actividad03
```

## Artefactos esperados
- `results/experiment_a.csv`
- `results/experiment_b.csv`
- `results/experiment_c.csv`
- `results/experiment_d.csv`
- `results/exp_a_scaling.png`
- `results/exp_b_cpu_speedup.png`
- `results/exp_b_io_throughput.png`
- `results/exp_c_pandas_vs_dask.png`
- `results/exp_d_speedup_curves.png`
- `resumen.md` con recomendaciones para servidor único, múltiples fuentes y nube

## Criterio de éxito
- El experimento A compara Python secuencial, NumPy vectorizado y `multiprocessing`.
- El experimento B usa `ThreadPoolExecutor` y `ProcessPoolExecutor` en workloads CPU-bound e I/O-bound.
- El experimento C compara Pandas y Dask con `4`, `16` y `64` particiones.
- El experimento D deja una curva observada frente a Amdahl y Gustafson.
