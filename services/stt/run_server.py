import logging

from datetime import datetime


import asyncio
from threading import Thread
from RealtimeSTT import AudioToTextRecorder  # type: ignore


PORT = 1234
ADDR = "0.0.0.0"

CHUNK_LEN = 1.0
SAMPLE_RATE = 16000


LOG_LEVEL = logging.INFO


logger = logging.getLogger("main")


logging.basicConfig(
    level=LOG_LEVEL,
    format="%(threadName)s:" + logging.BASIC_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/{datetime.now()}.log"),
    ],
)


class STTServerProtocol(asyncio.Protocol):
    stt: AudioToTextRecorder
    stt_thread: Thread
    transport: asyncio.Transport

    def __init__(self) -> None:
        logger.info("Creating TTS")

        self.stt = AudioToTextRecorder(
            use_microphone=False,
            model="large-v2",
            spinner=False,
            ensure_sentence_ends_with_period=True,
            language="de",
            print_transcription_time=True,
            enable_realtime_transcription=True,
            use_main_model_for_realtime=True,
            silero_deactivity_detection=True,
        )
        self.stt_thread = Thread(target=self.stt_loop)

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        peername = transport.get_extra_info("peername")
        logger.info("Connection from {}".format(peername))

        self.transport = transport  # type: ignore
        self.stt_thread.start()

    def connection_lost(self, exc: Exception | None) -> None:
        logger.warning(f"Connection closed: {exc}")
        self.stt.shutdown()
        self.stt_thread.join(1)
        logger.info("Cleaned up")

    def data_received(self, data: bytes) -> None:
        logger.debug(f"Received {len(data)} audio bytes")
        self.stt.feed_audio(data)  # type: ignore

    def stt_loop(self) -> None:
        logger.info("Starting STT loop")
        while self.stt.is_running:
            self.stt.text(self.write_text)  # type: ignore
        logger.info("Ending STT loop")

    def write_text(self, text: str) -> None:
        logger.debug(f"Sendig {len(text)} text bytes")
        self.transport.write(text.encode())


async def main():
    loop = asyncio.get_event_loop()

    logger.info(f"Opening server socket on ({ADDR}:{PORT})")
    server = await loop.create_server(
        STTServerProtocol,
        ADDR,
        PORT,
        reuse_address=True,
        reuse_port=True,
    )

    async with server:
        logger.info("Serving")
        await server.serve_forever()

    print("EXITING")


if __name__ == "__main__":
    asyncio.run(main())
