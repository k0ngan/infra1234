from __future__ import annotations

import json
import os
import platform
import shutil
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
import pyarrow.dataset as ds


ROOT = Path("/workspace")
DATA = ROOT / "data"
RESULTS = ROOT / "results"
SUMMARY = ROOT / "resumen.md"
SEED = 20260505
CSV_PATH = DATA / "veterinary_visits_bigdata.csv"
PARQUET_PATH = DATA / "veterinary_visits_bigdata.parquet"
PARTITIONED_DIR = DATA / "veterinary_visits_partitioned"


def ensure_dirs() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)


def rss_mb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def timer(callable_):
    before = rss_mb()
    start = time.perf_counter()
    result = callable_()
    elapsed = time.perf_counter() - start
    after = rss_mb()
    return result, elapsed, max(before, after)


def write_environment() -> None:
    payload = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "seed": SEED,
        "cpu_count": os.cpu_count(),
    }
    (RESULTS / "environment.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def generate_dataset(n_rows: int = 1_500_000) -> tuple[pd.DataFrame, float]:
    rng = np.random.default_rng(SEED)
    start = np.datetime64("2024-01-01T00:00:00")
    seconds = rng.integers(0, 365 * 24 * 3600, size=n_rows, dtype=np.int64)
    visit_ts = pd.to_datetime(start + seconds.astype("timedelta64[s]"))
    pet_weight_kg = rng.normal(17.5, 11.0, size=n_rows).clip(0.8, 68.0).round(2)
    visit_duration_min = rng.gamma(shape=2.4, scale=16.0, size=n_rows).round(2)
    treatment_cost = rng.normal(74_000.0, 28_000.0, size=n_rows).clip(8_000, 240_000).round(0)
    medicine_units = rng.integers(1, 8, size=n_rows, dtype=np.int16)
    followup_required = rng.choice([0, 1], size=n_rows, p=[0.76, 0.24]).astype(np.int8)
    emergency_flag = rng.choice([0, 1], size=n_rows, p=[0.93, 0.07]).astype(np.int8)

    frame = pd.DataFrame(
        {
            "visit_id": np.arange(n_rows, dtype=np.int64),
            "visit_ts": visit_ts,
            "clinic_branch": rng.choice(
                ["nunoa", "maipu", "vina", "concepcion"],
                size=n_rows,
                p=[0.31, 0.27, 0.19, 0.23],
            ),
            "species": rng.choice(["perro", "gato", "conejo", "ave"], size=n_rows, p=[0.52, 0.34, 0.08, 0.06]),
            "visit_type": rng.choice(["control", "vacunacion", "urgencia", "cirugia", "peluqueria"], size=n_rows),
            "vet_shift": rng.choice(["manana", "tarde", "noche"], size=n_rows, p=[0.41, 0.44, 0.15]),
            "pet_weight_kg": pet_weight_kg,
            "visit_duration_min": visit_duration_min,
            "treatment_cost_clp": treatment_cost,
            "medicine_units": medicine_units,
            "followup_required": followup_required,
            "emergency_flag": emergency_flag,
        }
    )
    frame["visit_month"] = frame["visit_ts"].dt.to_period("M").astype(str)
    frame["cost_per_minute"] = (frame["treatment_cost_clp"] / frame["visit_duration_min"]).round(2)
    frame["care_intensity"] = (frame["medicine_units"] * frame["visit_duration_min"]).round(2)

    start_write = time.perf_counter()
    frame.to_csv(CSV_PATH, index=False)
    write_seconds = time.perf_counter() - start_write
    return frame, write_seconds


def experiment_a(frame: pd.DataFrame, write_seconds: float) -> pd.DataFrame:
    csv_size_mb = CSV_PATH.stat().st_size / (1024 * 1024)
    row = pd.DataFrame(
        [
            {
                "rows": len(frame),
                "columns": len(frame.columns),
                "csv_size_mb": csv_size_mb,
                "write_seconds": write_seconds,
                "rss_mb_after_generation": rss_mb(),
            }
        ]
    )
    row.to_csv(RESULTS / "experiment_a.csv", index=False)
    return row


def experiment_b() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def read_full():
        df = pd.read_csv(CSV_PATH, parse_dates=["visit_ts"])
        return float(df["treatment_cost_clp"].sum())

    checksum, seconds, memory = timer(read_full)
    rows.append(
        {
            "mode": "full_read",
            "chunk_size": 0,
            "seconds": seconds,
            "rss_mb": memory,
            "checksum": round(checksum, 2),
        }
    )

    for chunk_size in (50_000, 100_000, 250_000):

        def read_chunked():
            total = 0.0
            for chunk in pd.read_csv(CSV_PATH, chunksize=chunk_size, parse_dates=["visit_ts"]):
                total += float(chunk["treatment_cost_clp"].sum())
            return total

        checksum, seconds, memory = timer(read_chunked)
        rows.append(
            {
                "mode": "chunked_read",
                "chunk_size": chunk_size,
                "seconds": seconds,
                "rss_mb": memory,
                "checksum": round(checksum, 2),
            }
        )

    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "experiment_b.csv", index=False)
    return frame


