# STT (Speech-to-Text) Service

This service transcribes audio from the microphone to text using [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT). It can run on either CPU or GPU.

## Requirements

- For GPU mode:
    - CUDA-capable GPU
    - NVIDIA driver ≥ 12.9
    - [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

## Usage

### Using Docker (recommended)

It is recommended to use the Docker Compose files in the root of the repository to run this service. See the [main README.md](../../README.md) for more information.

### Manual execution

This service can be run in either CPU or GPU mode. From this directory (`services/stt`):

**CPU Mode:**

1.  Build the Docker image:

    ```bash
    docker build --target cpu -t stt-server .
    ```

2.  Run the Docker container:

    ```bash
    docker run -p 9001:9001 stt-server
    ```

**GPU Mode:**

1.  Build the Docker image:

    ```bash
    docker build --target gpu -t stt-server .
    ```

2.  Run the Docker container:

    ```bash
    docker run --gpus all -p 9001:9001 stt-server
    ```

The service will be available on port `9001`.

## Testing

A simple test client is included in this directory. It will record from your microphone and send audio to the STT service for transcription.

Run it with:

```bash
uv run test_client.py
```

## About the pvporcupine shim

RealtimeSTT imports `pvporcupine` at startup for wake-word detection, even if wake words aren’t used. `pvporcupine` ships native binaries that can fail to load on Linux/arm64 (Apple Silicon Docker), which would break the container.

To avoid this, a small `pvporcupine.py` file is placed in the service’s source tree. This acts as a shim — it overrides the real package so imports succeed, but no native code is loaded. The shim’s `create()` function raises an error if wake words are ever enabled.
