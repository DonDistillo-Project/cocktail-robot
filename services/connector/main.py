import asyncio
import logging

import connector.config as config
from connector.nodes.base import FnNode
from connector.nodes.controlnode import (
    ESPControlCallbackArgs,
    ESPControlNode,
    WeightWatcher,
)
from connector.nodes.gainnode import Gain
from connector.nodes.streamnode import BroadcastStream

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
)


async def async_main():
    loop = asyncio.get_event_loop()

    logger.info("Creating ESP connection")
    on_esp_conn_lost = loop.create_future()
    esp_audio_transport, esp_audio_stream = await loop.create_connection(
        lambda: BroadcastStream[bytes, bytes]("ESP", on_esp_conn_lost),
        config.ESP_ADDR,
        config.ESP_PORT,
    )

    esp_audio_stream.add_outgoing_node(esp_audio_stream)

    on_esp_ctrl_lost = loop.create_future()
    esp_ctrl_transport, esp_ctrl_stream = await loop.create_connection(
        lambda: ESPControlNode(
            "esp_control", on_esp_ctrl_lost, WeightWatcher("ESPWW", 5.0)
        ),
        config.ESP_CTRL_ADDR,
        config.ESP_CTRL_PORT,
    )

    logger.info("Creating RealtimeSTT connection")
    on_stt_conn_lost = loop.create_future()
    stt_transport, stt_stream = await loop.create_connection(
        lambda: BroadcastStream[bytes, str](
            "STT", on_stt_conn_lost, out_converter=bytes.decode
        ),
        config.STT_ADDR,
        config.STT_PORT,
    )

    logger.info("Creating RealtimeTTS connection")
    on_tts_conn_lost = loop.create_future()
    tts_transport, tts_stream = await loop.create_connection(
        lambda: BroadcastStream[str, bytes](
            "TTS", on_tts_conn_lost, in_converter=str.encode
        ),
        config.TTS_ADDR,
        config.TTS_PORT,
    )

    # llm_node = LLMNode("LLM", tts_stream, esp_ctrl_stream)
    # esp_stream.add_outgoing_node(sounddebug)

    mic_gain = Gain(3.0, "Mic Gain")
    esp_audio_stream.add_outgoing_node(mic_gain)
    mic_gain.add_outgoing_node(stt_stream)

    stt_stream.add_outgoing_node(tts_stream)
    # stt_stream.add_outgoing_node(llm_node)
    # llm_node.add_outgoing_node(tts_stream)

    tts_gain = Gain(0.5, "TTS Gain")
    tts_stream.add_outgoing_node(tts_gain)
    tts_gain.add_outgoing_node(esp_audio_stream)

    ### DEBUG ###
    # tts_stream.handle_input("Hallo, das hier ist ein Test für den TTS / Lautsprecher.")
    stt_stream.add_outgoing_node(
        FnNode(
            lambda data: logger.info(f"Received STT Result: {data}"),
            name="Debug FN",
        )
    )

    x = FnNode[ESPControlCallbackArgs, None](fn=lambda x: print(*x), name="Print")
    esp_ctrl_stream.add_outgoing_node(x)

    # await asyncio.sleep(10)
    # esp_ctrl_stream.startRecipe("Test-Rezept\n Zeile 2")
    # await asyncio.sleep(1)
    # esp_ctrl_stream.doIngredientStep(3.0, "Test instruction")

    pending = [
        on_esp_conn_lost,
        on_stt_conn_lost,
        on_tts_conn_lost,
        # asyncio.ensure_future(llm_node.loop()),
        asyncio.ensure_future(asyncio.to_thread(input, "Press ENTER to exit\n")),
    ]

    while len(pending) > 0:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        logger.warning(f"Finished Task(s) {[d.get_name() for d in done]}")

        esp_audio_transport.close()
        stt_transport.close()
        tts_transport.close()


if __name__ == "__main__":
    asyncio.run(async_main())
