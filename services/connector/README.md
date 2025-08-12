# Connector Service

This service is the central hub of the cocktail robot. It connects to the ESP32, the STT service, and the TTS service to manage the cocktail mixing process.

## Requirements

- The `stt` and `tts` services must be running.
- The ESP32 must be running and connected to the network.

## Usage

### Using Docker (recommended)

It is recommended to use the Docker Compose files in the root of the repository to run this service. See the [main README.md](../../README.md) for more information.

### Manual execution

    ```bash
    uv run main.py
    ```

## Environment Variables

- `ESP_ADDR`: The IP address of the ESP32.
- `STT_ADDR`: The address of the STT service.
- `TTS_ADDR`: The address of the TTS service.
- `OPENAI_API_KEY`: Your OpenAI API key.
