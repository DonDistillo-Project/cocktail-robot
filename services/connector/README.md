# Connector

## Usage

### Before running the connector

This should be running before starting the connector:
1. The [ESP](https://gitlab.informatik.hu-berlin.de/swh2/esp-code) on `ESP_ADDR` (configured in `src/connector/config.py`).
2. The STT service on `STT_ADDR`
3. The TTS service on `TTS_ADDR`

Additionally, your working directory needs to contain the `resources/` (containing the system prompts and tools for both LLMs).

### Runing the connector

```bash
uv run main.py
```