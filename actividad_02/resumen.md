# Resumen de la Actividad 02

## Objetivo
Medir el impacto de la jerarquía de memoria, los formatos de almacenamiento y la forma de procesar flujos de datos sobre throughput y latencia.

## Enfoque aplicado
- Datos sintéticos reproducibles en CSV y Parquet.
- Warmup previo para los experimentos de memoria y streaming.
- Benchmark separado por memoria/disco, patrones de acceso, ETL y batch vs streaming.

## Decisiones técnicas
- En el experimento B se indexaron offsets de CSV para emular acceso aleatorio real sin cargar el archivo completo.
- En el experimento C se trataron CSV como I/O lento y Parquet como I/O rápido para aislar cuellos de botella.
- En el experimento D se reportó latencia media, máxima y `p95`, además del throughput.

## Hallazgos de la última corrida
- Mejor throughput de RAM: `7040.12 MB/s` con `8 MB`.
- Acceso más rápido en el experimento B: `parquet-random`.
- Configuración batch más rápida: `10000` registros por lote con `35620315.97 registros/s`.
- Menor latencia `p95`: modo `streaming` con lote `500` y `0.0006 ms`.
- Cuello de botella dominante del ETL: `{'transform': 2, 'read': 2, 'write': 2}`.

## Complejidad adicional incorporada
Se agregó warmup controlado y reporte de latencia `p95`, lo que permite comparar no solo promedio sino también cola de latencias en el escenario batch vs streaming.
