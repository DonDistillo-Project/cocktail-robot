# TTS (Text-to-Speech) Service

This service synthesizes text to audio using [RealtimeTTS](https://github.com/KoljaB/RealtimeTTS). It can use either a cloud service (Azure) or a local model (Coqui) as a backend.

## Requirements

- For GPU mode (local backend):
    - CUDA-capable GPU
    - NVIDIA driver ≥ 12.9
    - [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

## Usage

### Using Docker (recommended)

It is recommended to use the Docker Compose files in the root of the repository to run this service. See the [main README.md](../../README.md) for more information.

### Manual execution

This service can be run with a cloud backend (CPU) or a local backend (GPU). From this directory (`services/tts`):

**Cloud Backend (CPU):**

1.  Build the Docker image:

    ```bash
    docker build --target cpu -t tts-server .
    ```

2.  Run the Docker container:

    ```bash
    docker run -p 9002:9002 tts-server
    ```

**Local Backend (GPU):**

1.  Build the Docker image:

    ```bash
    docker build --target gpu -t tts-server .
    ```

2.  Run the Docker container:

    ```bash
    docker run --gpus all -p 9002:9002 tts-server
    ```

The service will be available on port `9002`.

## Environment Variables

- `AZURE_SPEECH_KEY`: Your Azure Speech API key (only for cloud backend).
- `AZURE_REGION`: The Azure region for your Speech service (only for cloud backend).

## Testing

A simple test client is included in this directory. You can enter text that the TTS service should synthesize.

Run it with:

```bash
uv run test_client.py
```
