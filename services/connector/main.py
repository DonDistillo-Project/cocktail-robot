import asyncio
import logging

import connector.config as config
from connector.nodes.base import FnNode, Node
from connector.nodes.controlnode import (
    ESPControlCallbackArgs,
    ESPControlNode,
    WeightWatcher,
)
from connector.nodes.gainnode import Gain
from connector.nodes.llmnode import LLMNode
from connector.nodes.streamnode import BroadcastStream, SDStreamNode, TTSStream

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
)


async def async_main():
    loop = asyncio.get_event_loop()

    # Setup nodes & connections
    logger.info("Creating ESP connection")
    on_esp_conn_lost = loop.create_future()
    esp_audio_transport, esp_audio_stream = await loop.create_connection(
        lambda: BroadcastStream[bytes, bytes]("ESP", on_esp_conn_lost),
        config.ESP_AUDIO_ADDR,
        config.ESP_AUDIO_PORT,
    )

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
        lambda: TTSStream("TTS", on_tts_conn_lost, in_converter=str.encode),
        config.TTS_ADDR,
        config.TTS_PORT,
    )

    llm_node = LLMNode("LLM", tts_stream, esp_ctrl_stream)

    # Setup pipeline
    mic_gain = Gain(15.0, "Mic Gain")
    esp_audio_stream.add_outgoing_node(mic_gain)
    mic_gain.add_outgoing_node(stt_stream)

    stt_stream.add_outgoing_node(llm_node)

    llm_node.add_outgoing_node(tts_stream)

    tts_gain = Gain(0.5, "TTS Gain")
    tts_stream.add_outgoing_node(tts_gain)
    tts_gain.add_outgoing_node(esp_audio_stream)

    ### DEBUG ###
    mic_gain.add_outgoing_node(
        SDStreamNode(samplerate=config.MIC_SAMPLE_RATE, name="Mic Playback")
    )

    esp_ctrl_stream.add_outgoing_node(
        FnNode[ESPControlCallbackArgs, None](
            fn=lambda x: print(*x),
            name="Print",
        )
    )

    stt_stream.add_outgoing_node(
        FnNode(
            lambda data: logger.info(f"Received STT Result: {data}"),
            name="Debug FN",
        )
    )

    pending = [
        on_esp_conn_lost,
        on_esp_ctrl_lost,
        on_stt_conn_lost,
        on_tts_conn_lost,
        asyncio.create_task(llm_node.loop()),
        asyncio.ensure_future(asyncio.to_thread(input, "Press ENTER to exit\n")),
    ]

    while len(pending) > 0:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        logger.warning("Finished Task(s)")

        esp_audio_transport.close()
        esp_ctrl_transport.close()
        stt_transport.close()
        tts_transport.close()


if __name__ == "__main__":
    asyncio.run(async_main())
