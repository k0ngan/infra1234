from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path("/workspace")
SRC = ROOT / "src"
RESULTS = ROOT / "results"
BOOT_ASM = SRC / "boot.asm"
BOOT_IMG = RESULTS / "boot.img"
SERIAL_LOG = RESULTS / "serial.log"
REPORT = RESULTS / "boot_report.json"
SUMMARY = ROOT / "resumen.md"
EXPECTED = "Boot OK: Micro S.O. UTEM"


def run_cmd(cmd: list[str], *, allow_exit_codes: set[int] | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if allow_exit_codes is None:
        allow_exit_codes = {0}
    if completed.returncode not in allow_exit_codes:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {' '.join(cmd)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


def build_boot_image() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    run_cmd(["nasm", "-f", "bin", str(BOOT_ASM), "-o", str(BOOT_IMG)])


def validate_boot_image() -> dict[str, object]:
    image = BOOT_IMG.read_bytes()
    size = len(image)
    signature = image[-2:].hex()
    if size != 512:
        raise RuntimeError(f"Boot image size must be 512 bytes, got {size}")
    if image[-2:] != b"\x55\xaa":
        raise RuntimeError(f"Invalid boot signature: {signature}")
    return {"size_bytes": size, "signature_hex": signature}


def run_qemu() -> dict[str, object]:
    if SERIAL_LOG.exists():
        SERIAL_LOG.unlink()

    cmd = [
        "qemu-system-i386",
        "-drive",
        f"format=raw,file={BOOT_IMG}",
        "-display",
        "none",
        "-serial",
        f"file:{SERIAL_LOG}",
        "-monitor",
        "none",
        "-no-reboot",
        "-device",
        "isa-debug-exit,iobase=0xf4,iosize=0x04",
    ]
    completed = run_cmd(cmd, allow_exit_codes={0, 1})
    serial_text = SERIAL_LOG.read_text(encoding="utf-8", errors="replace").strip()
    smoke_ok = EXPECTED in serial_text
    if not smoke_ok:
        raise RuntimeError(f"Expected serial text not found. Log contents: {serial_text!r}")
    return {
        "qemu_exit_code": completed.returncode,
        "serial_log": serial_text,
        "smoke_test_ok": smoke_ok,
    }


def write_summary(report: dict[str, object]) -> None:
    summary = f"""# Resumen de la Actividad 01

## Objetivo
Construir un boot sector de 512 bytes que arranque en QEMU y demuestre el flujo completo de ensamblado, validación y arranque reproducible.

## Enfoque aplicado
- Boot sector en NASM compilado como binario plano.
- Salida dual: BIOS teletype para VGA y UART COM1 para verificación headless.
- Ejecución automatizada en QEMU con `isa-debug-exit` para cerrar la VM sin interfaz gráfica.

## Decisiones técnicas
- La verificación principal usa la salida serial porque es determinista dentro del contenedor.
- La validación comprueba tamaño exacto de `512` bytes y firma `0x55AA`.
- La evidencia reproducible queda en `results/boot.img`, `results/serial.log` y `results/boot_report.json`.

## Resultados de la última corrida
- Tamaño de imagen: `{report['size_bytes']} bytes`
- Firma detectada: `0x{report['signature_hex']}`
- Código de salida de QEMU: `{report['qemu_exit_code']}`
- Smoke test serial: `{report['smoke_test_ok']}`
- Mensaje observado: `{report['serial_log']}`

## Complejidad adicional incorporada
Se agregó salida simultánea por VGA y serial, más una validación automática de build y boot para que la actividad sea comprobable sin depender de GUI.
"""
    SUMMARY.write_text(summary, encoding="utf-8")


def main() -> None:
    build_boot_image()
    report: dict[str, object] = {}
    report.update(validate_boot_image())
    report.update(run_qemu())
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_summary(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
