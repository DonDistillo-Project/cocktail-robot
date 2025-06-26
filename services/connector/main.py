import asyncio
import logging

from lib.StreamNodes import BroadcastStream, Gain

ESP_HOST = "ESP32"
ESP_ADDR = "192.168.71.16"
ESP_PORT = 1234

STT_ADDR = "localhost"
STT_PORT = 1234
STT_SPRT = 16000

TTS_ADDR = "localhost"
TTS_PORT = 2345
TTS_SPRT = 22500

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
)


async def async_main():
    loop = asyncio.get_event_loop()

    logger.info("Creating ESP connection")
    esp_transport, esp_stream = await loop.create_connection(
        lambda: BroadcastStream("ESP", loop.create_future()), ESP_ADDR, ESP_PORT
    )

    logger.info("Creating RealtimeSTT connection")
    stt_transport, stt_stream = await loop.create_connection(
        lambda: BroadcastStream("STT", loop.create_future()), STT_ADDR, STT_PORT
    )

    logger.info("Creating RealtimeTTS connection")
    tts_transport, tts_stream = await loop.create_connection(
        lambda: BroadcastStream("TTS", loop.create_future()), TTS_ADDR, TTS_PORT
    )

    esp_stream.add_data_callback(stt_stream.write)

    stt_stream.add_data_callback(tts_stream.write)
    stt_stream.add_data_callback(
        lambda data: logger.info(f"Received STT Result: {data.decode()}")
    )

    gain = Gain(0.5, "ESP:SpeakerGain")
    tts_stream.add_data_callback(gain.data_received)

    gain.add_data_callback(esp_stream.write)

    pending = [
        esp_stream.wait_for_close(),
        stt_stream.wait_for_close(),
        tts_stream.wait_for_close(),
        asyncio.ensure_future(asyncio.to_thread(input, "Press ENTER to exit\n")),
    ]

    while len(pending) > 0:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        logger.warning(f"Finished Task(s) {[d.get_name() for d in done]}")

        esp_transport.close()
        stt_transport.close()
        tts_transport.close()


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
