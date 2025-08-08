FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/

ADD . /app

WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "main.py"]