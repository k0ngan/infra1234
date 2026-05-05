from __future__ import annotations

import json
import math
import os
import platform
import time
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds


ROOT = Path("/workspace")
DATA = ROOT / "data"
RESULTS = ROOT / "results"
SUMMARY = ROOT / "resumen.md"
SEED = 20260505
SIZES_MB = [8, 32, 128, 256, 512]
CSV_PATH = DATA / "benchmark_dataset.csv"
PARQUET_PATH = DATA / "benchmark_dataset.parquet"
OFFSETS_PATH = DATA / "benchmark_offsets.npy"
TMP_DIR = RESULTS / "tmp"


@dataclass
class TimerResult:
    seconds: float
    rss_mb: float


def ensure_dirs() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def process_memory_mb() -> float:
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)


def timed(callable_):
    start = time.perf_counter()
    result = callable_()
    elapsed = time.perf_counter() - start
    return result, TimerResult(seconds=elapsed, rss_mb=process_memory_mb())


def write_environment() -> dict[str, object]:
    env = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "seed": SEED,
    }
    (RESULTS / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    return env


def generate_dataset(n_rows: int = 300_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    start = np.datetime64("2025-01-01T00:00:00")
    seconds = rng.integers(0, 180 * 24 * 3600, size=n_rows, dtype=np.int64)
    frame = pd.DataFrame(
        {
            "row_id": np.arange(n_rows, dtype=np.int64),
            "event_ts": start + seconds.astype("timedelta64[s]"),
            "region": rng.choice(["norte", "centro", "sur", "austral"], size=n_rows, p=[0.22, 0.34, 0.28, 0.16]),
            "channel": rng.choice(["web", "app", "store", "partner"], size=n_rows),
            "segment": rng.choice(["retail", "enterprise", "publico"], size=n_rows, p=[0.6, 0.25, 0.15]),
            "quantity": rng.integers(1, 12, size=n_rows, dtype=np.int16),
            "unit_price": rng.normal(42.0, 11.0, size=n_rows).clip(5, 110).round(2),
            "discount": rng.uniform(0.0, 0.32, size=n_rows).round(4),
            "latency_ms": rng.gamma(shape=2.6, scale=18.0, size=n_rows).round(3),
        }
    )
    frame["revenue"] = (frame["quantity"] * frame["unit_price"] * (1.0 - frame["discount"])).round(2)
    frame["event_ts"] = pd.to_datetime(frame["event_ts"])
    frame.sort_values("row_id", inplace=True)
    frame.to_csv(CSV_PATH, index=False)
    frame.to_parquet(PARQUET_PATH, index=False, row_group_size=4096)
    build_csv_offsets()
    return frame


def build_csv_offsets() -> np.ndarray:
    offsets: list[int] = []
    with CSV_PATH.open("rb") as handle:
        handle.readline()
        while True:
            position = handle.tell()
            line = handle.readline()
            if not line:
                break
            offsets.append(position)
    offset_array = np.array(offsets, dtype=np.int64)
    np.save(OFFSETS_PATH, offset_array)
    return offset_array


def warmup_io() -> None:
    buffer = np.arange(4 * 1024 * 1024, dtype=np.uint8)
    _ = buffer.copy()
    warm_path = TMP_DIR / "warmup.bin"
    with warm_path.open("wb") as handle:
        handle.write(buffer.tobytes())
        handle.flush()
        os.fsync(handle.fileno())
    with warm_path.open("rb") as handle:
        _ = handle.read()
    warm_path.unlink(missing_ok=True)


def experiment_a() -> pd.DataFrame:
    warmup_io()
    rows: list[dict[str, object]] = []
    for size_mb in SIZES_MB:
        rng = np.random.default_rng(SEED + size_mb)
        payload = rng.integers(0, 256, size=size_mb * 1024 * 1024, dtype=np.uint8)

        _, ram_timer = timed(lambda: payload.copy())

        disk_path = TMP_DIR / f"exp_a_{size_mb}mb.bin"
        bytes_payload = payload.tobytes()

        def write_disk():
            with disk_path.open("wb") as handle:
                handle.write(bytes_payload)
                handle.flush()
                os.fsync(handle.fileno())

        def read_disk():
            with disk_path.open("rb") as handle:
                return handle.read()

        _, disk_write_timer = timed(write_disk)
        disk_blob, disk_read_timer = timed(read_disk)
        disk_path.unlink(missing_ok=True)

        rows.append(
            {
                "size_mb": size_mb,
                "ram_copy_seconds": ram_timer.seconds,
                "ram_copy_throughput_mb_s": size_mb / ram_timer.seconds,
                "disk_write_seconds": disk_write_timer.seconds,
                "disk_write_throughput_mb_s": size_mb / disk_write_timer.seconds,
                "disk_read_seconds": disk_read_timer.seconds,
                "disk_read_throughput_mb_s": size_mb / disk_read_timer.seconds,
                "disk_checksum": int(sum(disk_blob[:1024])),
            }
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "experiment_a.csv", index=False)
    return frame


def experiment_b() -> pd.DataFrame:
    offsets = np.load(OFFSETS_PATH)
    sample_rng = np.random.default_rng(SEED + 200)
    sample_ids = np.sort(sample_rng.choice(len(offsets), size=512, replace=False))

    def sequential_csv():
        df = pd.read_csv(CSV_PATH)
        return float(df["revenue"].sum())

    def sequential_parquet():
        df = pd.read_parquet(PARQUET_PATH)
        return float(df["revenue"].sum())

    def random_csv():
        running = 0.0
        with CSV_PATH.open("rb") as handle:
            for row_id in sample_ids:
                handle.seek(int(offsets[row_id]))
                line = handle.readline().decode("utf-8").strip()
                fields = line.split(",")
                running += float(fields[-1])
        return running

    def random_parquet():
        dataset = ds.dataset(PARQUET_PATH, format="parquet")
        table = dataset.to_table(
            columns=["row_id", "revenue"],
            filter=pc.field("row_id").isin(pa.array(sample_ids.tolist(), type=pa.int64())),
        )
        return float(table.column("revenue").to_numpy().sum())

    tests = [
        ("csv", "sequential", sequential_csv),
        ("csv", "random", random_csv),
        ("parquet", "sequential", sequential_parquet),
        ("parquet", "random", random_parquet),
    ]

    rows = []
    for fmt, pattern, func in tests:
        checksum, timer = timed(func)
        rows.append(
            {
                "format": fmt,
                "access_pattern": pattern,
                "seconds": timer.seconds,
                "rows_or_lookups": len(offsets) if pattern == "sequential" else len(sample_ids),
                "checksum": round(checksum, 2),
            }
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "experiment_b.csv", index=False)
    return frame


def apply_transform(batch: pd.DataFrame, mode: str) -> pd.DataFrame:
    transformed = batch.copy()
    transformed["net_revenue"] = transformed["quantity"] * transformed["unit_price"] * (1.0 - transformed["discount"])
    transformed["priority_flag"] = transformed["channel"].eq("app").astype(int)
    if mode == "heavy":
        signal = transformed["net_revenue"].to_numpy(dtype=np.float64)
        latency = transformed["latency_ms"].to_numpy(dtype=np.float64)
        for _ in range(6):
            signal = np.sqrt(signal + 1.0) * np.log1p(latency + 1.0) + np.sin(signal / 30.0)
        transformed["signal_score"] = signal
        transformed["signal_bucket"] = pd.cut(signal, bins=5, labels=["m1", "m2", "m3", "m4", "m5"])
    else:
        transformed["signal_score"] = transformed["net_revenue"] / (transformed["latency_ms"] + 1.0)
        transformed["signal_bucket"] = np.where(transformed["signal_score"] > transformed["signal_score"].median(), "m4", "m2")
    return transformed


def experiment_c() -> pd.DataFrame:
    configs = [
        {"name": "light_small_fast", "transform": "light", "batch_size": 5_000, "io_mode": "fast"},
        {"name": "light_large_fast", "transform": "light", "batch_size": 50_000, "io_mode": "fast"},
        {"name": "heavy_small_fast", "transform": "heavy", "batch_size": 5_000, "io_mode": "fast"},
        {"name": "heavy_large_fast", "transform": "heavy", "batch_size": 50_000, "io_mode": "fast"},
        {"name": "light_large_slow", "transform": "light", "batch_size": 50_000, "io_mode": "slow"},
        {"name": "heavy_small_slow", "transform": "heavy", "batch_size": 5_000, "io_mode": "slow"},
    ]
    rows = []

    for config in configs:
        read_seconds = 0.0
        transform_seconds = 0.0
        write_seconds = 0.0
        total_rows = 0
        summary_chunks: list[pd.DataFrame] = []
        temp_output = TMP_DIR / f"{config['name']}.csv"
        temp_output.unlink(missing_ok=True)

        if config["io_mode"] == "fast":
            source_frame, preload_timer = timed(lambda: pd.read_parquet(PARQUET_PATH).iloc[:150_000].copy())
            read_seconds += preload_timer.seconds
            source_iter = [
                chunk for chunk in source_frame.groupby(np.arange(len(source_frame)) // config["batch_size"])
            ]
            iterator = (chunk for _, chunk in source_iter)
        else:
            iterator = pd.read_csv(CSV_PATH, chunksize=config["batch_size"], parse_dates=["event_ts"])

        for chunk_index, chunk in enumerate(iterator):
            if total_rows >= 150_000:
                break

            start_read = time.perf_counter()
            batch = chunk.copy()
            if config["io_mode"] == "slow":
                time.sleep(0.001)
            read_seconds += time.perf_counter() - start_read

            start_transform = time.perf_counter()
            transformed = apply_transform(batch, config["transform"])
            aggregate = (
                transformed.groupby(["region", "segment"], observed=True)["net_revenue"]
                .agg(["count", "mean"])
                .reset_index()
            )
            summary_chunks.append(aggregate)
            transform_seconds += time.perf_counter() - start_transform

            start_write = time.perf_counter()
            if config["io_mode"] == "slow":
                transformed[["row_id", "net_revenue", "signal_score"]].to_csv(
                    temp_output,
                    mode="a",
                    header=chunk_index == 0,
                    index=False,
                )
                with temp_output.open("ab") as handle:
                    handle.flush()
                    os.fsync(handle.fileno())
            else:
                _ = aggregate["mean"].sum()
            write_seconds += time.perf_counter() - start_write
            total_rows += len(batch)

        temp_output.unlink(missing_ok=True)
        stage_times = {"read": read_seconds, "transform": transform_seconds, "write": write_seconds}
        dominant_stage = max(stage_times, key=stage_times.get)
        rows.append(
            {
                "config": config["name"],
                "transform_mode": config["transform"],
                "batch_size": config["batch_size"],
                "io_mode": config["io_mode"],
                "rows_processed": total_rows,
                "read_seconds": read_seconds,
                "transform_seconds": transform_seconds,
                "write_seconds": write_seconds,
                "total_seconds": read_seconds + transform_seconds + write_seconds,
                "dominant_stage": dominant_stage,
                "aggregate_checksum": round(sum(chunk["mean"].sum() for chunk in summary_chunks), 2),
            }
        )

    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "experiment_c.csv", index=False)
    return frame


def stream_process_one(event: np.ndarray) -> float:
    value = float(event[0])
    latency = float(event[1])
    return math.sqrt(value + 1.0) * math.log1p(latency + 1.0)


def batch_process_many(batch: np.ndarray) -> np.ndarray:
    values = batch[:, 0]
    latencies = batch[:, 1]
    return np.sqrt(values + 1.0) * np.log1p(latencies + 1.0)


def experiment_d() -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 400)
    events = np.column_stack(
        [
            rng.normal(50.0, 8.0, size=60_000).clip(1.0, None),
            rng.gamma(shape=2.2, scale=14.0, size=60_000),
        ]
    )
    batch_sizes = [100, 500, 1_000, 5_000, 10_000]
    interarrival = 0.0004

    _ = batch_process_many(events[:64])
    for sample in events[:64]:
        _ = stream_process_one(sample)

    rows = []
    for mode in ("batch", "streaming"):
        for batch_size in batch_sizes:
            latencies_ms: list[float] = []
            start = time.perf_counter()

            if mode == "batch":
                for offset in range(0, len(events), batch_size):
                    batch = events[offset : offset + batch_size]
                    step_start = time.perf_counter()
                    _ = batch_process_many(batch)
                    compute = time.perf_counter() - step_start
                    arrivals = np.arange(len(batch)) * interarrival
                    completion = len(batch) * interarrival + compute
                    latencies_ms.extend(((completion - arrivals) * 1000.0).tolist())
            else:
                for offset in range(0, len(events), batch_size):
                    batch = events[offset : offset + batch_size]
                    for event in batch:
                        step_start = time.perf_counter()
                        _ = stream_process_one(event)
                        compute = time.perf_counter() - step_start
                        latencies_ms.append(compute * 1000.0)

            elapsed = time.perf_counter() - start
            rows.append(
                {
                    "mode": mode,
                    "batch_size": batch_size,
                    "records": len(events),
                    "throughput_records_s": len(events) / elapsed,
                    "latency_mean_ms": float(np.mean(latencies_ms)),
                    "latency_p95_ms": float(np.percentile(latencies_ms, 95)),
                    "latency_max_ms": float(np.max(latencies_ms)),
                }
            )

    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "experiment_d.csv", index=False)
    return frame


