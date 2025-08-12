ARG CPU_BASE=python:3.11-slim
ARG GPU_BASE=nvidia/cuda:12.9.1-cudnn-runtime-ubuntu24.04

# ---------- CPU ----------
FROM ${CPU_BASE} AS cpu

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential portaudio19-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/

WORKDIR /app
ADD . /app

RUN uv sync --locked --no-dev --extra cpu

EXPOSE 9002
CMD ["uv", "run", "run_server.py"]

# ---------- GPU ----------
FROM ${GPU_BASE} AS gpu

# Install Python on the CUDA base
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    build-essential portaudio19-dev ffmpeg \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/

WORKDIR /app
ADD . /app

RUN uv sync --locked --no-dev --extra gpu

EXPOSE 9002
CMD ["uv", "run", "run_server.py"]
