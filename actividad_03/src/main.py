from __future__ import annotations

import json
import math
import os
import platform
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import dask.dataframe as dd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil
from distributed import Client, LocalCluster


ROOT = Path("/workspace")
DATA = ROOT / "data"
RESULTS = ROOT / "results"
SUMMARY = ROOT / "resumen.md"
SEED = 20260505
CPU_LIMIT = min(8, os.cpu_count() or 2)


def ensure_dirs() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (DATA / "partitioned").mkdir(parents=True, exist_ok=True)
    (DATA / "io_chunks").mkdir(parents=True, exist_ok=True)


def write_environment() -> None:
    payload = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_limit": CPU_LIMIT,
        "seed": SEED,
    }
    (RESULTS / "environment.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def timer(callable_):
    start = time.perf_counter()
    result = callable_()
    return result, time.perf_counter() - start


def cpu_numeric_kernel_scalar(value: float) -> float:
    return math.sqrt(value + 1.0) * math.log1p(value + 1.0) + math.sin(value / 7.0)


def cpu_numeric_kernel_array(values: np.ndarray) -> np.ndarray:
    return np.sqrt(values + 1.0) * np.log1p(values + 1.0) + np.sin(values / 7.0)


def process_chunk(chunk: np.ndarray) -> float:
    return float(cpu_numeric_kernel_array(chunk).sum())


def experiment_a() -> pd.DataFrame:
    sizes = [250_000, 500_000, 1_000_000, 2_000_000, 4_000_000]
    workers = min(4, CPU_LIMIT)
    rows: list[dict[str, object]] = []
    for size in sizes:
        values = np.linspace(1.0, 250.0, size, dtype=np.float64)

        def sequential_python():
            total = 0.0
            for value in values.tolist():
                total += cpu_numeric_kernel_scalar(value)
            return total

        def numpy_vectorized():
            return float(cpu_numeric_kernel_array(values).sum())

        def multiprocessing_version():
            chunks = np.array_split(values, workers)
            ctx = get_context("fork")
            with ctx.Pool(processes=workers) as pool:
                return sum(pool.map(process_chunk, chunks))

        _, seq_seconds = timer(sequential_python)
        _, np_seconds = timer(numpy_vectorized)
        _, mp_seconds = timer(multiprocessing_version)
        baseline = seq_seconds
        rows.extend(
            [
                {
                    "size": size,
                    "implementation": "python_sequential",
                    "seconds": seq_seconds,
                    "speedup_vs_sequential": baseline / seq_seconds,
                    "efficiency": 1.0,
                    "workers": 1,
                },
                {
                    "size": size,
                    "implementation": "numpy_vectorized",
                    "seconds": np_seconds,
                    "speedup_vs_sequential": baseline / np_seconds,
                    "efficiency": baseline / np_seconds,
                    "workers": 1,
                },
                {
                    "size": size,
                    "implementation": "multiprocessing",
                    "seconds": mp_seconds,
                    "speedup_vs_sequential": baseline / mp_seconds,
                    "efficiency": (baseline / mp_seconds) / workers,
                    "workers": workers,
                },
            ]
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "experiment_a.csv", index=False)
    return frame


def cpu_task(iterations: int) -> float:
    total = 0.0
    for index in range(iterations):
        total += math.sqrt((index % 1_000) + 1.0) * math.sin(index / 15.0)
    return total


def io_task(path: str) -> int:
    with open(path, "rb") as handle:
        data = handle.read()
    return len(data)


def create_io_inputs() -> dict[str, list[str]]:
    rng = np.random.default_rng(SEED + 100)
    io_dir = DATA / "io_chunks"
    if io_dir.exists():
        shutil.rmtree(io_dir)
    io_dir.mkdir(parents=True, exist_ok=True)

    specs = {"small": 256 * 1024, "medium": 1024 * 1024, "large": 4 * 1024 * 1024}
    inputs: dict[str, list[str]] = {}
    for label, size in specs.items():
        label_dir = io_dir / label
        label_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for index in range(12):
            path = label_dir / f"chunk_{index:02d}.bin"
            path.write_bytes(rng.integers(0, 255, size=size, dtype=np.uint8).tobytes())
            paths.append(str(path))
        inputs[label] = paths
    return inputs


def map_with_executor(executor_cls, func, items, workers: int):
    with executor_cls(max_workers=workers) as executor:
        return list(executor.map(func, items))


def experiment_b() -> pd.DataFrame:
    worker_options = [worker for worker in (2, 4, 8) if worker <= CPU_LIMIT]
    cpu_chunks = {"small": 50_000, "medium": 150_000, "large": 300_000}
    io_inputs = create_io_inputs()
    rows: list[dict[str, object]] = []

    for label, iterations in cpu_chunks.items():
        tasks = [iterations] * 12
        _, serial_seconds = timer(lambda: [cpu_task(item) for item in tasks])
        rows.append(
            {
                "workload": "cpu_bound",
                "chunk_label": label,
                "workers": 1,
                "executor": "serial",
                "seconds": serial_seconds,
                "speedup": 1.0,
                "efficiency": 1.0,
            }
        )
        for workers in worker_options:
            _, thread_seconds = timer(lambda: map_with_executor(ThreadPoolExecutor, cpu_task, tasks, workers))
            _, process_seconds = timer(lambda: map_with_executor(ProcessPoolExecutor, cpu_task, tasks, workers))
            rows.extend(
                [
                    {
                        "workload": "cpu_bound",
                        "chunk_label": label,
                        "workers": workers,
                        "executor": "thread_pool",
                        "seconds": thread_seconds,
                        "speedup": serial_seconds / thread_seconds,
                        "efficiency": (serial_seconds / thread_seconds) / workers,
                    },
                    {
                        "workload": "cpu_bound",
                        "chunk_label": label,
                        "workers": workers,
                        "executor": "process_pool",
                        "seconds": process_seconds,
                        "speedup": serial_seconds / process_seconds,
                        "efficiency": (serial_seconds / process_seconds) / workers,
                    },
                ]
            )

    for label, paths in io_inputs.items():
        _, serial_seconds = timer(lambda: [io_task(path) for path in paths])
        rows.append(
            {
                "workload": "io_bound",
                "chunk_label": label,
                "workers": 1,
                "executor": "serial",
                "seconds": serial_seconds,
                "speedup": 1.0,
                "efficiency": 1.0,
            }
        )
        for workers in worker_options:
            _, thread_seconds = timer(lambda: map_with_executor(ThreadPoolExecutor, io_task, paths, workers))
            _, process_seconds = timer(lambda: map_with_executor(ProcessPoolExecutor, io_task, paths, workers))
            rows.extend(
                [
                    {
                        "workload": "io_bound",
                        "chunk_label": label,
                        "workers": workers,
                        "executor": "thread_pool",
                        "seconds": thread_seconds,
                        "speedup": serial_seconds / thread_seconds,
                        "efficiency": (serial_seconds / thread_seconds) / workers,
                    },
                    {
                        "workload": "io_bound",
                        "chunk_label": label,
                        "workers": workers,
                        "executor": "process_pool",
                        "seconds": process_seconds,
                        "speedup": serial_seconds / process_seconds,
                        "efficiency": (serial_seconds / process_seconds) / workers,
                    },
                ]
            )

    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "experiment_b.csv", index=False)
    return frame


