import asyncio
import logging
from time import sleep
from RealtimeTTS import TextToAudioStream, BaseEngine  # type: ignore
from RealtimeTTS.engines.coqui_engine import CoquiEngine

ADDR = "0.0.0.0"
PORT = 2345

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TTSProtocol(asyncio.Protocol):
    transport: asyncio.Transport
    engine: BaseEngine
    tts: TextToAudioStream

    def __init__(self, engine: CoquiEngine) -> None:
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
        logger.info("Made connection; Starting Playback")
        self.tts.play_async(  # type: ignore
            language="de",
            muted=True,
            on_audio_chunk=self.on_audio_chunk,
        )

        sleep(1)

    def connection_lost(self, exc: Exception | None) -> None:
        logger.info(f"Connection lost: {exc}")
        self.tts.stop()

    def data_received(self, data: bytes) -> None:
        logger.debug(f"Received {len(data)} text bytes")
        self.tts.feed(data.decode())
        if not self.tts.is_playing():
            self.tts.play_async(  # type: ignore
                language="de",
                muted=True,
                on_audio_chunk=self.on_audio_chunk,
            )

    def on_audio_chunk(self, data: bytes) -> None:
        logger.debug(f"Writing {len(data)} audio bytes")
        self.transport.write(data)


# type: ignore
async def main():
    loop = asyncio.get_event_loop()

    logger.info("Starting TTS Engine")
    engine = CoquiEngine(
        use_deepspeed=True,
        language="de",
    )
    print(engine.verify_sample_rate(-1))

    logger.info(f"Opening server socket on ({ADDR}:{PORT})")
    server = await loop.create_server(
        lambda: TTSProtocol(engine),
        ADDR,
        PORT,
        reuse_address=True,
        reuse_port=True,
    )

    async with server:
        logger.info("Serving TTS Server")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
