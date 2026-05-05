# Resumen de actividades

Este resumen fue elaborado a partir del contenido de los cuatro PDF indicados en `contexto.md`.

## 01_primera_actividad.pdf

**Titulo o encabezado principal:**  
`ACTIVIDAD NO 1: Boot de Micro S.O. en QEMU`

**Resumen breve:**  
La actividad introduce una aproximacion de bajo nivel a la infraestructura computacional mediante la construccion de un micro sistema operativo en ensamblador y su ejecucion en QEMU. El objetivo central es que el estudiantado comprenda el flujo completo desde el codigo fuente hasta el arranque de un binario reproducible, relacionando ensamblado, virtualizacion, arranque y documentacion tecnica con fundamentos de infraestructura para ciencia de datos.

**Secciones destacadas y puntos clave:**  
- Objetivo y justificacion en la asignatura: vincula el ejercicio con virtualizacion, reproducibilidad, automatizacion y trazabilidad.
- Objetivos especificos: comprender el proceso de boot, implementar el micro S.O., construir un flujo reproducible y documentar tecnicamente el trabajo.
- Indicaciones tecnicas: usar NASM para compilar y QEMU para emular; el sistema debe arrancar y mostrar un mensaje en pantalla.
- Desarrollo paso a paso: organizacion del repositorio, preparacion del entorno, revision de referentes, implementacion, compilacion, pruebas, iteracion, trazabilidad, analisis academico, video y entrega final.
- Productos esperados: codigo fuente, artefacto compilado o instrucciones para generarlo, video explicativo, informe de maximo cinco paginas y repositorio GitHub con evidencias.
- Recursos web validados: QEMU, documentacion de QEMU, NASM, OSDev Wiki y GitHub Docs.
- Rubrica de evaluacion: considera precision tecnica, reproducibilidad, documentacion, analisis del contexto de infraestructura y presentacion oral/video.

**Tablas, graficos o diagramas:**  
Incluye una tabla de rubrica de evaluacion. No se observan graficos analiticos ni diagramas tecnicos desarrollados dentro del documento.

## 02_Segunda_Actividad.pdf

**Titulo o encabezado principal:**  
`ACTIVIDAD SEMANA 2: Investigacion y Benchmarking de Jerarquia de Memoria e I/O`

**Resumen breve:**  
La actividad combina investigacion teorica y experimentacion practica en Python para estudiar el impacto de la jerarquia de memoria, los patrones de acceso a datos y la entrada/salida en tareas tipicas de Data Science. El foco esta en medir rendimiento, detectar cuellos de botella y comparar arquitecturas batch y streaming mediante benchmarks reproducibles.

**Secciones destacadas y puntos clave:**  
- Instrucciones generales: trabajo individual o en parejas, con documentacion del entorno experimental, uso de codigo original y declaracion de apoyo externo.
- Parte teorica: explicar jerarquia de memoria, localidad temporal y espacial, y arquitecturas batch, streaming e hibridas.
- Experimento A: comparar operaciones en memoria y en disco para distintos tamanos y calcular throughput.
- Experimento B: comparar acceso secuencial y aleatorio sobre archivos CSV y Parquet.
- Experimento C: simular un pipeline de ingesta, transformacion y almacenamiento para detectar el principal cuello de botella.
- Experimento D: comparar procesamiento batch vs streaming, analizando latencia y throughput para distintos tamanos de lote.
- Requisitos adicionales: al menos cinco tamanos en el experimento A, comparacion CSV/Parquet, seis configuraciones en el experimento C y lotes de 100, 500, 1000 y 5000 en el experimento D.
- Productos esperados: informe tecnico PDF, codigo Python, datos de experimentos, visualizaciones, documentacion del entorno y repositorio con README.
- Estructura sugerida del informe: portada, resumen ejecutivo, marco teorico, metodologia, resultados, analisis, conclusiones y anexos.
- Observaciones adicionales: enfatiza redaccion formal, control metodologico y correcto uso de fuentes.

**Tablas, graficos o diagramas:**  
Incluye una tabla detallada de rubrica de evaluacion. No contiene graficos o diagramas explicativos propios; mas bien exige que el estudiante los produzca como parte del trabajo.

## 03_Tercera_Actividad.pdf

**Titulo o encabezado principal:**  
`ACTIVIDAD SEMANA 3: Paralelismo Local y Procesamiento Distribuido en Data Science`

**Resumen breve:**  
La actividad busca que el estudiantado compare estrategias de procesamiento secuencial, paralelo y distribuido en problemas de ciencia de datos. Integra teoria y experimentacion en Python para medir speedup, eficiencia, overhead, escalabilidad y costo de coordinacion, con enfasis en decidir tecnicamente cuando conviene paralelizar, distribuir o mantener una solucion monolitica.

