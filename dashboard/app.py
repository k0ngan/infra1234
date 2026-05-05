from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path("/workspace")

ACTIVITIES: dict[str, Path] = {
    "Actividad 01": ROOT / "actividad_01",
    "Actividad 02": ROOT / "actividad_02",
    "Actividad 03": ROOT / "actividad_03",
    "Actividad 04": ROOT / "actividad_04",
}

SIDEBAR_LABELS: dict[str, str] = {
    "Actividad 01": "🖥️  Act. 01 — Boot QEMU",
    "Actividad 02": "📊  Act. 02 — Memoria e I/O",
    "Actividad 03": "⚡  Act. 03 — Paralelismo",
    "Actividad 04": "📦  Act. 04 — Big Data",
}

DESCRIPTIONS: dict[str, str] = {
    "Actividad 01": "Boot de Micro S.O. en QEMU — NASM, virtualización y arranque reproducible.",
    "Actividad 02": "Jerarquía de Memoria e I/O — benchmarks de throughput, formatos y batch/streaming.",
    "Actividad 03": "Paralelismo Local y Distribuido — speedup, overhead y leyes de Amdahl/Gustafson.",
    "Actividad 04": "Big Data y Selección Arquitectónica — Parquet, particionamiento y lectura incremental.",
}

# Descripción de cada archivo CSV generado por experimento
CSV_DESCS: dict[str, dict[str, str]] = {
    "Actividad 02": {
        "experiment_a.csv": "Throughput RAM vs disco para payloads de 8 a 512 MB",
        "experiment_b.csv": "Acceso secuencial vs aleatorio en CSV y Parquet",
        "experiment_c.csv": "Desglose del pipeline ETL por etapa (read / transform / write)",
        "experiment_d.csv": "Latencia p95, media y máxima — batch vs streaming",
    },
    "Actividad 03": {
        "experiment_a.csv": "Escalado Python secuencial, NumPy vectorizado y multiprocessing",
        "experiment_b.csv": "ThreadPoolExecutor vs ProcessPoolExecutor en CPU-bound e I/O-bound",
        "experiment_c.csv": "Pandas vs Dask local con 4, 16 y 64 particiones",
        "experiment_d.csv": "Speedup observado vs curvas de Amdahl y Gustafson",
    },
    "Actividad 04": {
        "experiment_a.csv": "Perfil del dataset generado (filas, columnas, tamaño, tiempo de escritura)",
        "experiment_b.csv": "Lectura monolítica vs chunked (50k, 100k y 250k filas por chunk)",
        "experiment_c.csv": "Métricas del pipeline incremental split-process-combine",
        "experiment_d.csv": "CSV vs Parquet plano vs Parquet particionado por mes",
        "incremental_aggregate.csv": "Resultado final del pipeline incremental por mes y categoría",
    },
}


