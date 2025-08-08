# STT Service

This directory contains the STT (speech-to-text) server module, which uses [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) under the hood.
It supports either CPU or GPU execution and runs entirely locally.

## Running in CPU mode

1. From the root of the repository:

```bash
cd services/stt/
```

2. Build:

```bash
docker build \
  --target cpu \
  -t stt-server .
```

3. Run:

```bash
docker run -p 9001:9001 stt-server
```

The container listens on port `9001`.


## Running in GPU mode

### Requirements

* CUDA-capable GPU
* NVIDIA driver ≥ 12.9
* [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) installed

### Usage

1. From the root of the repository:

```bash
cd services/stt/
```

2. Build:

```bash
docker build \
  --target gpu \
  -t stt-server .
```

3. Run:

```bash
docker run --gpus all -p 9001:9001 stt-server
```

The container listens on port `9001`.


## Testing

A simple test client is included in this directory. It will record from your microphone and send audio to the STT service for transcription.

Run it with:

```bash
uv run test_client.py
```


## About the pvporcupine shim

RealtimeSTT imports pvporcupine at startup for wake-word detection, even if wake words aren’t used.
pvporcupine ships native binaries that can fail to load on Linux/arm64 (Apple Silicon Docker), which would break the container.

To avoid this, a small pvporcupine.py file is placed in the service’s source tree. This acts as a shim — it overrides the real package so imports succeed, but no native code is loaded. The shim’s create() function raises an error if wake words are ever enabled.”