def experiment_c() -> tuple[pd.DataFrame, pd.DataFrame]:
    chunk_size = 100_000
    partials: list[pd.DataFrame] = []

    def incremental_pipeline():
        for chunk in pd.read_csv(CSV_PATH, chunksize=chunk_size, parse_dates=["visit_ts"]):
            filtered = chunk[
                (chunk["emergency_flag"] == 0)
                & (chunk["clinic_branch"].isin(["nunoa", "maipu", "concepcion"]))
                & (chunk["visit_duration_min"] <= 180.0)
            ].copy()
            filtered["visit_month"] = filtered["visit_ts"].dt.to_period("M").astype(str)
            grouped = (
                filtered.groupby(["visit_month", "species"], observed=True)
                .agg(
                    visits_sum=("visit_id", "count"),
                    cost_sum=("treatment_cost_clp", "sum"),
                    duration_sum=("visit_duration_min", "sum"),
                )
                .reset_index()
            )
            partials.append(grouped)

        combined = pd.concat(partials, ignore_index=True)
        final = (
            combined.groupby(["visit_month", "species"], observed=True)
            .agg(
                visits_sum=("visits_sum", "sum"),
                cost_sum=("cost_sum", "sum"),
                duration_sum=("duration_sum", "sum"),
            )
            .reset_index()
        )
        final["avg_cost_per_visit"] = (final["cost_sum"] / final["visits_sum"]).round(2)
        final["avg_duration_per_visit"] = (final["duration_sum"] / final["visits_sum"]).round(2)
        return final

    aggregate, seconds, memory = timer(incremental_pipeline)
    aggregate.to_csv(RESULTS / "incremental_aggregate.csv", index=False)
    metrics = pd.DataFrame(
        [
            {
                "chunk_size": chunk_size,
                "seconds": seconds,
                "rss_mb": memory,
                "groups": len(aggregate),
                "cost_checksum": round(float(aggregate["cost_sum"].sum()), 2),
            }
        ]
    )
    metrics.to_csv(RESULTS / "experiment_c.csv", index=False)
    return metrics, aggregate


def build_parquet_artifacts() -> tuple[float, float]:
    if PARTITIONED_DIR.exists():
        shutil.rmtree(PARTITIONED_DIR)

    def build_flat():
        df = pd.read_csv(CSV_PATH, parse_dates=["visit_ts"])
        df.to_parquet(PARQUET_PATH, index=False)

    def build_partitioned():
        df = pd.read_csv(CSV_PATH, parse_dates=["visit_ts"])
        df.to_parquet(PARTITIONED_DIR, index=False, partition_cols=["clinic_branch"])

    _, flat_seconds, _ = timer(build_flat)
    _, partitioned_seconds, _ = timer(build_partitioned)
    return flat_seconds, partitioned_seconds


