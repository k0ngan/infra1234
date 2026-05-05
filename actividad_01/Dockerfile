FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends nasm qemu-system-x86 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

CMD ["python", "src/run.py"]
