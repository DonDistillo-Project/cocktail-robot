from pathlib import Path

# Network config
ESP_HOST = "ESP32"
ESP_ADDR = "172.20.10.2"
ESP_PORT = 1234

ESP_CTRL_ADDR = ESP_ADDR
ESP_CTRL_PORT = 2345

STT_ADDR = "localhost"
STT_PORT = 1234
STT_SPRT = 16000

TTS_ADDR = "localhost"
TTS_PORT = 2345
TTS_SPRT = 22500

# LLM config
OPENAI_MODEL = "gpt-4.1-mini"
RESOURCES_DIR = Path.cwd() / "resources" / "llm"