def dataset_size_mb(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / (1024 * 1024)
    return sum(file.stat().st_size for file in path.rglob("*.parquet")) / (1024 * 1024)


def read_full_csv() -> float:
    df = pd.read_csv(CSV_PATH, parse_dates=["visit_ts"])
    return float(df["treatment_cost_clp"].sum())


def read_full_parquet() -> float:
    df = pd.read_parquet(PARQUET_PATH)
    return float(df["treatment_cost_clp"].sum())


def read_full_partitioned() -> float:
    table = ds.dataset(PARTITIONED_DIR, format="parquet", partitioning="hive").to_table()
    return float(table.column("treatment_cost_clp").to_numpy().sum())


def filtered_query_csv() -> float:
    df = pd.read_csv(CSV_PATH, parse_dates=["visit_ts"])
    subset = df[(df["clinic_branch"] == "nunoa") & (df["species"] == "perro")]
    return float(subset["care_intensity"].sum())


def filtered_query_flat() -> float:
    dataset = ds.dataset(PARQUET_PATH, format="parquet")
    table = dataset.to_table(filter=(ds.field("clinic_branch") == "nunoa") & (ds.field("species") == "perro"))
    return float(table.column("care_intensity").to_numpy().sum())


def filtered_query_partitioned() -> float:
    dataset = ds.dataset(PARTITIONED_DIR, format="parquet", partitioning="hive")
    table = dataset.to_table(filter=(ds.field("clinic_branch") == "nunoa") & (ds.field("species") == "perro"))
    return float(table.column("care_intensity").to_numpy().sum())


def aggregate_csv() -> float:
    df = pd.read_csv(CSV_PATH)
    grouped = df.groupby(["visit_month", "clinic_branch"], observed=True)["treatment_cost_clp"].sum()
    return float(grouped.sum())


def aggregate_flat() -> float:
    df = pd.read_parquet(PARQUET_PATH)
    grouped = df.groupby(["visit_month", "clinic_branch"], observed=True)["treatment_cost_clp"].sum()
    return float(grouped.sum())


def aggregate_partitioned() -> float:
    table = ds.dataset(PARTITIONED_DIR, format="parquet", partitioning="hive").to_table()
    df = table.to_pandas()
    grouped = df.groupby(["visit_month", "clinic_branch"], observed=True)["treatment_cost_clp"].sum()
    return float(grouped.sum())


def experiment_d() -> pd.DataFrame:
    flat_seconds, partitioned_seconds = build_parquet_artifacts()
    rows: list[dict[str, object]] = [
        {
            "format": "parquet_flat_build",
            "query": "build",
            "seconds": flat_seconds,
            "rss_mb": rss_mb(),
            "checksum": 0.0,
            "size_mb": dataset_size_mb(PARQUET_PATH),
        },
        {
            "format": "parquet_partitioned_build",
            "query": "build",
            "seconds": partitioned_seconds,
            "rss_mb": rss_mb(),
            "checksum": 0.0,
            "size_mb": dataset_size_mb(PARTITIONED_DIR),
        },
    ]

    tests = [
        ("csv", "full_read", read_full_csv, dataset_size_mb(CSV_PATH)),
        ("parquet_flat", "full_read", read_full_parquet, dataset_size_mb(PARQUET_PATH)),
        ("parquet_partitioned", "full_read", read_full_partitioned, dataset_size_mb(PARTITIONED_DIR)),
        ("csv", "filtered_query", filtered_query_csv, dataset_size_mb(CSV_PATH)),
        ("parquet_flat", "filtered_query", filtered_query_flat, dataset_size_mb(PARQUET_PATH)),
        ("parquet_partitioned", "filtered_query", filtered_query_partitioned, dataset_size_mb(PARTITIONED_DIR)),
        ("csv", "aggregation", aggregate_csv, dataset_size_mb(CSV_PATH)),
        ("parquet_flat", "aggregation", aggregate_flat, dataset_size_mb(PARQUET_PATH)),
        ("parquet_partitioned", "aggregation", aggregate_partitioned, dataset_size_mb(PARTITIONED_DIR)),
    ]

    for fmt, query, func, size_mb in tests:
        checksum, seconds, memory = timer(func)
        rows.append(
            {
                "format": fmt,
                "query": query,
                "seconds": seconds,
                "rss_mb": memory,
                "checksum": round(checksum, 2),
                "size_mb": size_mb,
            }
        )

    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "experiment_d.csv", index=False)
    return frame


