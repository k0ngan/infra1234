# Resumen de la Actividad 04

## Objetivo
Evaluar como el formato, el particionamiento y la lectura incremental cambian el costo de procesar archivos grandes en un escenario Big Data.

## Enfoque aplicado
- Dataset sintetico plausible de `1.500.000` filas sobre atenciones de clinicas veterinarias y mascotas, con variables temporales, categoricas y numericas.
- Lectura monolitica vs por chunks con `50k`, `100k` y `250k`.
- Pipeline incremental split-process-combine con filtrado, casteo, agregacion y metrica derivada.
- Comparativa CSV vs Parquet plano vs Parquet particionado por sucursal veterinaria.

## Hallazgos de la ultima corrida
- Filas generadas: `1500000`.
- Tamano del CSV base: `147.88 MB`.
- Lectura mas rapida del experimento B: `chunked_read` con chunk `50000` en `2.09s`.
- Mejor consulta filtrada: `parquet_partitioned` en `0.12s`.
- Mejor agregacion: `parquet_partitioned` en `0.38s`.
- Tamanos por formato: `{'csv': 147.88, 'parquet_flat': 42.53, 'parquet_partitioned': 64.14}`.

## Recomendacion arquitectonica
- Batch local: suficiente cuando el CSV cabe en disco y la carga es una corrida esporadica.
- Data lake/lakehouse: preferible cuando predominan consultas repetidas por sucursal o especie, porque el Parquet particionado reduce I/O.
- Formato recomendado para analisis recurrente: Parquet plano para scans completos y Parquet particionado cuando el patron dominante son cortes operacionales por sucursal.

## Complejidad adicional incorporada
Se comparo CSV contra Parquet plano y Parquet particionado, no solo contra la variante particionada, para justificar mejor la decision arquitectonica final.
