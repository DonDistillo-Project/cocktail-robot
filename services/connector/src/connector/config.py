from pathlib import Path

# Network config
ESP_HOST = "ESP32"
ESP_AUDIO_ADDR = "192.168.125.16"
ESP_AUDIO_PORT = 1234

ESP_CTRL_ADDR = ESP_AUDIO_ADDR
ESP_CTRL_PORT = 2345

STT_ADDR = "localhost"
STT_PORT = 1234
STT_SPRT = 16000

TTS_ADDR = "localhost"
TTS_PORT = 2345
TTS_SPRT = 22500

# AudioStream config
MIC_SAMPLE_RATE = 16000
SPEAKER_SAMPLE_RATE = 24000

# LLM config
OPENAI_MODEL = "gpt-4.1-mini"
RESOURCES_DIR = Path.cwd() / "resources" / "llm"
