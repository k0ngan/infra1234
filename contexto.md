# Contexto de las 4 actividades

Este archivo resume, a partir de la lectura de los cuatro PDF, que se tiene que hacer en cada actividad de la asignatura **Infraestructura para Ciencia de Datos**.

## Requisitos comunes

- Las actividades pueden hacerse de forma individual o en parejas, con maximo 2 integrantes.
- En todos los casos se debe documentar el entorno experimental o de ejecucion: sistema operativo, hardware, version de Python y librerias usadas cuando corresponda.
- El codigo debe ser original, reproducible y estar bien documentado.
- Se deben citar fuentes y declarar el uso de herramientas de apoyo, incluyendo IA si fue utilizada.
- Se espera una entrega ordenada con codigo funcional, evidencias, visualizaciones cuando aplique, y un informe tecnico claro.

## 01_primera_actividad.pdf

### Tema
Boot de Micro S.O. en QEMU.

### Que hay que hacer

- Construir un micro sistema operativo simple en ensamblador.
- Compilarlo con NASM.
- Ejecutarlo en QEMU.
- Lograr que el sistema arranque correctamente y muestre un mensaje en pantalla.
- Documentar el flujo completo desde el codigo fuente hasta el binario ejecutable.

### En que se enfoca la actividad

- Comprender el proceso de boot.
- Relacionar codigo fuente, ensamblado, binario, arranque y virtualizacion.
- Trabajar con reproducibilidad, trazabilidad y documentacion tecnica.

### Entregables esperados

- Codigo fuente en ensamblador.
- Instrucciones claras para compilar y ejecutar.
- Evidencias del arranque, como capturas.
- Video breve de presentacion.
- Informe tecnico.
- Repositorio con el trabajo organizado.

## 02_Segunda_Actividad.pdf

### Tema
Investigacion y benchmarking de jerarquia de memoria e I/O.

### Que hay que hacer

- Realizar una parte teorica sobre jerarquia de memoria, localidad temporal y espacial, y arquitecturas batch, streaming e hibridas.
- Implementar experimentos en Python para medir rendimiento.
- Analizar resultados y redactar un informe tecnico final.

### Experimentos que se deben realizar

- **Experimento A:** comparar operaciones en memoria y en disco para varios tamanos y calcular throughput.
- **Experimento B:** comparar acceso secuencial y acceso aleatorio sobre archivos CSV y Parquet.
- **Experimento C:** simular un pipeline de ingesta, transformacion y almacenamiento para detectar el principal cuello de botella.
- **Experimento D:** comparar procesamiento batch vs streaming, evaluando latencia y throughput para distintos tamanos de lote.

### Requisitos minimos importantes

- Usar al menos 5 tamanos distintos en el experimento A.
- Comparar CSV y Parquet en el experimento B.
- Disenar al menos 6 configuraciones en el experimento C.
- Probar lotes de 100, 500, 1000 y 5000 en el experimento D.

### Entregables esperados

- Informe tecnico en PDF.
- Codigo Python funcional.
- Datos de experimentos.
- Visualizaciones de resultados.
- README o documentacion para reproducir el trabajo.

## 03_Tercera_Actividad.pdf

### Tema
Paralelismo local y procesamiento distribuido en Data Science.

### Que hay que hacer

- Elaborar una parte teorica comparando procesamiento paralelo y distribuido.
- Implementar experimentos en Python para comparar enfoques secuenciales, paralelos y distribuidos.
- Medir speedup, eficiencia, overhead, escalabilidad y costo de coordinacion.
- Presentar conclusiones tecnicas segun el tipo de problema y el entorno disponible.

### Requisitos tecnicos relevantes

- Usar al menos un mecanismo de paralelismo local, por ejemplo `multiprocessing`, `concurrent.futures` o `joblib`.
- Usar al menos un framework distribuido en modo local, por ejemplo Dask o PySpark.
- Documentar CPU, numero de nucleos, RAM, sistema operativo, librerias y si hay o no GPU.

### Experimentos que se deben realizar

- **Experimento A:** comparar Python secuencial, version vectorizada con NumPy y una version paralela local en una carga numerica intensiva.
- **Experimento B:** comparar ejecucion secuencial, `ThreadPoolExecutor` y `ProcessPoolExecutor` sobre tareas independientes, analizando workers, tamanos de lote y si la carga es CPU-bound o I/O-bound.
- **Experimento C:** comparar procesamiento con Pandas frente a un framework distribuido local sobre datos particionados.
- **Experimento D:** modelar el overhead de coordinacion, serializacion o comunicacion para mostrar que el speedup no crece linealmente.

### Entregables esperados

- Informe tecnico.
- Codigo reproducible.
- Datos o particiones usadas en los experimentos.
- Visualizaciones.
- Analisis de trade-offs y recomendaciones por escenario.

## 04_Cuarta_Actividad.pdf

### Tema
Tratamiento de archivos Big Data, particionamiento y seleccion arquitectonica en Python.

### Que hay que hacer

- Desarrollar una parte teorica sobre clasificacion de arquitecturas Big Data y criterios de seleccion de infraestructura.
- Implementar experimentos en Python para trabajar con archivos grandes bajo restricciones de memoria.
- Justificar tecnicamente cuando conviene una solucion batch local, cuando usar particionamiento, cuando usar formato columnar y cuando tendria sentido escalar a una arquitectura distribuida o cloud.

### Experimentos que se deben realizar

- **Experimento A:** construir o seleccionar un dataset tabular grande y plausible, inicialmente en CSV o JSONL.
- **Experimento B:** comparar lectura completa con `pandas.read_csv()` frente a lectura por partes con `chunksize`.
- **Experimento C:** implementar procesamiento incremental correcto, incluyendo filtrado, seleccion de columnas, conversion de tipos, agregaciones y combinacion de resultados parciales.
- **Experimento D:** convertir a Parquet, particionar por una variable relevante y comparar consultas para justificar decisiones arquitectonicas.

### Requisitos minimos importantes

- El dataset debe tener al menos 1 millon de filas, o justificar si es menor.
- Evaluar al menos 3 tamanos de `chunksize`.
- Medir tiempo y memoria.
- Generar al menos 4 visualizaciones.

### Entregables esperados

- Informe tecnico.
- Codigo funcional.
- Datos originales y convertidos.
- Tablas de resultados.
- Visualizaciones.
- Recomendacion arquitectonica basada en evidencia.

## Resumen general

En conjunto, las cuatro actividades piden:

- Comprender fundamentos de infraestructura, desde el arranque de un sistema hasta decisiones de arquitectura Big Data.
- Implementar codigo reproducible, no solo responder teoria.
- Medir rendimiento con experimentos bien documentados.
- Comparar alternativas tecnicas con evidencia.
- Entregar informes claros, con metodologia, resultados, analisis y conclusiones.

## Idea central por semana

- **Semana 1:** entender el arranque y la virtualizacion desde muy bajo nivel.
- **Semana 2:** estudiar memoria, disco, formatos y cuellos de botella de I/O.
- **Semana 3:** comparar secuencial, paralelo y distribuido.
- **Semana 4:** trabajar con archivos grandes y justificar decisiones de arquitectura de datos.