def generate_partition_source(n_rows: int = 600_000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 200)
    frame = pd.DataFrame(
        {
            "record_id": np.arange(n_rows, dtype=np.int64),
            "region": rng.choice(["norte", "centro", "sur", "austral"], size=n_rows),
            "source": rng.choice(["crm", "erp", "iot", "ecommerce"], size=n_rows),
            "segment": rng.choice(["retail", "enterprise", "publico"], size=n_rows),
            "metric_a": rng.normal(100.0, 25.0, size=n_rows).round(4),
            "metric_b": rng.gamma(shape=2.5, scale=12.0, size=n_rows).round(4),
        }
    )
    frame["score"] = (frame["metric_a"] * 0.7 + frame["metric_b"] * 0.3).round(4)
    return frame


def write_partitions(frame: pd.DataFrame) -> None:
    base = DATA / "partitioned"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    for partition_count in (4, 16, 64):
        target = base / f"p{partition_count}"
        target.mkdir(parents=True, exist_ok=True)
        parts = np.array_split(frame, partition_count)
        for index, part in enumerate(parts):
            part.to_csv(target / f"part_{index:03d}.csv", index=False)


def pandas_partition_run(partition_dir: Path) -> float:
    paths = sorted(partition_dir.glob("*.csv"))
    frames = [pd.read_csv(path) for path in paths]
    combined = pd.concat(frames, ignore_index=True)
    filtered = combined[combined["metric_a"] > 95.0]
    grouped = filtered.groupby(["region", "source"], observed=True)["score"].agg(["mean", "sum"])
    return float(grouped["sum"].sum())


