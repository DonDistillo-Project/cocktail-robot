This directory contains the TTS server module, which uses [RealtimeTTS](https://github.com/KoljaB/RealtimeTTS) under the hood. It can use either a cloud service (Azure) or a local model (Coqui) as a backend.

## Running with cloud backend

> [!NOTE]  
> This will use Azure's TTS service as a backend, so the environment variables `AZURE_SPEECH_KEY` and `AZURE_REGION` need to be set.

1. Starting from the root directory of the repo:

```bash
cd services/tts/
```

2. Build:

```bash
docker build -t tts-server --target cpu .
```

3. Run:

```bash
docker run -p 9002:9002 tts-server
```

The container listens on port `9002`.


## Running locally

### Requirements

For GPU mode:

* CUDA-capable GPU
* NVIDIA driver ≥12.9
* NVIDIA Container Toolkit installed

### Usage

1. Starting from the root directory of the repo:

```bash
cd services/tts/
```

2. Build

```bash
docker build -t tts-server --target gpu .
```

3. Run

```bash
docker run --gpus all -p 9002:9002 tts-server
```

The container listens on port `9002`.

## Testing

This directory also contains a simple test client where you can enter text that the TTS service should synthesize.

Run it using:

```bash
uv run test_client.py
```