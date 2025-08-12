import asyncio
import logging
import os
from datetime import datetime
from threading import Thread
from typing import Optional

import numpy as np

# DEBUGGING
import soundfile as sf
from RealtimeSTT import AudioToTextRecorder

ADDR = "0.0.0.0"
PORT = 9001

CHUNK_LEN = 1.0
SAMPLE_RATE = 16000
DTYPE = "int16"

LOG_LEVEL = logging.INFO
DEBUG_SAVE_WAV = False

if not os.path.exists("logs/"):
    os.makedirs("logs/")


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(threadName)s:" + logging.BASIC_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/{datetime.now()}.log"),
    ],
)


def env_use_cuda() -> bool:
    return os.getenv("USE_CUDA", "false").lower() in ("1", "true", "yes")


class STTServerProtocol(asyncio.Protocol):
    stt: AudioToTextRecorder
    stt_thread: Thread
    transport: asyncio.Transport

    # DEBUGGING
    audio_buffer: bytearray
    connection_time: datetime

    def __init__(self, model: str, device: str) -> None:
        logger.info("Creating STT (model=%s, device=%s)", model, device)

        self.stt = AudioToTextRecorder(
            use_microphone=False,
            model=model,
            device=device,
            spinner=False,
            ensure_sentence_ends_with_period=True,
            language="de",
            print_transcription_time=True,
            enable_realtime_transcription=True,
            use_main_model_for_realtime=True,
            silero_sensitivity=0.9,
            silero_deactivity_detection=False,
            no_log_file=True,
        )
        self.stt_thread = Thread(target=self.stt_loop, daemon=True)

        if DEBUG_SAVE_WAV:
            self.audio_buffer = bytearray()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        peername = transport.get_extra_info("peername")
        logger.info("Connection from %s", peername)

        self.transport = transport  # type: ignore
        self.stt_thread.start()

        if DEBUG_SAVE_WAV:
            self.connection_time = datetime.now()

    def connection_lost(self, exc: Optional[Exception]) -> None:
        logger.warning("Connection closed: %s", exc)
        self.stt.shutdown()
        self.stt_thread.join(1)
        logger.info("Cleaned up")

        if DEBUG_SAVE_WAV and hasattr(self, "audio_buffer") and self.audio_buffer:
            filename = f"logs/received_audio_{self.connection_time.strftime('%Y-%m-%d_%H-%M-%S')}.wav"
            logger.info(
                "Writing %d bytes of audio to %s", len(self.audio_buffer), filename
            )
            try:
                audio_array = np.frombuffer(self.audio_buffer, dtype=DTYPE)
                sf.write(filename, audio_array, SAMPLE_RATE)
                logger.info("Successfully saved debug audio to %s", filename)
            except Exception as e:
                logger.error("Could not save debug audio file: %s", e)

    def data_received(self, data: bytes) -> None:
        logger.debug("Received %d audio bytes", len(data))
        self.stt.feed_audio(data)  # type: ignore
        if DEBUG_SAVE_WAV:
            self.audio_buffer.extend(data)

    def stt_loop(self) -> None:
        logger.info("Starting STT loop")
        while self.stt.is_running:
            self.stt.text(self.write_text)  # type: ignore
        logger.info("Ending STT loop")

    def write_text(self, text: str) -> None:
        logger.debug("Sending %d text bytes", len(text))
        logger.info("Sending transcription result: %s", text)
        self.transport.write(text.encode())


async def main():
    loop = asyncio.get_event_loop()

    use_cuda = env_use_cuda()
    model = "large-v2" if use_cuda else "small"
    device = "cuda" if use_cuda else "cpu"

    logger.info("Initializing STT (model=%s, device=%s)", model, device)
    logger.info("Opening server socket on (%s:%d)", ADDR, PORT)

    server = await loop.create_server(
        lambda: STTServerProtocol(model, device),
        ADDR,
        PORT,
        reuse_address=True,
        reuse_port=True,
    )

    async with server:
        logger.info("Serving")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
