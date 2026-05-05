# Actividad 02: Jerarquía de memoria e I/O

## Objetivo
Ejecutar benchmarks reproducibles sobre memoria, disco, formatos tabulares y estrategias batch/streaming, dejando métricas y visualizaciones listas para informe.

## Marco Teórico

- **Jerarquía de memoria:** Los tiempos de acceso varían varios órdenes de magnitud: registros (~0.3 ns), caché L1/L2 (~1–10 ns), DRAM (~100 ns) y SSD (~100 µs). Ignorar esta jerarquía es la causa más frecuente de cuellos de botella en pipelines de ciencia de datos.
- **Localidad temporal y espacial:** Acceder repetidamente al mismo dato (temporal) o a datos contiguos en memoria (espacial) maximiza la tasa de aciertos de caché. El experimento B cuantifica empíricamente el costo de no respetar esta localidad al comparar acceso secuencial y aleatorio.
- **Formatos columnares vs orientados a filas:** CSV almacena filas completas; Parquet agrupa columnas con compresión por columna. Para consultas analíticas que leen pocas columnas de muchas filas, Parquet reduce I/O entre 3× y 10× respecto a CSV.
- **Arquitecturas batch y streaming:** El procesamiento batch agrupa eventos para maximizar throughput; el streaming procesa eventos individualmente para minimizar latencia. El experimento D mide el trade-off latencia/throughput al variar el tamaño de lote entre 100 y 10 000 registros.
- **Warmup experimental:** Los primeros accesos a disco cargan bloques en el caché del sistema operativo. Sin un paso de warmup previo, las primeras mediciones incluyen ese costo extra y sesgan la comparación entre tamaños de payload.

## Estructura
- `src/main.py`: genera datos, corre los experimentos A-D y actualiza `resumen.md`.
- `data/benchmark_dataset.csv`: dataset tabular sintético base.
- `data/benchmark_dataset.parquet`: versión columnar del mismo dataset.
- `results/*.csv`: tablas de métricas por experimento.
- `results/*.json`: metadatos y resumen técnico.
- `results/*.png`: visualizaciones para el informe.

## Ejecución
Desde la raíz:

```bash
docker compose run --rm actividad02
```

Desde esta carpeta:

```bash
docker build -t actividad02 .
docker run --rm -v ${PWD}:/workspace actividad02
```

## Artefactos esperados
- `results/experiment_a.csv`
- `results/experiment_b.csv`
- `results/experiment_c.csv`
- `results/experiment_d.csv`
- `results/environment.json`
- `results/exp_a_throughput.png`
- `results/exp_b_access_patterns.png`
- `results/exp_c_stage_breakdown.png`
- `results/exp_d_latency.png`
- `results/exp_d_throughput.png`
- `resumen.md` actualizado con hallazgos y cuello de botella dominante

## Criterio de éxito
- Se generan los cuatro experimentos con datos reproducibles.
- Los tamaños del experimento A son `8, 32, 128, 256 y 512 MB`.
- El experimento D reporta latencia `p95`.
- La carpeta `results/` contiene tablas, JSON y al menos cuatro gráficos PNG.
