import asyncio
import logging
import os
from time import sleep

from RealtimeTTS import BaseEngine, TextToAudioStream

ADDR = "0.0.0.0"
PORT = 9002

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def get_engine(backend: str) -> BaseEngine:
    if backend == "coqui":
        from RealtimeTTS.engines.coqui_engine import CoquiEngine

        return CoquiEngine(use_deepspeed=True, language="de", device="cuda")
    elif backend == "azure":
        from RealtimeTTS.engines.azure_engine import AzureEngine

        # assumes AZURE_SPEECH_KEY / AZURE_REGION are set in env
        key = os.environ["AZURE_SPEECH_KEY"]
        region = os.environ["AZURE_REGION"]
        return AzureEngine(
            speech_key=key,
            service_region=region,
            voice="de-DE-FlorianMultilingualNeural",
            audio_format="riff-24khz-16bit-mono-pcm",
        )
    else:
        raise ValueError(f"Unknown TTS_BACKEND: {backend!r}")


class TTSProtocol(asyncio.Protocol):
    transport: asyncio.Transport
    engine: BaseEngine
    tts: TextToAudioStream

    def __init__(self, engine: BaseEngine) -> None:
        self.engine = engine
        logger.info("Starting TTS Stream")
        self.tts = TextToAudioStream(
            engine=self.engine,
            language="de",
            muted=True,
        )
        logger.info("TTS Server started")

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore
        logger.info("Connection made; starting playback")
        self._play()
        sleep(1)

    def data_received(self, data: bytes) -> None:
        self.tts.feed(data.decode())
        if not self.tts.is_playing():
            self._play()

    def connection_lost(self, exc: Exception | None) -> None:
        logger.info(f"Connection lost: {exc}")
        self.tts.stop()

    def _play(self) -> None:
        self.tts.play_async(
            language="de", muted=True, on_audio_chunk=self.transport.write
        )


async def main():
    use_cuda = os.getenv("USE_CUDA", "false").lower() in ("1", "true", "yes")
    backend = "coqui" if use_cuda else "azure"

    logger.info(f"Initializing engine (backend={backend})")
    engine = get_engine(backend)
    logger.debug("Engine info: %s", engine.get_stream_info())

    loop = asyncio.get_event_loop()
    server = await loop.create_server(
        lambda: TTSProtocol(engine),
        ADDR,
        PORT,
        reuse_address=True,
        reuse_port=True,
    )

    logger.info(f"Serving on {ADDR}:{PORT}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