st.set_page_config(
    page_title="Infraestructura para Ciencia de Datos — UTEM",
    layout="wide",
    page_icon="🖥️",
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def status_for(activity_path: Path) -> str:
    results = activity_path / "results"
    if not results.exists():
        return "⚪ Sin ejecutar"
    if any(results.glob("*.csv")) or any(results.glob("*.png")) or any(results.glob("*.json")):
        return "🟢 Completada"
    return "🟡 Pendiente"


def extract_md_section(text: str, heading: str) -> str:
    """Devuelve el contenido de una sección ## del markdown, sin incluir el encabezado."""
    lines = text.split("\n")
    collecting = False
    result: list[str] = []
    for line in lines:
        if line.startswith("## ") and collecting:
            break
        if line.strip() == f"## {heading}":
            collecting = True
            continue
        if collecting:
            result.append(line)
    return "\n".join(result).strip()


# ── Páginas ───────────────────────────────────────────────────────────────────

def page_inicio() -> None:
    st.markdown(
        """
## Descripción del proyecto

Este repositorio integra cuatro actividades evaluadas de la asignatura
**Infraestructura para Ciencia de Datos** — Universidad Tecnológica Metropolitana (UTEM).

Cada actividad explora un nivel distinto de la pila de infraestructura que sustenta
los sistemas de datos modernos: desde el arranque del hardware hasta la selección
de arquitecturas para conjuntos de datos de gran volumen.
Todas son **reproducibles**, **contenerizadas con Docker** y generan artefactos medibles.
"""
    )

    # Estado de las actividades
    st.markdown("### Estado de las actividades")
    cols = st.columns(4)
    for col, (key, path) in zip(cols, ACTIVITIES.items(), strict=False):
        with col:
            st.metric(key, status_for(path))
            st.caption(DESCRIPTIONS[key])

    st.divider()

    # Tabla resumen
    st.markdown("### Resumen de actividades")
    summary = pd.DataFrame(
        {
            "#": ["01", "02", "03", "04"],
            "Título": [
                "Boot de Micro S.O. en QEMU",
                "Jerarquía de Memoria e I/O",
                "Paralelismo Local y Distribuido",
                "Big Data y Selección Arquitectónica",
            ],
            "Tema central": [
                "Virtualización y arranque de bajo nivel",
                "Benchmarking de almacenamiento y formatos de datos",
                "Speedup, overhead y leyes de escalado paralelo",
                "Formatos columnares, particionamiento y arquitecturas Big Data",
            ],
            "Tecnologías": [
                "NASM · QEMU · Docker",
                "Pandas · PyArrow · Matplotlib",
                "multiprocessing · Dask · concurrent.futures",
                "PyArrow Datasets · Parquet · Pandas chunking",
            ],
        }
    )
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.divider()

    # Contenido de los enunciados PDF
    resumen_path = ROOT / "resumen_actividades.md"
    if resumen_path.exists():
        st.markdown("### Contenido de los enunciados (PDF)")
        st.markdown(resumen_path.read_text(encoding="utf-8"))
    else:
        st.info("`resumen_actividades.md` no encontrado en la raíz del workspace.")


def tab_teoria(key: str, activity_path: Path) -> None:
    readme_path = activity_path / "README.md"
    if not readme_path.exists():
        st.warning("README.md no disponible.")
        return

    text = readme_path.read_text(encoding="utf-8")

    objetivo = extract_md_section(text, "Objetivo")
    if objetivo:
        st.markdown("### Objetivo")
        st.info(objetivo)

    teoria = extract_md_section(text, "Marco Teórico")
    if teoria:
        st.markdown("### Marco Teórico")
        st.markdown(teoria)
    else:
        st.info("Sección Marco Teórico no disponible.")

    criterio = extract_md_section(text, "Criterio de éxito")
    if criterio:
        st.divider()
        st.markdown("### Criterio de éxito")
        st.markdown(criterio)


def tab_visualizaciones(activity_path: Path) -> None:
    results = activity_path / "results"
    if not results.exists():
        st.warning("Ejecuta el contenedor primero para generar visualizaciones.")
        return
    image_files = sorted(results.glob("*.png"))
    if not image_files:
        st.info("Esta actividad no genera gráficos PNG (ver pestaña Resultados para los artefactos).")
        return
    cols = st.columns(2)
    for idx, img in enumerate(image_files):
        cols[idx % 2].image(str(img), caption=img.name, use_column_width=True)


def tab_resultados(key: str, activity_path: Path) -> None:
    results = activity_path / "results"
    if not results.exists():
        st.warning("Ejecuta el contenedor primero.")
        return

    # Resumen generado por el script
    resumen_path = activity_path / "resumen.md"
    if resumen_path.exists():
        st.markdown(resumen_path.read_text(encoding="utf-8"))
        st.divider()
    else:
        st.info("resumen.md aún no generado.")

    csv_files = sorted(results.glob("*.csv"))
    json_files = sorted(results.glob("*.json"))
    log_files = sorted(results.glob("*.log"))
    descs = CSV_DESCS.get(key, {})

    if csv_files:
        st.markdown("#### Tablas de métricas")
        for csv_path in csv_files:
            desc = descs.get(csv_path.name, "")
            header = f"{csv_path.name}" + (f"  —  {desc}" if desc else "")
            with st.expander(header):
                st.dataframe(pd.read_csv(csv_path), use_container_width=True)

    if json_files:
        st.markdown("#### Metadatos del entorno")
        for json_path in json_files:
            with st.expander(json_path.name):
                st.code(json_path.read_text(encoding="utf-8"), language="json")

    if log_files:
        st.markdown("#### Logs de ejecución")
        for log_path in log_files:
            with st.expander(log_path.name):
                st.code(log_path.read_text(encoding="utf-8", errors="replace"), language="text")


def tab_documentacion(activity_path: Path) -> None:
    readme_path = activity_path / "README.md"
    if readme_path.exists():
        st.markdown(readme_path.read_text(encoding="utf-8"))
    else:
        st.info("README.md no disponible.")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Navegación")
    nav_options = ["🏠  Inicio"] + list(SIDEBAR_LABELS.values())
    selected_nav = st.radio("Ir a", nav_options, label_visibility="collapsed")

    if selected_nav != "🏠  Inicio":
        current_key = next(k for k, v in SIDEBAR_LABELS.items() if v == selected_nav)
        st.divider()
        st.markdown(f"**{current_key}**")
        st.caption(DESCRIPTIONS[current_key])
        st.markdown(f"Estado: {status_for(ACTIVITIES[current_key])}")

    st.divider()
    st.caption("Infraestructura para Ciencia de Datos · UTEM")


# ── Header ────────────────────────────────────────────────────────────────────
st.title("Infraestructura para Ciencia de Datos")
st.caption("Universidad Tecnológica Metropolitana (UTEM) · Dashboard de revisión de actividades evaluadas")
st.divider()

# ── Routing ───────────────────────────────────────────────────────────────────
if selected_nav == "🏠  Inicio":
    page_inicio()
else:
    current_key = next(k for k, v in SIDEBAR_LABELS.items() if v == selected_nav)
    current_root = ACTIVITIES[current_key]

    st.subheader(current_key)
    st.caption(DESCRIPTIONS[current_key])

    t_teoria, t_viz, t_resultados, t_docs = st.tabs([
        "📚 Marco Teórico",
        "📈 Visualizaciones",
        "🧪 Resultados",
        "📄 Documentación completa",
    ])

    with t_teoria:
        tab_teoria(current_key, current_root)

    with t_viz:
        tab_visualizaciones(current_root)

    with t_resultados:
        tab_resultados(current_key, current_root)

    with t_docs:
        tab_documentacion(current_root)