**Secciones destacadas y puntos clave:**  
- Instrucciones generales: documentar CPU, nucleos, memoria, sistema operativo, librerias y disponibilidad de GPU; usar al menos un mecanismo de paralelismo local y un framework distribuido local como Dask o PySpark.
- Parte teorica: comparar procesamiento paralelo y distribuido, con ventajas, limites y criterios de decision.
- Experimento A: comparar una implementacion secuencial, una vectorizada con NumPy y una paralela local para una carga numerica intensiva.
- Experimento B: paralelismo a nivel de tareas con `ThreadPoolExecutor` y `ProcessPoolExecutor`, variando workers y tamano de lote.
- Experimento C: procesamiento distribuido con Dask o PySpark sobre datos particionados, comparado contra Pandas.
- Experimento D: modelar overhead de coordinacion, serializacion o comunicacion para demostrar que el speedup no crece linealmente.
- Requisitos adicionales: repetir experimentos al menos tres veces, evaluar distintos tamanos de entrada, workers y particiones, e incluir al menos cuatro visualizaciones.
- Registro minimo obligatorio: version de Python, sistema operativo, hardware, librerias, parametros, tiempos y analisis.
- Advertencia de integridad academica: prohibe usar IA como sustituto del razonamiento del grupo y sanciona entregas demasiado similares entre estudiantes.
- Productos esperados: informe tecnico, codigo Python, datos y particiones, visualizaciones, documentacion del entorno y repositorio con README.

**Tablas, graficos o diagramas:**  
Incluye una tabla de rubrica de evaluacion y una seccion de referencias bibliograficas. No se observan diagramas; el documento es principalmente textual y normativo.

## 04_Cuarta_Actividad.pdf

**Titulo o encabezado principal:**  
`ACTIVIDAD SEMANA 4: Tratamiento de Archivos Big Data, Particionamiento y Seleccion Arquitectonica en Python`

**Resumen breve:**  
La actividad aborda el tratamiento de archivos grandes en escenarios Big Data y exige justificar decisiones de infraestructura a partir de evidencia experimental en Python. El enfasis esta en comparar lectura completa versus incremental, procesamiento por fragmentos, conversion a formato columnar, particionamiento y seleccion de arquitecturas como batch local, data lake, lakehouse o soluciones distribuidas/cloud.

**Secciones destacadas y puntos clave:**  
- Instrucciones generales: articular clasificacion de arquitecturas Big Data con seleccion de infraestructura usando criterios tecnicos y resultados medidos.
- Parte teorica: explicar como se clasifican las arquitecturas Big Data y como influyen tamano, formato, particionamiento y patron de acceso.
- Experimento A: construir o seleccionar un dataset tabular grande y plausible, inicialmente en CSV o JSONL, con variables temporales, categoricas y numericas.
- Experimento B: comparar lectura monolitica con `pandas.read_csv()` frente a lectura por partes con `chunksize`.
- Experimento C: implementar procesamiento incremental con filtrado, seleccion de columnas, conversion de tipos, agregaciones y combinacion correcta de resultados parciales.
- Experimento D: convertir a Parquet, particionar por una variable relevante y comparar consultas para justificar decisiones arquitectonicas.
- Requisitos adicionales: dataset de al menos 1 millon de filas o justificar un tamano menor, evaluar al menos tres tamanos de `chunksize`, medir tiempo y memoria, y generar al menos cuatro visualizaciones.
- Registro minimo obligatorio: version de Python, sistema operativo, RAM, espacio en disco, librerias, tamano del archivo, formatos generados, criterio de particionamiento, tiempos y recomendacion final.
- Advertencia de integridad academica: insiste en que la IA no puede reemplazar el razonamiento propio y sanciona entregas esencialmente identicas.
- Productos esperados: informe tecnico, codigo Python, datos originales y convertidos, tablas de resultados, visualizaciones, documentacion del entorno y repositorio con README.

**Tablas, graficos o diagramas:**  
Incluye una tabla de rubrica de evaluacion y listados estructurados de requisitos y referencias. No presenta diagramas tecnicos ni graficos analiticos internos.

## Observacion general

Los cuatro documentos son guias de actividades evaluadas orientadas a infraestructura para ciencia de datos. Todos siguen una estructura similar: introduccion, etapas del trabajo, requisitos experimentales, productos esperados, recomendaciones, rubrica y referencias. En terminos visuales, predominan tablas de evaluacion y listados; no destacan diagramas ni graficos explicativos ya construidos dentro de los PDF.
