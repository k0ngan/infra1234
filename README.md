# Infraestructura para Ciencia de Datos — UTEM

Repositorio integrador de la asignatura **Infraestructura para Ciencia de Datos** de la Universidad Tecnológica Metropolitana (UTEM).  
Contiene cuatro actividades evaluadas, cada una contenerizada con Docker y orquestada desde un único `docker-compose.yml`.

## Descripción general

El proyecto explora los fundamentos prácticos de infraestructura que sustentan la ciencia de datos moderna: desde el arranque de un sistema operativo mínimo hasta la selección de arquitecturas de almacenamiento para conjuntos de datos de gran volumen.  
Cada actividad es autocontenida, reproducible y documentada con evidencia medida.

## Actividades

| # | Título | Tema central | Tecnologías |
|---|--------|--------------|-------------|
| 01 | Boot de Micro S.O. en QEMU | Virtualización y arranque | NASM, QEMU, Docker |
| 02 | Jerarquía de Memoria e I/O | Benchmarking de almacenamiento | Pandas, PyArrow, Matplotlib |
| 03 | Paralelismo Local y Distribuido | Speedup y overhead de coordinación | multiprocessing, Dask, concurrent.futures |
| 04 | Big Data y Selección Arquitectónica | Formatos y particionamiento | PyArrow Datasets, Parquet, Pandas chunking |

## Requisitos previos

| Herramienta | Versión mínima | Notas |
|-------------|---------------|-------|
| Docker Desktop | 24.x | Con `docker compose` v2 incluido |
| RAM disponible | 4 GB | 8 GB recomendado para actividad 04 |
| Espacio en disco | 4 GB libres | Imágenes Docker + datos generados |

## Inicio rápido

```bash
# 1. Construir todas las imágenes
docker compose build

# 2. Ejecutar cada actividad (los resultados quedan en results/ de su carpeta)
docker compose run --rm actividad01
docker compose run --rm actividad02
docker compose run --rm actividad03
docker compose run --rm actividad04

# 3. Iniciar el dashboard de revisión
docker compose up dashboard
```

El dashboard queda disponible en **http://localhost:8501**.

## Dashboard de revisión

El dashboard Streamlit integra en una sola interfaz:

- Documentación y hallazgos de cada actividad (pestañas README, Resumen y Resultados).
- Visualizaciones PNG generadas automáticamente en grilla de dos columnas.
- Tablas CSV con métricas de cada experimento (colapsables).
- Indicador de estado por actividad (ejecutada / pendiente).

## Estructura del repositorio

```
infra/
├── docker-compose.yml              # Orquestación de todos los servicios
├── README.md                       # Este documento
├── resumen_actividades.md          # Síntesis de los enunciados PDF
├── actividad_01/                   # Micro S.O. en ensamblador + QEMU
│   ├── Dockerfile
│   ├── README.md
│   ├── src/
│   │   ├── boot.asm                # Boot sector de 512 bytes en NASM
│   │   └── run.py                  # Compilación, validación y ejecución headless
│   └── results/                   # boot.img · serial.log · boot_report.json
├── actividad_02/                   # Benchmarks de jerarquía de memoria e I/O
│   ├── src/main.py
│   ├── data/                      # Dataset CSV y Parquet generados
│   └── results/                   # Tablas CSV · JSON · gráficos PNG
├── actividad_03/                   # Paralelismo local y Dask
│   ├── src/main.py
│   ├── data/                      # Particiones CSV y chunks binarios
│   └── results/
├── actividad_04/                   # Big Data: formatos y selección arquitectónica
│   ├── src/main.py
│   ├── data/                      # CSV · Parquet plano · Parquet particionado
│   └── results/
└── dashboard/                      # Dashboard Streamlit de revisión
    ├── Dockerfile
    ├── requirements.txt
    └── app.py
```

## Reproducibilidad

- Todas las actividades utilizan la semilla `SEED = 20260505` para resultados deterministas entre corridas.
- Las imágenes Docker fijan versiones de dependencias en cada `requirements.txt`.
- Cada actividad genera un `resumen.md` actualizado automáticamente con los resultados de la última ejecución.
