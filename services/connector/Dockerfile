FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Needed to build pyaudio
RUN apt-get update && apt-get install -y \
    build-essential \
    libportaudio2 \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "src/main.py"]