def plot_experiment_a(frame: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(["CSV base"], frame["csv_size_mb"], color="#2A9D8F")
    ax.set_title("Experimento A: Perfil del archivo base")
    ax.set_ylabel("Tamano (MB)")
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_a_storage_profile.png", dpi=160)
    plt.close(fig)


def plot_experiment_b(frame: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = ["full"] + [f"{int(size / 1000)}k" for size in frame["chunk_size"].iloc[1:]]
    ax.bar(labels, frame["seconds"], color=["#264653", "#2A9D8F", "#E9C46A", "#E76F51"])
    ax.set_title("Experimento B: Lectura monolitica vs chunked")
    ax.set_ylabel("Tiempo (s)")
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_b_chunked_reads.png", dpi=160)
    plt.close(fig)


def plot_experiment_c(aggregate: pd.DataFrame) -> None:
    top = aggregate.groupby("species", observed=True)["cost_sum"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(top.index, top.values, color="#3D5A80")
    ax.set_title("Experimento C: Costo incremental por especie")
    ax.set_ylabel("Costo acumulado (CLP)")
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_c_incremental_top_categories.png", dpi=160)
    plt.close(fig)


def plot_experiment_d(frame: pd.DataFrame) -> None:
    query_rows = frame[frame["query"].isin(["full_read", "filtered_query", "aggregation"])]
    fig, ax = plt.subplots(figsize=(10, 5))
    for query, subset in query_rows.groupby("query"):
        ax.plot(subset["format"], subset["seconds"], marker="o", label=query)
    ax.set_title("Experimento D: Tiempos por formato y tipo de consulta")
    ax.set_ylabel("Tiempo (s)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_d_query_formats.png", dpi=160)
    plt.close(fig)

    size_rows = pd.DataFrame(
        [
            {"format": "csv", "size_mb": dataset_size_mb(CSV_PATH)},
            {"format": "parquet_flat", "size_mb": dataset_size_mb(PARQUET_PATH)},
            {"format": "parquet_partitioned", "size_mb": dataset_size_mb(PARTITIONED_DIR)},
        ]
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(size_rows["format"], size_rows["size_mb"], color=["#264653", "#2A9D8F", "#E9C46A"])
    ax.set_title("Experimento D: Tamano por formato")
    ax.set_ylabel("Tamano (MB)")
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_d_storage_sizes.png", dpi=160)
    plt.close(fig)


def write_summary(exp_a: pd.DataFrame, exp_b: pd.DataFrame, exp_c: pd.DataFrame, exp_d: pd.DataFrame) -> None:
    fastest_chunk = exp_b.sort_values("seconds").iloc[0]
    filtered_best = exp_d[exp_d["query"] == "filtered_query"].sort_values("seconds").iloc[0]
    aggregation_best = exp_d[exp_d["query"] == "aggregation"].sort_values("seconds").iloc[0]
    sizes = {
        "csv": dataset_size_mb(CSV_PATH),
        "parquet_flat": dataset_size_mb(PARQUET_PATH),
        "parquet_partitioned": dataset_size_mb(PARTITIONED_DIR),
    }

    summary = f"""# Resumen de la Actividad 04

## Objetivo
Evaluar como el formato, el particionamiento y la lectura incremental cambian el costo de procesar archivos grandes en un escenario Big Data.

## Enfoque aplicado
- Dataset sintetico plausible de `1.500.000` filas sobre atenciones de clinicas veterinarias y mascotas, con variables temporales, categoricas y numericas.
- Lectura monolitica vs por chunks con `50k`, `100k` y `250k`.
- Pipeline incremental split-process-combine con filtrado, casteo, agregacion y metrica derivada.
- Comparativa CSV vs Parquet plano vs Parquet particionado por sucursal veterinaria.

## Hallazgos de la ultima corrida
- Filas generadas: `{int(exp_a.iloc[0]['rows'])}`.
- Tamano del CSV base: `{exp_a.iloc[0]['csv_size_mb']:.2f} MB`.
- Lectura mas rapida del experimento B: `{fastest_chunk['mode']}` con chunk `{int(fastest_chunk['chunk_size']) if fastest_chunk['chunk_size'] else 0}` en `{fastest_chunk['seconds']:.2f}s`.
- Mejor consulta filtrada: `{filtered_best['format']}` en `{filtered_best['seconds']:.2f}s`.
- Mejor agregacion: `{aggregation_best['format']}` en `{aggregation_best['seconds']:.2f}s`.
- Tamanos por formato: `{ {key: round(value, 2) for key, value in sizes.items()} }`.

## Recomendacion arquitectonica
- Batch local: suficiente cuando el CSV cabe en disco y la carga es una corrida esporadica.
- Data lake/lakehouse: preferible cuando predominan consultas repetidas por sucursal o especie, porque el Parquet particionado reduce I/O.
- Formato recomendado para analisis recurrente: Parquet plano para scans completos y Parquet particionado cuando el patron dominante son cortes operacionales por sucursal.

## Complejidad adicional incorporada
Se comparo CSV contra Parquet plano y Parquet particionado, no solo contra la variante particionada, para justificar mejor la decision arquitectonica final.
"""
    SUMMARY.write_text(summary, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    write_environment()
    frame, write_seconds = generate_dataset()
    exp_a = experiment_a(frame, write_seconds)
    del frame
    exp_b = experiment_b()
    exp_c, aggregate = experiment_c()
    exp_d = experiment_d()
    plot_experiment_a(exp_a)
    plot_experiment_b(exp_b)
    plot_experiment_c(aggregate)
    plot_experiment_d(exp_d)
    write_summary(exp_a, exp_b, exp_c, exp_d)
    payload = {
        "rows": int(exp_a.iloc[0]["rows"]),
        "experiment_b_rows": len(exp_b),
        "experiment_d_rows": len(exp_d),
        "rss_mb": round(rss_mb(), 2),
    }
    (RESULTS / "summary_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
