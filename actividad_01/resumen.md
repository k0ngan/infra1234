# Resumen de la Actividad 01

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
- Tamaño de imagen: `512 bytes`
- Firma detectada: `0x55aa`
- Código de salida de QEMU: `1`
- Smoke test serial: `True`
- Mensaje observado: `Boot OK: Micro S.O. UTEM`

## Complejidad adicional incorporada
Se agregó salida simultánea por VGA y serial, más una validación automática de build y boot para que la actividad sea comprobable sin depender de GUI.
