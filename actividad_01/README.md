# Actividad 01: Boot de Micro S.O. en QEMU

## Objetivo
Construir un boot sector de 512 bytes en NASM que arranque en QEMU, escriba un mensaje por VGA y serial, y deje evidencia verificable de la ejecución.

## Marco Teórico

- **Master Boot Record (MBR):** El BIOS/UEFI-legacy carga los primeros 512 bytes del disco en la dirección física `0x7C00`. Los últimos dos bytes deben contener la firma `0x55AA`; cualquier otro valor hace que el hardware rechace el sector de arranque.
- **BIOS Interrupt Services:** En modo real de 16 bits, las interrupciones del BIOS (`INT 10h` para video, puertos UART para serial) proveen una capa de abstracción mínima sobre el hardware, suficiente para verificar el arranque sin dependencias externas.
- **Ensamblador NASM:** NASM genera binarios planos (`-f bin`) sin encabezados ELF ni PE, lo que permite posicionar el código exactamente en el offset que requiere el boot sector y garantizar un artefacto de 512 bytes.
- **Virtualización con QEMU:** QEMU emula el hardware completo de una PC (placa madre, CPU i386, puertos UART) en un proceso de usuario. Elimina la necesidad de hardware físico y garantiza reproducibilidad total entre entornos mediante `isa-debug-exit` para cierre headless.
- **Reproducibilidad en infraestructura:** Contenerizar el entorno de compilación y ejecución asegura que NASM y QEMU tengan las mismas versiones en cualquier máquina, alineándose con el principio de infraestructura como código.

## Estructura
- `src/boot.asm`: boot sector en ensamblador.
- `src/run.py`: compila, valida, ejecuta QEMU headless y actualiza `resumen.md`.
- `results/boot.img`: imagen raw de 512 bytes.
- `results/serial.log`: salida serial capturada desde QEMU.
- `results/boot_report.json`: reporte de validación y arranque.

## Ejecución
Desde la raíz del proyecto:

```bash
docker compose run --rm actividad01
```

Desde esta carpeta de forma autónoma:

```bash
docker build -t actividad01 .
docker run --rm -v ${PWD}:/workspace actividad01
```

## Criterio de éxito
- La imagen generada mide exactamente `512` bytes.
- La firma final corresponde a `0x55AA`.
- QEMU arranca en modo headless y deja el mensaje esperado en `results/serial.log`.
- `resumen.md` queda actualizado con los hallazgos de la última corrida.
