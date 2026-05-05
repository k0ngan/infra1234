# Actividad 04: Archivos Big Data, particionamiento y seleccion arquitectonica

## Objetivo
Generar un dataset tabular grande y usarlo para comparar lectura completa, lectura incremental, procesamiento por chunks y conversion a Parquet plano/particionado.

## Estructura
- `src/main.py`: genera el dataset, corre los experimentos A-D y actualiza `resumen.md`.
- `data/veterinary_visits_bigdata.csv`: dataset sintetico base de al menos 1.5 millones de filas.
- `data/veterinary_visits_bigdata.parquet`: version columnar no particionada.
- `data/veterinary_visits_partitioned/`: version Parquet particionada por sucursal veterinaria.
- `results/*.csv`: metricas de tiempo, memoria y tamano.
- `results/*.png`: visualizaciones de tamanos, tiempos y formato.

## Ejecucion
Desde la raiz:

```bash
docker compose run --rm actividad04
```

Desde esta carpeta:

```bash
docker build -t actividad04 .
docker run --rm -v ${PWD}:/workspace actividad04
```

## Artefactos esperados
- `results/experiment_a.csv`
- `results/experiment_b.csv`
- `results/experiment_c.csv`
- `results/experiment_d.csv`
- `results/incremental_aggregate.csv`
- `results/exp_a_storage_profile.png`
- `results/exp_b_chunked_reads.png`
- `results/exp_c_incremental_top_categories.png`
- `results/exp_d_query_formats.png`
- `results/exp_d_storage_sizes.png`
- `resumen.md` actualizado con recomendacion arquitectonica

## Criterio de exito
- El dataset generado tiene `1.500.000` filas o mas.
- El experimento B compara lectura monolitica contra `chunksize 50k, 100k y 250k`.
- El experimento C implementa un pipeline incremental split-process-combine correcto.
- El experimento D compara CSV, Parquet plano y Parquet particionado.
