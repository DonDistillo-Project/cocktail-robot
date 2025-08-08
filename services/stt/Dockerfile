# syntax=docker/dockerfile:1

ARG CPU_BASE=python:3.12-slim
ARG GPU_BASE=nvidia/cuda:12.9.1-cudnn-runtime-ubuntu24.04

############################
# ---------- CPU ----------
############################
FROM ${CPU_BASE} AS cpu

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential portaudio19-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# uv (python package manager)
COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/

# Caches live in-image so downloads are baked at build time
ENV TORCH_HOME=/root/.cache/torch \
    HF_HOME=/root/.cache/huggingface \
    HUGGINGFACE_HUB_CACHE=/root/.cache/huggingface \
    PYTHONUNBUFFERED=1

WORKDIR /app
ADD . /app

# Ensure our local pvporcupine.py shim is preferred over site-packages
ENV PYTHONPATH=/app

# Resolve & install project deps for the CPU extra
RUN uv sync --locked --no-dev --extra cpu

# Prefetch model artifacts at build time:
# - Silero VAD (torch.hub)
# - faster-whisper "small" model (CTranslate2 weights via HF cache)
RUN uv run python - <<'PY'
import torch
torch.hub.load('snakers4/silero-vad', 'silero_vad', trust_repo=True)
from faster_whisper import WhisperModel
_ = WhisperModel("small", device="cpu", compute_type="int8")
PY

EXPOSE 9001
CMD ["uv", "run", "run_server.py"]


############################
# ---------- GPU ----------
############################
FROM ${GPU_BASE} AS gpu

# Python + build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    build-essential portaudio19-dev ffmpeg \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

# uv
COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/

# Caches live in-image so downloads are baked at build time
ENV TORCH_HOME=/root/.cache/torch \
    HF_HOME=/root/.cache/huggingface \
    HUGGINGFACE_HUB_CACHE=/root/.cache/huggingface \
    PYTHONUNBUFFERED=1

WORKDIR /app
ADD . /app

# Ensure our local pvporcupine.py shim is preferred over site-packages
ENV PYTHONPATH=/app

# Resolve & install project deps for the GPU extra
RUN uv sync --locked --no-dev --extra gpu

# Prefetch model artifacts at build time.
RUN uv run python - <<'PY'
import torch
torch.hub.load('snakers4/silero-vad', 'silero_vad', trust_repo=True)
from faster_whisper import WhisperModel
_ = WhisperModel("small", device="cuda", compute_type="int8")
PY

EXPOSE 9001
CMD ["uv", "run", "run_server.py"]
