from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Network config
    ESP_ADDR: str = "192.168.125.16"
    ESP_AUDIO_PORT: int = 1234
    ESP_CTRL_PORT: int = 2345

    STT_ADDR: str = "localhost"
    STT_PORT: int = 9001
    STT_SPRT: int = 16000

    TTS_ADDR: str = "localhost"
    TTS_PORT: int = 9002
    TTS_SPRT: int = 22500

    # AudioStream config
    MIC_SAMPLE_RATE: int = 16000
    SPEAKER_SAMPLE_RATE: int = 24000

    # LLM config
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_API_KEY: str = "YOUR_API_KEY"

    # Path config
    # Assumes the project root is two levels up from this file
    # (src/connector/config.py -> src/ -> project root)
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    RESOURCES_DIR: Path = PROJECT_ROOT / "resources" / "llm"

    model_config = SettingsConfigDict(env_file=".env", extra="")


settings = Settings()