def dask_partition_run(pattern: str) -> float:
    cluster = LocalCluster(
        n_workers=min(4, CPU_LIMIT),
        threads_per_worker=1,
        dashboard_address=None,
        processes=True,
    )
    client = Client(cluster)
    try:
        frame = dd.read_csv(pattern)
        filtered = frame[frame["metric_a"] > 95.0]
        grouped = filtered.groupby(["region", "source"])["score"].agg(["mean", "sum"])
        result = grouped.compute()
        return float(result["sum"].sum())
    finally:
        client.close()
        cluster.close()


def experiment_c() -> pd.DataFrame:
    frame = generate_partition_source()
    write_partitions(frame)
    rows: list[dict[str, object]] = []
    for partition_count in (4, 16, 64):
        partition_dir = DATA / "partitioned" / f"p{partition_count}"
        pattern = str(partition_dir / "*.csv")
        pandas_checksum, pandas_seconds = timer(lambda: pandas_partition_run(partition_dir))
        dask_checksum, dask_seconds = timer(lambda: dask_partition_run(pattern))
        rows.extend(
            [
                {
                    "engine": "pandas",
                    "partition_count": partition_count,
                    "seconds": pandas_seconds,
                    "checksum": round(pandas_checksum, 4),
                },
                {
                    "engine": "dask",
                    "partition_count": partition_count,
                    "seconds": dask_seconds,
                    "checksum": round(dask_checksum, 4),
                },
            ]
        )
    result = pd.DataFrame(rows)
    result.to_csv(RESULTS / "experiment_c.csv", index=False)
    return result


def experiment_d(exp_b: pd.DataFrame) -> pd.DataFrame:
    cpu_large = exp_b[(exp_b["workload"] == "cpu_bound") & (exp_b["chunk_label"] == "large")]
    serial_seconds = float(cpu_large[cpu_large["executor"] == "serial"]["seconds"].iloc[0])
    observed = {1: 1.0}
    for workers in [worker for worker in (2, 4, 8) if worker <= CPU_LIMIT]:
        observed_row = cpu_large[(cpu_large["executor"] == "process_pool") & (cpu_large["workers"] == workers)].iloc[0]
        observed[workers] = float(observed_row["speedup"])

    parallel_fractions = []
    for workers, speedup in observed.items():
        if workers == 1:
            continue
        estimate = (1.0 - (1.0 / speedup)) / (1.0 - (1.0 / workers))
        parallel_fractions.append(max(0.0, min(0.99, estimate)))
    parallel_fraction = float(np.mean(parallel_fractions)) if parallel_fractions else 0.85

    rows = []
    for workers in sorted(observed):
        amdahl = 1.0 / ((1.0 - parallel_fraction) + (parallel_fraction / workers))
        gustafson = workers - (1.0 - parallel_fraction) * (workers - 1.0)
        coordination_overhead = max(0.0, serial_seconds / observed[workers] - serial_seconds / amdahl)
        rows.append(
            {
                "workers": workers,
                "observed_speedup": observed[workers],
                "amdahl_speedup": amdahl,
                "gustafson_speedup": gustafson,
                "coordination_overhead_seconds": coordination_overhead,
                "parallel_fraction_estimate": parallel_fraction,
            }
        )
    frame = pd.DataFrame(rows)
    frame.to_csv(RESULTS / "experiment_d.csv", index=False)
    return frame