def plot_experiment_a(frame: pd.DataFrame) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(frame["size_mb"], frame["ram_copy_throughput_mb_s"], marker="o", label="RAM copy")
    ax.plot(frame["size_mb"], frame["disk_write_throughput_mb_s"], marker="o", label="Disk write")
    ax.plot(frame["size_mb"], frame["disk_read_throughput_mb_s"], marker="o", label="Disk read")
    ax.set_title("Experimento A: Throughput RAM vs Disco")
    ax.set_xlabel("Tamaño (MB)")
    ax.set_ylabel("Throughput (MB/s)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_a_throughput.png", dpi=160)
    plt.close(fig)


def plot_experiment_b(frame: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    labels = [f"{row['format']}-{row['access_pattern']}" for _, row in frame.iterrows()]
    positions = np.arange(len(labels))
    ax.bar(positions, frame["seconds"], color=["#33658A", "#86BBD8", "#758E4F", "#F6AE2D"])
    ax.set_title("Experimento B: Acceso secuencial y aleatorio")
    ax.set_ylabel("Tiempo (s)")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=20)
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_b_access_patterns.png", dpi=160)
    plt.close(fig)


def plot_experiment_c(frame: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(frame))
    ax.bar(x, frame["read_seconds"], label="Read", color="#3A7CA5")
    ax.bar(x, frame["transform_seconds"], bottom=frame["read_seconds"], label="Transform", color="#2A9D8F")
    ax.bar(
        x,
        frame["write_seconds"],
        bottom=frame["read_seconds"] + frame["transform_seconds"],
        label="Write",
        color="#E76F51",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(frame["config"], rotation=20)
    ax.set_ylabel("Tiempo (s)")
    ax.set_title("Experimento C: Desglose del pipeline ETL")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_c_stage_breakdown.png", dpi=160)
    plt.close(fig)


def plot_experiment_d(frame: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for mode, subset in frame.groupby("mode"):
        ax.plot(subset["batch_size"], subset["latency_p95_ms"], marker="o", label=mode)
    ax.set_title("Experimento D: p95 de latencia")
    ax.set_xlabel("Tamaño de lote")
    ax.set_ylabel("Latencia p95 (ms)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_d_latency.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for mode, subset in frame.groupby("mode"):
        ax.plot(subset["batch_size"], subset["throughput_records_s"], marker="o", label=mode)
    ax.set_title("Experimento D: Throughput batch vs streaming")
    ax.set_xlabel("Tamaño de lote")
    ax.set_ylabel("Registros por segundo")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_d_throughput.png", dpi=160)
    plt.close(fig)


def write_summary(exp_a: pd.DataFrame, exp_b: pd.DataFrame, exp_c: pd.DataFrame, exp_d: pd.DataFrame) -> None:
    best_ram = exp_a.loc[exp_a["ram_copy_throughput_mb_s"].idxmax()]
    best_batch = exp_d[exp_d["mode"] == "batch"].sort_values("throughput_records_s", ascending=False).iloc[0]
    lowest_latency = exp_d.sort_values("latency_p95_ms").iloc[0]
    bottlenecks = exp_c["dominant_stage"].value_counts().to_dict()

    summary = f"""# Resumen de la Actividad 02

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
- Mejor throughput de RAM: `{best_ram['ram_copy_throughput_mb_s']:.2f} MB/s` con `{int(best_ram['size_mb'])} MB`.
- Acceso más rápido en el experimento B: `{exp_b.sort_values('seconds').iloc[0]['format']}-{exp_b.sort_values('seconds').iloc[0]['access_pattern']}`.
- Configuración batch más rápida: `{best_batch['batch_size']}` registros por lote con `{best_batch['throughput_records_s']:.2f} registros/s`.
- Menor latencia `p95`: modo `{lowest_latency['mode']}` con lote `{int(lowest_latency['batch_size'])}` y `{lowest_latency['latency_p95_ms']:.4f} ms`.
- Cuello de botella dominante del ETL: `{bottlenecks}`.

## Complejidad adicional incorporada
Se agregó warmup controlado y reporte de latencia `p95`, lo que permite comparar no solo promedio sino también cola de latencias en el escenario batch vs streaming.
"""
    SUMMARY.write_text(summary, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    write_environment()
    generate_dataset()
    exp_a = experiment_a()
    exp_b = experiment_b()
    exp_c = experiment_c()
    exp_d = experiment_d()
    plot_experiment_a(exp_a)
    plot_experiment_b(exp_b)
    plot_experiment_c(exp_c)
    plot_experiment_d(exp_d)
    write_summary(exp_a, exp_b, exp_c, exp_d)
    payload = {
        "experiment_a_rows": len(exp_a),
        "experiment_b_rows": len(exp_b),
        "experiment_c_rows": len(exp_c),
        "experiment_d_rows": len(exp_d),
    }
    (RESULTS / "summary_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