def plot_experiment_a(frame: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    for implementation, subset in frame.groupby("implementation"):
        ax.plot(subset["size"], subset["seconds"], marker="o", label=implementation)
    ax.set_title("Experimento A: Escalado secuencial, vectorizado y multiprocessing")
    ax.set_xlabel("Tamaño de entrada")
    ax.set_ylabel("Tiempo (s)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_a_scaling.png", dpi=160)
    plt.close(fig)


def plot_experiment_b(frame: pd.DataFrame) -> None:
    cpu = frame[(frame["workload"] == "cpu_bound") & (frame["executor"] != "serial")]
    fig, ax = plt.subplots(figsize=(9, 5))
    for executor, subset in cpu.groupby("executor"):
        pivot = subset[subset["chunk_label"] == "large"]
        ax.plot(pivot["workers"], pivot["speedup"], marker="o", label=executor)
    ax.set_title("Experimento B: Speedup CPU-bound")
    ax.set_xlabel("Workers")
    ax.set_ylabel("Speedup")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_b_cpu_speedup.png", dpi=160)
    plt.close(fig)

    io = frame[(frame["workload"] == "io_bound") & (frame["executor"] != "serial")]
    fig, ax = plt.subplots(figsize=(9, 5))
    for executor, subset in io.groupby("executor"):
        pivot = subset[subset["chunk_label"] == "large"].copy()
        pivot["throughput_ops_s"] = 12 / pivot["seconds"]
        ax.plot(pivot["workers"], pivot["throughput_ops_s"], marker="o", label=executor)
    ax.set_title("Experimento B: Throughput I/O-bound")
    ax.set_xlabel("Workers")
    ax.set_ylabel("Operaciones por segundo")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_b_io_throughput.png", dpi=160)
    plt.close(fig)


def plot_experiment_c(frame: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for engine, subset in frame.groupby("engine"):
        ax.plot(subset["partition_count"], subset["seconds"], marker="o", label=engine)
    ax.set_title("Experimento C: Pandas vs Dask local")
    ax.set_xlabel("Número de particiones")
    ax.set_ylabel("Tiempo (s)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_c_pandas_vs_dask.png", dpi=160)
    plt.close(fig)


def plot_experiment_d(frame: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(frame["workers"], frame["observed_speedup"], marker="o", label="Observado")
    ax.plot(frame["workers"], frame["amdahl_speedup"], marker="o", label="Amdahl")
    ax.plot(frame["workers"], frame["gustafson_speedup"], marker="o", label="Gustafson")
    ax.set_title("Experimento D: Curvas teóricas vs speedup observado")
    ax.set_xlabel("Workers")
    ax.set_ylabel("Speedup")
    ax.legend()
    fig.tight_layout()
    fig.savefig(RESULTS / "exp_d_speedup_curves.png", dpi=160)
    plt.close(fig)


def write_summary(exp_a: pd.DataFrame, exp_b: pd.DataFrame, exp_c: pd.DataFrame, exp_d: pd.DataFrame) -> None:
    best_numpy = exp_a[exp_a["implementation"] == "numpy_vectorized"].sort_values("speedup_vs_sequential", ascending=False).iloc[0]
    best_process_cpu = exp_b[(exp_b["workload"] == "cpu_bound") & (exp_b["executor"] == "process_pool")].sort_values(
        "speedup", ascending=False
    ).iloc[0]
    best_io_thread = exp_b[(exp_b["workload"] == "io_bound") & (exp_b["executor"] == "thread_pool")].sort_values(
        "speedup", ascending=False
    ).iloc[0]
    best_dask = exp_c[exp_c["engine"] == "dask"].sort_values("seconds").iloc[0]
    best_curve = exp_d.sort_values("coordination_overhead_seconds").iloc[-1]

    summary = f"""# Resumen de la Actividad 03

## Objetivo
Comparar paralelismo local y procesamiento distribuido local para determinar cuándo conviene vectorizar, paralelizar o distribuir cargas de trabajo.

## Enfoque aplicado
- Carga numérica intensiva en tres estilos: Python puro, NumPy y `multiprocessing`.
- Workloads CPU-bound e I/O-bound sobre `ThreadPoolExecutor` y `ProcessPoolExecutor`.
- Comparativa Pandas vs Dask local sobre datos repartidos en `4`, `16` y `64` particiones.

## Hallazgos de la última corrida
- Mejor speedup vectorizado: `{best_numpy['speedup_vs_sequential']:.2f}x` con tamaño `{int(best_numpy['size'])}`.
- Mejor configuración CPU-bound con procesos: `{best_process_cpu['workers']}` workers, chunk `{best_process_cpu['chunk_label']}`, speedup `{best_process_cpu['speedup']:.2f}x`.
- Mejor configuración I/O-bound con hilos: `{best_io_thread['workers']}` workers, chunk `{best_io_thread['chunk_label']}`, speedup `{best_io_thread['speedup']:.2f}x`.
- Mejor corrida de Dask: `{int(best_dask['partition_count'])}` particiones en `{best_dask['seconds']:.2f}s`.
- El mayor overhead de coordinación observado aparece cerca de `{int(best_curve['workers'])}` workers.

## Recomendaciones por escenario
- Servidor único: preferir NumPy vectorizado cuando el dataset cabe en memoria y la operación es numérica.
- Múltiples fuentes: usar hilos para I/O-bound y Dask local cuando ya existen particiones o archivos independientes.
- Escenario cloud: escalar hacia un motor distribuido solo si el costo de particionar y coordinar se compensa con más volumen y consultas repetidas.

## Complejidad adicional incorporada
Se superpuso el speedup observado con curvas tipo Amdahl y Gustafson para mostrar explícitamente por qué el crecimiento deja de ser lineal al aumentar workers.
"""
    SUMMARY.write_text(summary, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    write_environment()
    exp_a = experiment_a()
    exp_b = experiment_b()
    exp_c = experiment_c()
    exp_d = experiment_d(exp_b)
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
        "rss_mb": round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 2),
    }
    (RESULTS / "summary_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
